from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from deep_translator import GoogleTranslator

app = Flask(__name__)
app.secret_key = os.urandom(24)

def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/whoiam")
def whoiam():
    return render_template("whoiam.html")

@app.route("/nothing")
def nothing():
    return render_template("nothing.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        if not name or not email or not subject or not message:
            flash("All fields are required!", "danger")
            return redirect(url_for("contact"))

        try:
            with sqlite3.connect("users.db") as conn:
                conn.execute(
                    "INSERT INTO messages (name, email, subject, message) VALUES (?, ?, ?, ?)",
                    (name, email, subject, message)
                )
                conn.commit()
            flash("Your message has been sent!", "success")
            return redirect(url_for("contact"))
        except Exception as e:
            flash(f"Error while sending message: {e}", "danger")
            return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not username or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)

        try:
            with sqlite3.connect("users.db") as conn:
                conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                             (username, email, hashed_pw))
                conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "warning")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        with sqlite3.connect("users.db") as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash(f"Welcome back, {user[1]}!", "info")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/translate", methods=["POST"])
def translate():
    if "user_id" not in session:
        return redirect("/login")

    text = request.form.get("text")
    target_lang = request.form.get("lang")

    try:
        translated_text = GoogleTranslator(source="auto", target=target_lang).translate(text)
    except Exception as e:
        translated_text = f"Translation failed: {e}"

    return render_template("dashboard.html", username=session["username"], translated=translated_text)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
