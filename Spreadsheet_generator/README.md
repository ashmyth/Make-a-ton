# Brightloop purchase register (Django + PostgreSQL)

Every order / line / payment save auto-updates a PostgreSQL register table and
rewrites `media/register/purchase_register.xlsx` (sheets: All Purchases, Subscriptions, Products).

## Run
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    createdb brightloop                       # or via psql
    export DB_PASSWORD=...                    # see .env.example
    python manage.py makemigrations sales register
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

## Use
1. /admin -> add Customer, Product (+Variants), Plan.
2. Add Order + lines (+ payments). Select orders -> "Confirm selected orders".
3. Spreadsheet updates itself. Download fresh copy: /register/download/ (staff login).
4. Backfill old data: `python manage.py rebuild_register`
