#!/usr/bin/env python3
"""
Axanet Client Manager (CLI)
- Crea, lee, actualiza, elimina y lista clientes.
- Guarda cada cliente en data/clients/<hash>.json
- Usa un índice hash (index.json) para mapear nombre -> archivo
- Opcional: notifica a GitHub Actions vía repository_dispatch si existen
  variables de entorno GITHUB_TOKEN y GITHUB_REPOSITORY.
"""
import argparse
import json
import os
import re
import sys
import hashlib
from datetime import datetime
from urllib import request
from urllib.error import URLError, HTTPError

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clients")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "index.json")

def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def _hash_name(name: str) -> str:
    return hashlib.sha256(name.strip().lower().encode("utf-8")).hexdigest()[:16]

def _load_index() -> dict:
    if not os.path.exists(INDEX_PATH):
        return {}
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save_index(idx: dict) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)

def _client_path(hash_id: str) -> str:
    return os.path.join(DATA_DIR, f"{hash_id}.json")

def _load_client(hash_id: str) -> dict | None:
    path = _client_path(hash_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_client(hash_id: str, data: dict) -> None:
    path = _client_path(hash_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _notify_github(event_type: str, client_name: str, payload: dict | None = None) -> None:
    """
    Envía un repository_dispatch para activar GitHub Actions (opcional).
    Requiere:
      - GITHUB_TOKEN: un token (PAT) con permisos "repo" o el GITHUB_TOKEN de Actions
      - GITHUB_REPOSITORY: owner/repo
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not token or not repo:
        # Notificación opcional: omitimos silenciosamente si faltan variables
        return
    url = f"https://api.github.com/repos/{repo}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "axanet-client-manager-cli"
    }
    body = {
        "event_type": event_type,
        "client_payload": {
            "client_name": client_name,
            **(payload or {})
        }
    }
    data = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=10) as resp:
            # 204 expected
            _ = resp.read()
    except HTTPError as e:
        print(f"[WARN] repository_dispatch HTTPError {e.code}: {e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
    except URLError as e:
        print(f"[WARN] repository_dispatch URLError: {e}", file=sys.stderr)

def create_client(name: str, service: str, contact: str | None) -> dict:
    idx = _load_index()
    key = name.strip().lower()
    if key in idx:
        raise SystemExit(f"El cliente '{name}' ya existe. Usa 'update' para agregar servicio.")
    hid = _hash_name(name)
    now = datetime.utcnow().isoformat() + "Z"
    client = {
        "name": name,
        "slug": _slugify(name),
        "hash_id": hid,
        "contact": contact or "",
        "services": [
            {"date": now, "description": service}
        ],
        "created_at": now,
        "updated_at": now
    }
    _save_client(hid, client)
    idx[key] = f"{hid}.json"
    _save_index(idx)
    _notify_github("client.created", name, {"service": service})
    return client

def update_client(name: str, service: str | None = None, contact: str | None = None) -> dict:
    idx = _load_index()
    key = name.strip().lower()
    if key not in idx:
        raise SystemExit(f"No existe el cliente '{name}'. Usa 'create'.")
    hid = idx[key].replace(".json", "")
    client = _load_client(hid)
    if client is None:
        raise SystemExit("Índice corrupto. Archivo de cliente no encontrado.")
    changed = False
    if contact is not None:
        client["contact"] = contact
        changed = True
    if service:
        now = datetime.utcnow().isoformat() + "Z"
        client["services"].append({"date": now, "description": service})
        changed = True
    if not changed:
        raise SystemExit("No se proporcionaron cambios.")
    client["updated_at"] = datetime.utcnow().isoformat() + "Z"
    _save_client(hid, client)
    _notify_github("client.updated", name, {"service": service or ""})
    return client

def read_client(name: str) -> dict:
    idx = _load_index()
    key = name.strip().lower()
    if key not in idx:
        raise SystemExit(f"No existe el cliente '{name}'.")
    hid = idx[key].replace(".json", "")
    client = _load_client(hid)
    if client is None:
        raise SystemExit("Índice corrupto. Archivo de cliente no encontrado.")
    _notify_github("client.queried", name, {})
    return client

def delete_client(name: str) -> None:
    idx = _load_index()
    key = name.strip().lower()
    if key not in idx:
        raise SystemExit(f"No existe el cliente '{name}'.")
    hid = idx[key].replace(".json", "")
    path = _client_path(hid)
    if os.path.exists(path):
        os.remove(path)
    del idx[key]
    _save_index(idx)

def list_clients() -> list[dict]:
    idx = _load_index()
    out = []
    for key, fname in sorted(idx.items()):
        hid = fname.replace(".json", "")
        client = _load_client(hid)
        if client:
            out.append(client)
    return out

def main():
    parser = argparse.ArgumentParser(description="Gestor de clientes Axanet (CLI)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Crear un nuevo cliente")
    p_create.add_argument("--name", required=True, help="Nombre del cliente")
    p_create.add_argument("--service", required=True, help="Descripción del servicio solicitado")
    p_create.add_argument("--contact", required=False, help="Información de contacto (tel/correo)")

    p_update = sub.add_parser("update", help="Actualizar un cliente existente")
    p_update.add_argument("--name", required=True)
    p_update.add_argument("--service", required=False, help="Agregar nueva solicitud/servicio")
    p_update.add_argument("--contact", required=False, help="Actualizar contacto")

    p_read = sub.add_parser("read", help="Consultar un cliente")
    p_read.add_argument("--name", required=True)

    p_delete = sub.add_parser("delete", help="Borrar un cliente")
    p_delete.add_argument("--name", required=True)

    sub.add_parser("list", help="Listar todos los clientes")

    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    if args.cmd == "create":
        c = create_client(args.name, args.service, args.contact)
        print(json.dumps(c, indent=2, ensure_ascii=False))
    elif args.cmd == "update":
        c = update_client(args.name, args.service, args.contact)
        print(json.dumps(c, indent=2, ensure_ascii=False))
    elif args.cmd == "read":
        c = read_client(args.name)
        print(json.dumps(c, indent=2, ensure_ascii=False))
    elif args.cmd == "delete":
        delete_client(args.name)
        print(f"Cliente '{args.name}' eliminado.")
    elif args.cmd == "list":
        lst = list_clients()
        print(json.dumps(lst, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
