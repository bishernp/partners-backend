# partners-backend — Render deploy

This repo is the Django API. It needs a **PostgreSQL** database and runs as a
**Web Service**. The front-ends live in the separate `partners-portal` repo.

## 1) PostgreSQL — `bnp-partners-db`
DB name `bnp_partners`, user `bnp_partners`, region e.g. **Frankfurt** (must match
the web service region). Copy its **Internal Database URL** → the web service's
`DATABASE_URL`. (Question catalog is seeded automatically on every deploy.)

## 2) Web Service — `bnp-partners-backend` (Python, same region as the DB)

| Setting | Value |
|---|---|
| Repository | `bishernp/partners-backend` |
| Root Directory | *(leave blank — repo root)* |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py seed_catalog` |
| Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT` |
| Health Check Path | `/healthz` |

### Environment variables
| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.13.8` |
| `DEBUG` | `false` |
| `SECRET_KEY` | *(generate a long random string)* |
| `DATABASE_URL` | *(DB Internal Database URL)* |
| `CORS_ALLOWED_ORIGINS` | `https://partners.bishernp.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://bnp-partners-backend.onrender.com` |
| `FRONTEND_ORIGIN` | `https://partners.bishernp.com` |
| `ALLOWED_HOSTS` | *(optional — `*.onrender.com` is trusted automatically)* |

> Before DNS resolves you can also test from the portal's `…onrender.com` URL by
> adding it to `CORS_ALLOWED_ORIGINS` (comma-separated).

### After the first deploy
Open the service's **Shell** and create the dashboard admin login:
```
python manage.py createsuperuser
```

Live URLs: `…/api/docs/` (API docs), `…/admin/` (Django admin), `…/healthz`.

### Changing the form questions later
Questions are owned by the portal repo. From a checkout where both repos are
siblings: `node scripts/export_catalog.mjs` (regenerates `catalog/seed/catalog.json`),
commit, redeploy (build re-seeds). Point elsewhere with `PARTNERS_FRONTEND=/path/to/partners-frontend`.
