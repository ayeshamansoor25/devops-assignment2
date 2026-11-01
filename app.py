"""Simple Notes web app (Flask + PostgreSQL) for CSC418 Assignment 2."""
import os
import time
from html import escape

import psycopg2
from flask import Flask, request, redirect, jsonify

REGISTRATION = "FA23-BDS-006"
APP_TITLE = os.environ.get("APP_TITLE", "Notes App")

DB = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "notesdb"),
    "user": os.environ.get("DB_USER", "notesuser"),
    "password": os.environ.get("DB_PASSWORD", "NotesPass123"),
}

app = Flask(__name__)


def query(sql, params=(), fetch=False):
    conn = psycopg2.connect(**DB)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall() if fetch else None
    finally:
        conn.close()


def init_db():
    """Wait for the database container, then create the table if needed."""
    for _ in range(60):
        try:
            query("""CREATE TABLE IF NOT EXISTS notes (
                         id SERIAL PRIMARY KEY,
                         content TEXT NOT NULL,
                         created_at TIMESTAMP DEFAULT NOW())""")
            print("Database ready.", flush=True)
            return
        except psycopg2.OperationalError:
            print("Waiting for database...", flush=True)
            time.sleep(2)
    raise RuntimeError("Database not reachable")


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
 body{{font-family:Arial,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;background:#f5f7fb;color:#222}}
 h1{{margin-bottom:4px}} .sub{{color:#666;margin-top:0}}
 form{{display:flex;gap:8px;margin:24px 0}} input[type=text]{{flex:1;padding:10px;border:1px solid #ccc;border-radius:6px}}
 button{{padding:10px 18px;border:0;border-radius:6px;background:#2563eb;color:#fff;cursor:pointer}}
 li{{background:#fff;padding:12px;border-radius:6px;margin-bottom:8px;list-style:none;box-shadow:0 1px 2px #0001}}
 ul{{padding:0}} small{{color:#888}}
</style></head><body>
<h1>{title}</h1>
<p class="sub">Registration: {reg} &middot; Data stored in PostgreSQL ({count} notes)</p>
<form method="post" action="/add">
 <input type="text" name="content" placeholder="Write a note..." required>
 <button type="submit">Add note</button>
</form>
<ul>{items}</ul>
</body></html>"""


@app.route("/")
def index():
    rows = query("SELECT id, content, created_at FROM notes ORDER BY id DESC", fetch=True)
    items = "".join(
        f"<li>{escape(r[1])}<br><small>#{r[0]} &middot; {r[2]:%Y-%m-%d %H:%M}</small></li>" for r in rows
    ) or "<li><small>No notes yet. Add one above!</small></li>"
    return PAGE.format(title=escape(APP_TITLE), reg=REGISTRATION, count=len(rows), items=items)


@app.route("/add", methods=["POST"])
def add():
    content = request.form.get("content", "").strip()
    if content:
        query("INSERT INTO notes (content) VALUES (%s)", (content,))
    return redirect("/")


@app.route("/health")
def health():
    try:
        count = query("SELECT COUNT(*) FROM notes", fetch=True)[0][0]
        return jsonify(status="ok", database="connected", notes=count, app=APP_TITLE)
    except Exception as e:
        return jsonify(status="error", database=str(e)), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
