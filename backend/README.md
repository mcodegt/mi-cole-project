# Mi Cole — Backend (FastAPI)

API REST multicolegio: auth, RBAC, estudiantes, padres, facturación, plataforma.

## Desarrollo

```bash
cd mi-cole-project/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Docs interactivas: http://localhost:8000/docs

## CLI

```bash
python -m app.cli seed-superadmin
python -m app.cli seed-demo
python -m app.cli seed-bulk-students --reset --schools 20
```

Ver [`../../mi-cole-docs/USUARIOS-DEMO.md`](../../mi-cole-docs/USUARIOS-DEMO.md) para credenciales y datos de escala.

## Tests

```bash
set TEST_DATABASE_URL=postgresql+psycopg://postgres:PASSWORD@localhost:5432/micole_test
pytest -v
pytest -v -m slow          # pruebas de volumen (seed grande)
pytest -v -m "not slow"    # suite rápida
```

## Paginación (Fase 09)

Listados staff/platform devuelven:

```json
{ "items": [...], "total": 10000, "page": 1, "limit": 25 }
```

- Default `limit=25`, máximo `limit=100`.
- Filtros en estudiantes: `campus_id`, `status`, `q` (ILIKE en `full_name` / `code`).
- Filtros en padres: `status`, `q` (ILIKE en `full_name` / `email`).

## Performance — query principal de estudiantes

Índices (ver `mi-cole-docs/sql/migrations/006_students_parents.sql`):

- `idx_students_school_id` → `(school_id)`
- `idx_students_school_campus` → `(school_id, campus_id)`

Consulta típica del listado staff (paginada):

```sql
EXPLAIN ANALYZE
SELECT *
FROM students
WHERE school_id = '…'
  AND campus_id = '…'          -- opcional
  AND status = 'active'        -- opcional
  AND (full_name ILIKE '%x%' OR code ILIKE '%x%')
ORDER BY full_name
OFFSET 0 LIMIT 25;
```

En dev con ~10k estudiantes repartidos en 20 colegios, `page=1&limit=25` debe responder en **< 2 s** sin cache. PostgreSQL usa el índice `(school_id, campus_id)` cuando filtrás por sede; con solo `school_id` usa `idx_students_school_id`.

Conteos de plan (`plan_limits`) usan `COUNT(*)` en SQL, nunca cargan la colección completa.

### Seed de volumen

```bash
python -m app.cli seed-bulk-students --reset
```

Genera colegios `scale-colegio-*` con estudiantes distribuidos por sede. Para borrar: `--reset` o `DELETE` en cascada vía slug.

## Estructura

```
app/
  routes/          # endpoints FastAPI
  services/        # lógica de negocio
  models/          # SQLAlchemy
  core/authz.py    # AuthzContext, guards
  cli.py           # comandos seed / SQL
tests/             # pytest (BD micole_test)
```
