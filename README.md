# Mi Cole — ERP Educativo

Monolito FastAPI + Angular (mismo puerto) + PostgreSQL.

## Requisitos

- Docker y Docker Compose
- PostgreSQL en tu máquina (recomendado) o perfil `local-db`
- Python 3.12+ (desarrollo local sin Docker, opcional)

## Configuración

```bash
cd backend
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/macOS
```

Edita `backend/.env` con tu Postgres local (`DATABASE_*`, JWT, superadmin).

## Inicio rápido (Docker — patrón monolito)

Postgres en **tu PC** + app en Docker:

```bash
# 1) Esquema y seed SQL (manual — recomendado)
cd ../../mi-cole-docs/sql
pip install -r requirements.txt
python run_schema.py --bootstrap

# 2) Usuarios demo (bcrypt)
cd ../../mi-cole-project/backend
pip install -r requirements.txt
python -m app.cli seed-superadmin
python -m app.cli seed-demo

# 3) App en Docker
cd ..
docker compose up --build
```

- App + SPA stub: http://localhost:8000  
- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

Si el puerto 8000 está ocupado: `$env:APP_PORT="8001"; docker compose up --build` (Windows) o `APP_PORT=8001 docker compose up --build`.

Dentro del contenedor, `localhost` no es tu máquina: Compose fuerza `DATABASE_HOST=host.docker.internal` para llegar al Postgres del host.

### Usuarios demo

Tabla completa (superadmin, owner, staff, padres, estudiantes): [`../mi-cole-docs/USUARIOS-DEMO.md`](../mi-cole-docs/USUARIOS-DEMO.md)

| Rol | Email | Password |
|-----|-------|----------|
| Superadmin | `superadmin@micole.dev` | `ChangeMe123!` |
| Owner | `owner@colegio-demo.dev` | `Demo123!` |
| Operador staff | `operator@colegio-demo.dev` | `Demo123!` |

### Comandos útiles (contenedor en marcha)

```bash
docker compose exec app python -m app.cli apply-sql
docker compose exec app python -m app.cli seed-superadmin
```

### Postgres embebido (sin Postgres local)

```bash
docker compose --profile local-db up --build
```

En `docker-compose.yml`, cambia `DATABASE_HOST: host.docker.internal` por `DATABASE_HOST: db` y en `backend/.env` usa `DATABASE_USER=micole`, `DATABASE_PASSWORD=micole`, `DATABASE_NAME=micole`.

## Desarrollo local (sin Docker)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt

# CREATE DATABASE mi_cole_db;  (si no existe)
python -m app.cli apply-sql
python -m app.cli seed-superadmin
uvicorn app.main:app --reload
```

API: http://localhost:8000 (sin montar SPA; solo rutas `/api/v1` y `/health`).

## Flujo auth (curl)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"superadmin@micole.dev","password":"ChangeMe123!","portal":"platform"}'
```

## Tests

```bash
cd backend
docker compose --profile local-db up db -d   # opcional
docker exec mi-cole-project-db-1 psql -U micole -d postgres -c "CREATE DATABASE micole_test;" 2>nul

pip install -r requirements.txt
set TEST_DATABASE_URL=postgresql+psycopg://postgres:tu_password@localhost:5432/micole_test
pytest -v
```

O dentro del contenedor:

```bash
docker compose exec -e TEST_DATABASE_URL=postgresql+psycopg://...@host.docker.internal:5432/micole_test app pytest -v
```

## SQL (orden)

Fuente única: [`../mi-cole-docs/sql/`](../mi-cole-docs/sql/) — ver su [`README.md`](../mi-cole-docs/sql/README.md).

```bash
cd ../mi-cole-docs/sql
python run_schema.py --bootstrap   # 001 + 002 en BD nueva
cd ../../mi-cole-project/backend
python -m app.cli seed-superadmin  # usuario (bcrypt, no va en SQL)
```

| Archivo | Contenido |
|---------|-----------|
| `001_schema.sql` | schools, users, RBAC, refresh_tokens |
| `002_seed.sql` | permisos `platform.*`, rol superadmin |
| `migrations/003_*.sql` | incrementales (fase 02+) |

CLI backend (alternativa): `python -m app.cli apply-sql` lee la misma carpeta `mi-cole-docs/sql/`.

## Estructura Docker

```
Dockerfile          # node build (SPA) + python runtime
docker-compose.yml  # servicio `app`; `db` solo con --profile local-db
backend/.env        # credenciales locales (gitignored)
```

## Fase actual

**Fase 10** — Portal padres: login, dashboard, hijos y tareas. Ver [`dev-plan/10-fase-portal-padres.md`](../mi-cole-docs/dev-plan/10-fase-portal-padres.md).

**Fase 09** — Escala: paginación server-side, seed multi-colegio. Ver [`backend/README.md`](backend/README.md).

**Fase 08** — Angular 19 SPA: shells `/platform`, `/app`, `/parent`, `/student`. Ver [`frontend/README.md`](frontend/README.md).

**Desarrollo frontend:**

```bash
cd frontend
npm install
npm start          # http://localhost:4200 → proxy API :8000
```

**Monolito (SPA + API mismo puerto):** `docker compose up --build` → http://localhost:8000

**Guía de estilos UI:** [`../mi-cole-docs/design-system/README.md`](../mi-cole-docs/design-system/README.md) (Tailwind + PrimeNG, tokens, branding por sede).

Fases anteriores: 06 facturación, 07 branding login (`011_campus_portal_branding.sql`).

### Probar facturación restringida (UI)

1. SQL (o platform): `UPDATE schools SET billing_access_mode='payment_evidence_only' WHERE slug='colegio-demo';`
2. Owner → `/login/staff/colegio-demo/sede-norte` → **Estudiantes** bloqueado; solo **Suscripción**.
3. En **Suscripción** → subir PDF/imagen (`p-fileUpload`).
4. Superadmin → `/login/platform` → **Cola facturación** → **Aprobar**.
5. Owner → **Estudiantes** vuelve a funcionar.

Credenciales: [`../mi-cole-docs/USUARIOS-DEMO.md`](../mi-cole-docs/USUARIOS-DEMO.md)

Comprobantes se guardan en `backend/storage/uploads/` (configurable con `STORAGE_ROOT`).
