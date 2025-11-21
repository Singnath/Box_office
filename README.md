# Box Office App

**Quick start**
- Python 3.10+
- Install: `python -m venv .venv && source .venv/bin/activate && pip install Flask Flask-Login python-dotenv`
- Create `.env`:
SECRET_KEY=dev-secret-change-me
DB_PATH=/absolute/path/to/box_office.db
- Run: `export FLASK_APP=app && flask run` → http://127.0.0.1:5000

**Login (test)**
- Email: `user1@example.com`
- Password: `test123`

**Health check**
- `GET /api/health` → `{"ok": true, "db": "ok"}` when DB is reachable

**Notes**
- Uses SQLite, Flask, Flask-Login. Templates under `templates/`, styles in `static/`.