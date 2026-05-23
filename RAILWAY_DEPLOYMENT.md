# Railway Deployment Guide

## Production Variables

Add these on the Railway app service, not the PostgreSQL service.

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=replace-with-a-long-random-secret
FLASK_ENV=production
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=replace-with-werkzeug-password-hash
PGSSLMODE=require
PYTHONUNBUFFERED=1
```

If the PostgreSQL service is not named `Postgres`, change `DATABASE_URL` to use the real service name:

```env
DATABASE_URL=${{YOUR_POSTGRES_SERVICE_NAME.DATABASE_URL}}
```

Generate an admin password hash:

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password', method='pbkdf2:sha256:1000000'))"
```

## PostgreSQL

1. Open the Railway project.
2. Click `+ New`.
3. Select `Database` -> `PostgreSQL`.
4. Wait for the Postgres service to deploy.
5. In the app service, set `DATABASE_URL` to reference the PostgreSQL service variable.

## GitHub Deployment

1. Push this repository to GitHub.
2. In Railway, click `+ New`.
3. Select `GitHub Repo`.
4. Choose this repo and the `main` branch.
5. Add the production variables.
6. Deploy.

Railway will use `railway.json` for the start command and `/health` deployment healthcheck.

## Domain

1. Open the app service in Railway.
2. Go to `Settings` -> `Networking`.
3. Generate a Railway domain first and test it.
4. Add a custom domain when ready.
5. Create the DNS record Railway shows at your registrar.
6. Wait for verification and HTTPS certificate provisioning.

## Post-Deploy Tests

Replace `YOUR_URL` with the Railway or custom domain.

```bash
curl https://YOUR_URL/health
curl https://YOUR_URL/debug-db
```

Then test:

1. `https://YOUR_URL/admin`
2. Username from `ADMIN_USERNAME`.
3. Password used to generate `ADMIN_PASSWORD_HASH`.
4. `https://YOUR_URL/book`
5. Submit a booking and confirm it appears in admin appointments.
