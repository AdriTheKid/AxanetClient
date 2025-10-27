# Axanet – Gestor de Clientes (Python + GitHub Actions) por LAFY AL07113680

Aplicación de línea de comandos para gestionar archivos de clientes, con integración opcional a **GitHub Actions** mediante `repository_dispatch`.

## Características

- Crear, leer, actualizar, borrar y listar clientes.
- Cada cliente se guarda como JSON en `data/clients/<hash>.json`.
- Índice `data/index.json` mapea `nombre -> archivo` (tablas hash / diccionario).
- **Integración opcional** con GitHub Actions: al crear/actualizar/consultar, la app puede emitir eventos `repository_dispatch` (`client.created`, `client.updated`, `client.queried`) que activan flujos de notificación.

## Requisitos

- Python 3.10+
- (Opcional) Variables de entorno para GitHub:
  - `GITHUB_TOKEN` (PAT con permisos `repo` o el token automático de Actions)
  - `GITHUB_REPOSITORY` con el formato `owner/repo`

## Uso

```bash
# Activar entorno (opcional) e instalar nada: solo stdlib
python app/main.py create --name "Acme S.A." --service "Instalación de red" --contact "acme@example.com"
python app/main.py read --name "Acme S.A."
python app/main.py update --name "Acme S.A." --service "Mantenimiento trimestral"
python app/main.py update --name "Acme S.A." --contact "soporte@acme.com"
python app/main.py list
python app/main.py delete --name "Acme S.A."
```

> Si `GITHUB_TOKEN` y `GITHUB_REPOSITORY` están definidos, cada acción emitirá un `repository_dispatch` para activar los flujos definidos en `.github/workflows/*`.

## Colaboración simulada

Agrega dos colaboradores ficticios (p. ej. `@alice-dev` y `@bob-ops`) en tus flujos para simular notificaciones. Si el repositorio es privado y no deseas invitarlos, los flujos **solo** los mencionarán en el resumen del job.

## GitHub Actions

Se incluyen 3 flujos que escuchan `repository_dispatch`:
- `client.created` → **Creación de un nuevo cliente**
- `client.updated` → **Actualización de cliente**
- `client.queried` → **Consulta de cliente**

Cada flujo escribe un mensaje en el Job Summary y (opcional) abre/comenta un Issue si configuras `NOTIFY_ISSUE_NUMBER` en *Repository → Settings → Variables*.

## Estructura

```
.
├── app/
│   └── main.py
├── data/
│   ├── clients/
│   └── index.json
├── .github/
│   └── workflows/
│       ├── notify-created.yml
│       ├── notify-updated.yml
│       └── notify-queried.yml
└── docs/
    └── Axanet_Reporte.docx
```

## Configurar repo y secret (opcional)

1. Crea un repositorio en GitHub y sube este proyecto.
2. En **Settings → Secrets and variables → Actions → Secrets** agrega un secreto llamado `GITHUB_TOKEN` solo si usarás un PAT (en Actions existe automáticamente un token como `secrets.GITHUB_TOKEN`).
3. En **Settings → Variables → Actions → Variables**, crea `NOTIFY_ISSUE_NUMBER` con el número de un Issue para centralizar notificaciones (opcional).

