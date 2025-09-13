import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"pdf"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- DB ---
def get_db():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, filename TEXT)")
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",(username,email,password))
            conn.commit()
            flash("Registered successfully! Please log in.","success")
            return redirect(url_for("login"))
        except:
            flash("User already exists or invalid.","danger")
        conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"],password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Logged in!","success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials","danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.","info")
    return redirect(url_for("login"))

@app.route("/books", methods=["GET","POST"])
def books():
    conn = get_db()
    if request.method == "POST":
        title = request.form["title"]
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            conn.execute("INSERT INTO books (title,filename) VALUES (?,?)",(title,filename))
            conn.commit()
            flash("Book uploaded!","success")
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template("books.html", books=books)

@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id=?",(book_id,)).fetchone()
    if book:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], book["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
        conn.execute("DELETE FROM books WHERE id=?",(book_id,))
        conn.commit()
        flash("Book deleted.","info")
    conn.close()
    return redirect(url_for("books"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/members")
def members():
    conn = get_db()
    members = conn.execute("SELECT id,username,email FROM users").fetchall()
    conn.close()
    return render_template("members.html", members=members)

@app.route("/delete_member/<int:member_id>", methods=["POST"])
def delete_member(member_id):
    if "user_id" not in session:
        flash("Login required","danger")
        return redirect(url_for("login"))
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id=?",(member_id,))
    conn.commit()
    conn.close()
    flash("Member deleted.","info")
    return redirect(url_for("members"))

if __name__ == "__main__":
    app.run(debug=True)
