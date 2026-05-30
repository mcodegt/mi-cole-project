# Mi Cole — Frontend (Angular 19)

SPA con cuatro portales lazy-loaded: **platform**, **staff** (`/app`), **parent**, **student**.

**Guía de estilos (Tailwind + PrimeNG, tokens, portales):** [`../../mi-cole-docs/design-system/README.md`](../../mi-cole-docs/design-system/README.md)

**Stack UI:** Tailwind 3 · PrimeNG 19 (Aura) · PrimeIcons · componentes shared `mc-page-header`, `mc-kpi-card`.

## Desarrollo

```bash
cd frontend
npm install
npm start
```

- App: http://localhost:4200  
- API vía proxy → http://127.0.0.1:8000 (`proxy.conf.json`)

Levantá el backend en paralelo:

```bash
cd ../backend
uvicorn app.main:app --reload
```

## Build producción (monolito Docker)

```bash
npm run build
# Salida: dist/mi-cole/browser/
```

El `Dockerfile` del monolito copia esa carpeta a `STATIC_ROOT`.

## Rutas de login

| Portal | URL ejemplo |
|--------|-------------|
| Plataforma | `/login/platform` |
| Staff | `/login/staff/colegio-demo/sede-norte` |
| Padres | `/login/parent/colegio-demo/sede-norte` |
| Estudiantes | `/login/student/colegio-demo/sede-norte` |

Tras login, branding se carga con `GET /api/v1/public/login-context`.

## Matriz guards

| Ruta | Guards |
|------|--------|
| `/login/**` | — |
| `/platform/**` | `authGuard`, `platformGuard` |
| `/app/**` | `authGuard`, `staffContextGuard` |
| `/app/*` (excepto subscription) | + `billingAllowedGuard` si modo restringido |
| `/app/subscription` | siempre accesible con staff |
| `/parent/**`, `/student/**` | `authGuard` (portales completos en fases 10–11) |

## Interceptor

Envía en cada request autenticado:

- `Authorization: Bearer …`
- Staff: `X-Portal`, `X-School-Id`, `X-Campus-Id`
- Platform: `X-Portal: platform`

Ante **401**, intenta `POST /auth/refresh` una vez y reintenta; si falla, limpia sesión.

## Usuarios demo

Documento completo: [`../../mi-cole-docs/USUARIOS-DEMO.md`](../../mi-cole-docs/USUARIOS-DEMO.md)

| Rol | Login | Credenciales |
|-----|-------|--------------|
| Superadmin | `/login/platform` | `superadmin@micole.dev` / `ChangeMe123!` |
| Owner staff | `/login/staff/colegio-demo/sede-norte` | `owner@colegio-demo.dev` / `Demo123!` |
| Operador | `/login/staff/colegio-demo/sede-norte` | `operator@colegio-demo.dev` / `Demo123!` |
| Padre / Estudiante | — | Reservados fases 10–11 (ver doc) |

## Demo facturación (UI-2)

1. Restringir colegio: `UPDATE schools SET billing_access_mode='payment_evidence_only' WHERE slug='colegio-demo';`
2. Owner → `/app/subscription` → subir comprobante
3. Superadmin → `/platform/billing` → Aprobar

## Estructura

```
src/app/
  core/auth/          AuthService, guards, interceptor
  layouts/            *-shell (nav + outlet)
  features/
    auth/             login-page
    platform/         schools, billing queue
    staff/            dashboard, campuses, students, team, subscription
    parent/           placeholder fase 10
    student/          placeholder fase 11
```
