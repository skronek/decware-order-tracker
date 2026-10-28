# Decware Order Tracker

Tracks orders on [Decware's public order list](https://orders.decware.com) and estimates when each one will pass QC. Live at https://decware-orders.info.

The scraper downloads the order list daily, records each status change, and recomputes completion estimates with a queue model (position in the build queue ÷ recent start rate, plus typical build time).

## Stack

- **Backend:** Django + Django REST Framework, PostgreSQL, Selenium (headless Chrome) for scraping
- **Frontend:** React (Create React App) + MUI
- **Hosting:** Heroku

## Development

Requires Python 3.12, Node 24, and a `.env` with `DATABASE_URL` (Postgres) and `SECRET_KEY`.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver                 # API on :8000

cd frontend && npm install && npm start    # app on :3000, proxies the API

python manage.py update_orders             # scrape + import + recompute estimates (needs Chrome)
```

Tests:

```bash
python manage.py test --settings=decware_order_tracker.test_settings   # SQLite, no Postgres needed
cd frontend && CI=true npx react-scripts test --watchAll=false
```

See `CLAUDE.md`, `orders/CLAUDE.md` and `frontend/CLAUDE.md` for architecture and conventions.
