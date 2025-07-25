from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from deep_translator import GoogleTranslator
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE_URL = os.getenv("${{ Postgres.DATABASE_URL }}")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

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
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO messages (name, email, subject, message) VALUES (%s, %s, %s, %s)",
                        (name, email, subject, message)
                    )
                    conn.commit()
            flash("Your message has been sent!", "success")
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
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                                (username, email, hashed_pw))
                    conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except Exception:
            flash("Username or email already exists.", "warning")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cur.fetchone()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "info")
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
