# Taxi Management App

A production-ready Flask + PostgreSQL taxi management app for Railway.

## Railway environment variables

Required:

- `DATABASE_URL` - Railway PostgreSQL connection string
- `SECRET_KEY` - long random value for secure sessions
- `ADMIN_USERNAME` - admin username
- `ADMIN_PASSWORD_HASH` - Werkzeug password hash

Optional fallback:

- `ADMIN_PASSWORD` - plain password checked at runtime if no hash is set. Use `ADMIN_PASSWORD_HASH` in production.

Generate a password hash:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

## Routes

- `/book` - public customer booking page
- `/admin` - admin dashboard
- `/health` - app health check
- `/debug-db` - database connectivity and table diagnostics

## Railway deploy

This project includes `railway.json`, `Procfile`, `runtime.txt`, and `requirements.txt`.
See `RAILWAY_DEPLOYMENT.md` for the exact Railway deployment checklist.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."
export SECRET_KEY="change-me"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="change-me"
flask --app app:create_app run --debug
```
