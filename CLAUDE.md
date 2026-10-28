# Decware Order Tracker

Scrapes Decware's public order list daily, records status history, and estimates when each order will pass QC. Django + DRF backend (`decware_order_tracker/`, `orders/`) and a React SPA (`frontend/`). Live at https://decware-orders.info (Heroku).

## Commands

```bash
# Backend (Python 3.12, venv at ./venv)
source venv/bin/activate
python manage.py runserver                                         # API on :8000
python manage.py test --settings=decware_order_tracker.test_settings  # SQLite, no Postgres needed
python manage.py update_orders        # scrape + import + recompute estimates (needs Chrome)
python manage.py compute_estimates    # recompute estimates only
python manage.py compute_estimates --backtest YYYY-MM-DD

# Frontend (Node 24)
cd frontend && npm start                                # :3000, proxies API to :8000
cd frontend && CI=true npx react-scripts test --watchAll=false
```

Always pass `--settings=decware_order_tracker.test_settings` to backend tests; the default settings need a Postgres `DATABASE_URL` from `.env`.

## Architecture

- `decware_order_tracker/`: project settings, URL routing, HTTPS middleware, and the view that serves the React build.
- `orders/`: the only app. Models, scraper, estimation, DRF viewsets, management commands. See `orders/CLAUDE.md`.
- `frontend/`: Create React App + MUI. See `frontend/CLAUDE.md` for the coding standards (Bulletproof React).
- API is mounted at `/api/orders/` and the router adds `orders/`, so list/detail is `/api/orders/orders/`. Every path not under `api/`, `api-auth/`, `api-docs/` or `admin/` returns the React `index.html`.

## Deployment (Heroku)

- `Procfile`: gunicorn web dyno; `release` runs migrations.
- The Node buildpack runs the root `package.json` `build` script, which is `heroku-build.sh`. That script builds the frontend, copies it to `staticfiles/`, and copies `index.html` to `decware_order_tracker/templates/react/`. Both outputs are generated at build time and gitignored.
- The user runs production deploys (`git push heroku main`). Ask them to do it; don't push yourself.

## Gotchas

- With `DEBUG` off, `HerokuHttpsMiddleware` redirects plain-HTTP requests (based on `X-Forwarded-Proto`) and cookies are secure-only. `test_settings` forces this production setup on.
- `scripts/crontab.txt` / `update_orders.sh` are for local scheduled runs. Production scheduling is separate.
- Loose `*.py` scripts in the repo root (`debug_date_parsing.py`, `local_update.py`, …) are gitignored scratch files, not part of the app.
