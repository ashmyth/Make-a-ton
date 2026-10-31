# Brightloop backend — Identity, Access & Customer Foundation

Django 5.2 + DRF + PostgreSQL (needs the `citext` extension; migration 0001 creates it).

## Setup
```bash
pip install -r requirements-dev.txt
cp .env.example .env   # export these variables; nothing is hardcoded in settings
python manage.py migrate
python manage.py createcachetable          # DB cache backs DRF throttling
python manage.py bootstrap_admin --email you@company.com   # first Administrator (prompts for password)
python manage.py seed_data                 # DEBUG only; random passwords printed once
```
Run tests (needs a reachable PostgreSQL; `pytest.ini` has the test `DATABASE_URL`): `pytest`
Quality: `ruff check .` · `lint-imports` · `python manage.py spectacular --validate`

## Production notes
- Set `TRUSTED_PROXY_COUNT=1` behind Caddy so audit IPs and throttling use the real client IP.
- Password reset email uses Django's email backend (`EMAIL_BACKEND`, `EMAIL_HOST`, ...).
- Docs: `/api/docs/`, schema: `/api/schema/`.
