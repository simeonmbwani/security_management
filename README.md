# SGMIS Backend (Django + DRF)

Security Guard Management Information System — REST API.

## Modules implemented

| Module | App | Notes |
|---|---|---|
| Users / roles / stations | `apps.accounts` | Admin, Supervisor, Guard roles; multi-station support |
| Digital Occurrence Book | `apps.occurrence_book` | Auto-numbered entries, photos, supervisor comments |
| Patrol monitoring | `apps.patrols` | Checkpoints, GPS + photo per visit, overdue detection |
| Duty roster / shifts | `apps.shifts` | **Automatic 4-day pair rotation engine** — see `apps/shifts/services.py` |
| Shift handover | `apps.shifts` | Digital accept/sign-off flow |
| Leave (casual/vacation/compensation) | `apps.leave_management` | **Accrual + expiry engine** — see `apps/leave_management/services.py` |
| Exam deployment | `apps.exam_management` | Blocks double-booking, reassigns remaining roster automatically |
| Vehicle escort | `apps.escort_management` | Locks guard out of normal roster while "On Escort Duty" |
| Incident reporting | `apps.incidents` | Emergency-style reports, auto-alerts supervisors |
| Visitor register | `apps.visitors` | |
| Key & equipment registers | `apps.registers` | |
| Notifications | `apps.notifications` | In-app; stubs for push/SMS provider |
| Reports | `apps.reports` | PDF (reportlab) + Excel (openpyxl) exports |

The three "engines" described in the original plan are implemented as
plain, readable service functions (not hidden in views), so you can unit
test and extend them independently:

- `apps/shifts/services.py` — duty roster / rotation
- `apps/leave_management/services.py` — leave accrual, expiry, holiday compensation
- `apps/exam_management/services.py` — exam deployment vs normal roster conflict handling

## Quick start (Docker — recommended)

```bash
cd backend
cp .env.example .env        # edit SECRET_KEY, DB password, etc.
docker compose up --build
```

Then, in a second terminal:

```bash
docker compose exec backend python manage.py createsuperuser   # optional, seed command below already makes one
docker compose exec backend python manage.py seed_demo_data
docker compose exec backend python manage.py setup_periodic_tasks
```

API is now live at `http://127.0.0.1:8000/api/`, docs at
`http://127.0.0.1:8000/api/docs/`, admin at `http://127.0.0.1:8000/admin/`.

Demo login (created by `seed_demo_data`): `admin` / `ChangeMe123!` — **change
this immediately in production.**

## Quick start (manual / no Docker)

Requires: Python 3.12, PostgreSQL 14+, Redis (for Celery).

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# create the Postgres database + user first, matching .env
cp .env.example .env
python manage.py migrate
python manage.py seed_demo_data
python manage.py setup_periodic_tasks
python manage.py runserver
```

In separate terminals, run the background workers (needed for
notifications, roster auto-generation, leave accrual, overdue-patrol
detection):

```bash
celery -A sgmis_project worker -l info
celery -A sgmis_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Authentication

JWT via `djangorestframework-simplejwt`.

```
POST /api/auth/login/     { "username": "...", "password": "..." }  -> { access, refresh }
POST /api/auth/refresh/   { "refresh": "..." }                       -> { access }
POST /api/auth/logout/    { "refresh": "..." }                       (blacklists it)
```

Send `Authorization: Bearer <access>` on every other request.

## Key endpoints (non-exhaustive — see /api/docs/ for the full list)

```
GET/POST   /api/accounts/users/
GET/PATCH  /api/accounts/users/me/
GET/POST   /api/ob/entries/
GET/POST   /api/patrols/patrols/            POST /api/patrols/patrols/{id}/finish/
POST       /api/patrols/patrols/{id}/log_checkpoint/
GET        /api/shifts/shifts/today/
POST       /api/shifts/shifts/generate/     (supervisor/admin — bulk-generate roster)
POST       /api/shifts/handovers/{id}/accept/
GET/POST   /api/leave/applications/         POST .../{id}/approve/  .../{id}/reject/
GET        /api/leave/balances/mine/
POST       /api/exams/exams/{id}/assign_guard/
POST       /api/escorts/missions/{id}/complete/
POST       /api/incidents/reports/          POST .../{id}/acknowledge/  .../{id}/resolve/
GET        /api/reports/daily-ob/?format=pdf
GET        /api/reports/leave-balances/?format=excel
```

## Configuration knobs

All business-rule numbers (cycle length, leave accrual rates/caps, holiday
compensation days, patrol overdue threshold) live in one place:
`sgmis_project/settings.py` → `SGMIS_SETTINGS`. Change them there rather
than hunting through the codebase.

## What you'll still want to do before going to production

1. Set a strong `SECRET_KEY`, `DEBUG=False`, and real `ALLOWED_HOSTS` in `.env`.
2. Put this behind HTTPS (nginx/Caddy + Let's Encrypt, or a managed platform).
3. Wire `apps/notifications/services.py` `send_push` / `send_sms` to a real
   provider (Firebase Cloud Messaging, Africa's Talking, Twilio, etc.).
4. Review `core/permissions.py` against your organisation's actual approval
   chain if it differs from Admin > Supervisor > Guard.
5. Add automated tests (the service-layer functions in `services.py` files
   are written to be easy to unit test in isolation).
