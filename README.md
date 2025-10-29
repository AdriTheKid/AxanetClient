# Axanet – Gestor de Clientes  por LAFY AL07113680

Aplicación de línea de comandos para gestionar archivos de clientes, con integración opcional a **GitHub Actions** mediante `repository_dispatch`.

## Características

- Crear, leer, actualizar, borrar y listar clientes.
- Cada cliente se guarda como JSON en `data/clients/<hash>.json`.
- Índice `data/index.json` mapea `nombre -> archivo` (tablas hash / diccionario).
- **Integración opcional** con GitHub Actions: al crear/actualizar/consultar, la app puede emitir eventos `repository_dispatch` (`client.created`, `client.updated`, `client.queried`) que activan flujos de notificación.
