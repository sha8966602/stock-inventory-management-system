from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "stock_secret_key"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT DATABASE ----------------
def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        quantity INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        qty INTEGER,
        date TEXT
    )
    """)

    # Default admin
    cur.execute("INSERT OR IGNORE INTO users VALUES (1,'admin','admin')")
    db.commit()

init_db()

# ---------------- INDEX PAGE ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = cur.fetchone()

        if user:
            session["user"] = u
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

# ---------------- PRODUCTS ----------------
@app.route("/products")
def products():
    if "user" not in session:
        return redirect("/login")
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    return render_template("products.html", products=data)

# ---------------- ADD PRODUCT ----------------
@app.route("/add_product", methods=["POST"])
def add_product():
    if "user" not in session:
        return redirect("/login")

    name = request.form["name"]
    price = request.form["price"]
    qty = request.form["qty"]

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO products(name, price, quantity) VALUES (?, ?, ?)",
        (name, price, qty)
    )
    db.commit()
    return redirect("/products")

# ---------------- UPDATE PRODUCT ----------------
@app.route("/update_product/<int:id>", methods=["POST"])
def update_product(id):
    if "user" not in session:
        return redirect("/login")

    name = request.form["name"]
    price = request.form["price"]
    quantity = request.form["quantity"]

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        UPDATE products 
        SET name=?, price=?, quantity=? 
        WHERE id=?
    """, (name, price, quantity, id))
    db.commit()
    return redirect("/products")

# ---------------- DELETE PRODUCT ----------------
@app.route("/delete_product/<int:id>")
def delete_product(id):
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (id,))
    db.commit()
    return redirect("/products")

# ---------------- SELL PRODUCT ----------------
@app.route("/sell", methods=["POST"])
def sell():
    if "user" not in session:
        return redirect("/login")

    pid = request.form["product_id"]
    qty = int(request.form["qty"])

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "UPDATE products SET quantity = quantity - ? WHERE id = ?",
        (qty, pid)
    )

    cur.execute(
        "INSERT INTO sales(product_id, qty, date) VALUES (?, ?, ?)",
        (pid, qty, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )

    db.commit()
    return redirect("/products")

# ---------------- SALES HISTORY ----------------
@app.route("/sales")
def sales():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT sales.id, products.name, sales.qty, sales.date
        FROM sales
        JOIN products ON sales.product_id = products.id
        ORDER BY sales.id DESC
    """)
    data = cur.fetchall()
    return render_template("sales.html", sales=data)

# ---------------- LOW STOCK ALERT ----------------
@app.route("/low_stock")
def low_stock():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM products WHERE quantity <= 5")
    data = cur.fetchall()
    return render_template("low_stock.html", products=data)

# ---------------- SALES CHART ----------------
@app.route("/chart")
def chart():
    if "user" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT products.name, SUM(sales.qty)
        FROM sales
        JOIN products ON sales.product_id = products.id
        GROUP BY products.name
    """)
    result = cur.fetchall()

    labels = [row[0] for row in result]
    values = [row[1] for row in result]

    return render_template("chart.html", labels=labels, values=values)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
