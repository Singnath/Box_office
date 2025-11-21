import os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import (
    LoginManager, UserMixin, login_user, login_required, logout_user, current_user
)
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

# Load .env (contains SECRET_KEY and DB_PATH)
load_dotenv()
DB_PATH = os.getenv("DB_PATH")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# ---- DB helpers ----
def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ---- Auth setup ----
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, row):
        self.id = row["user_id"]           # flask-login requires .id
        self.email = row["email"]
        self.name = row["name"]
        self.password_hash = row["password_hash"]

    @staticmethod
    def get_by_id(uid):
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
        return User(row) if row else None

    @staticmethod
    def get_by_email(email):
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        return User(row) if row else None

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# ---- Routes ----
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        u = User.get_by_email(email)
        if not u:
            flash("No such user.")
        else:
            if check_password_hash(u.password_hash, password):
                login_user(u)
                return redirect(url_for("dashboard"))
            else:
                flash("Wrong password.")
    return render_template("login.html", title="Login")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    db = get_db()
    # simple chart: events per venue (top 10)
    rows = db.execute("""
        SELECT v.name AS label, COUNT(e.event_id) AS cnt
        FROM venues v
        LEFT JOIN events e ON e.venue_id = v.venue_id
        GROUP BY v.venue_id
        ORDER BY v.venue_id
        LIMIT 10
    """).fetchall()
    labels = [r["label"] for r in rows]
    counts = [r["cnt"] for r in rows]
    return render_template("dashboard.html", title="Dashboard", labels=labels, counts=counts)

# ---------- CRUD: Events ----------
@app.route("/events")
@login_required
def events_list():
    db = get_db()
    events = db.execute("""
        SELECT e.event_id, e.title, e.starts_at, e.ends_at, e.status, v.name AS venue
        FROM events e JOIN venues v ON v.venue_id = e.venue_id
        ORDER BY e.event_id
    """).fetchall()
    return render_template("events_list.html", title="Events", events=events)

@app.route("/events/new", methods=["GET","POST"])
@login_required
def events_new():
    db = get_db()
    venues = db.execute("SELECT venue_id, name FROM venues ORDER BY venue_id").fetchall()
    if request.method == "POST":
        venue_id = request.form["venue_id"]
        title = request.form["title"].strip()
        starts = request.form["starts_at"].strip()
        ends = request.form["ends_at"].strip()
        status = request.form["status"].strip()
        db.execute("INSERT INTO events(venue_id,title,starts_at,ends_at,status) VALUES(?,?,?,?,?)",
                   (venue_id, title, starts, ends, status))
        db.commit()
        return redirect(url_for("events_list"))
    return render_template("event_form.html", title="New Event", venues=venues, event=None)

@app.route("/events/<int:event_id>/edit", methods=["GET","POST"])
@login_required
def events_edit(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
    if not event:
        return "Not found", 404
    venues = db.execute("SELECT venue_id, name FROM venues ORDER BY venue_id").fetchall()
    if request.method == "POST":
        venue_id = request.form["venue_id"]
        title = request.form["title"].strip()
        starts = request.form["starts_at"].strip()
        ends = request.form["ends_at"].strip()
        status = request.form["status"].strip()
        db.execute("""UPDATE events SET venue_id=?, title=?, starts_at=?, ends_at=?, status=?
                      WHERE event_id=?""",
                   (venue_id, title, starts, ends, status, event_id))
        db.commit()
        return redirect(url_for("events_list"))
    return render_template("event_form.html", title="Edit Event", venues=venues, event=event)

@app.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def events_delete(event_id):
    db = get_db()
    db.execute("DELETE FROM events WHERE event_id=?", (event_id,))
    db.commit()
    return redirect(url_for("events_list"))

@app.route("/api/health")
def api_health():
    try:
        db = get_db()
        db.execute("SELECT 1").fetchone()
        return jsonify({"ok": True, "db": "ok"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    # For VS Code debugging, you can set breakpoints and run this file.
    app.run(debug=True)