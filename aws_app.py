from flask import Flask, render_template_string, request, session, redirect, url_for, Response, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# --- AWS LAB CONFIGURATION ---
# AWS environments (Elastic Beanstalk/App Runner) look for 'application'
app = Flask(__name__)
application = app 
app.secret_key = 'fresh_basket_aws_lab_session'

# Ensure the database is created in the current working directory
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'freshbasket_pro.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default='user')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(10), nullable=False)
    stock = db.Column(db.Integer, default=100)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    customer_name = db.Column(db.String(100))
    total = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    items_json = db.Column(db.Text)

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:522814716982:freshbasket'

# --- INITIALIZE DATABASE ---
with app.app_context():
    db.create_all()
    if not Product.query.first():
        seeds = [
            Product(name='Royal Gala Apple', price=180, category='fruits', icon='🍎'),
            Product(name='Alphonso Mango', price=450, category='fruits', icon='🥭'),
            Product(name='Organic Carrots', price=60, category='vegetables', icon='🥕'),
            Product(name='Whole Wheat Bread', price=45, category='bakery', icon='🍞'),
            Product(name='Fresh Farm Milk', price=30, category='dairy', icon='🥛')
        ]
        db.session.add_all(seeds)
        db.session.commit()

# --- STYLES & UI ---
MASTER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FreshBasket | AWS Lab Edition</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #22c55e; --dark-bg: #0f172a; --card-bg: #1e293b; --text-main: #f8fafc; --danger: #ef4444; }
        body { background: var(--dark-bg); color: var(--text-main); margin: 0; font-family: 'Poppins', sans-serif; }
        .navbar { background: #000; padding: 1rem 5%; display: flex; justify-content: space-between; border-bottom: 2px solid var(--primary); sticky; top: 0; z-index: 1000; }
        .nav-links a { color: white; text-decoration: none; margin-left: 20px; font-size: 0.9rem; }
        .logo { font-family: 'Cinzel', serif; color: var(--primary); font-size: 1.8rem; text-decoration: none; }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; padding: 40px 5%; }
        .product-card { background: var(--card-bg); padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #334155; }
        .product-card .icon { font-size: 3rem; display: block; }
        .btn-add { background: var(--primary); color: white; border: none; padding: 10px; border-radius: 8px; width: 100%; cursor: pointer; margin-top: 10px; }
        .admin-content { padding: 40px; }
        .order-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .order-table th, .order-table td { padding: 12px; border-bottom: 1px solid #334155; text-align: left; }
        .flash-msg { padding: 15px; background: var(--primary); text-align: center; }
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="/" class="logo">FreshBasket</a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/cart">🛒 ({{ cart_count }})</a>
            {% if session.get('user_id') %}
                <a href="/logout">Logout</a>
            {% else %}
                <a href="/login">Login</a>
            {% endif %}
            <a href="/admin" style="color:var(--primary)">Admin</a>
        </div>
    </nav>

    {% with messages = get_flashed_messages() %}
      {% if messages %}{% for m in messages %}<div class="flash-msg">{{ m }}</div>{% endfor %}{% endif %}
    {% endwith %}

    {% if page == 'home' %}
        <div style="text-align:center; padding:60px 5%; background:rgba(0,0,0,0.3)">
            <h1 style="font-family:'Cinzel'; font-size:3rem">AWS Lab Deployment</h1>
            <p>Your grocery store is now live on AWS!</p>
        </div>
        <div class="product-grid">
            {% for p in products %}
            <div class="product-card">
                <span class="icon">{{ p.icon }}</span>
                <h3>{{ p.name }}</h3>
                <p>₹{{ p.price }}</p>
                <form action="/add-to-cart/{{ p.id }}" method="POST"><button class="btn-add">Add to Basket</button></form>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'admin_dash' %}
        <div class="admin-content">
            <h1>Admin Panel</h1>
            <div style="background:var(--card-bg); padding:20px; border-radius:10px; margin-bottom:30px;">
                <h3>Add Product</h3>
                <form action="/admin/add-product" method="POST" style="display:flex; gap:10px;">
                    <input type="text" name="name" placeholder="Name" required>
                    <input type="number" name="price" placeholder="Price" required>
                    <input type="text" name="icon" placeholder="Emoji" required>
                    <select name="category"><option value="fruits">Fruits</option><option value="vegetables">Veggies</option></select>
                    <button class="btn-add" style="width:auto">Add</button>
                </form>
            </div>
            <table class="order-table">
                <thead><tr><th>Icon</th><th>Name</th><th>Price</th><th>Action</th></tr></thead>
                <tbody>
                    {% for p in all_products_list %}
                    <tr><td>{{ p.icon }}</td><td>{{ p.name }}</td><td>₹{{ p.price }}</td>
                    <td><a href="/admin/delete-product/{{ p.id }}" style="color:var(--danger)">Delete</a></td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

    {% elif page == 'login' %}
        <div style="max-width:400px; margin:100px auto; background:var(--card-bg); padding:40px; border-radius:20px;">
            <h2>Login</h2>
            <form action="/auth-login" method="POST">
                <input type="email" name="email" placeholder="Email" style="width:100%; margin-bottom:10px; padding:10px" required>
                <input type="password" name="password" placeholder="Password" style="width:100%; margin-bottom:20px; padding:10px" required>
                <button class="btn-add">Sign In</button>
            </form>
            <p>Admin Hint: Register with name "Admin" to access panel.</p>
            <a href="/signup" style="color:var(--primary)">Signup</a>
        </div>
    {% elif page == 'signup' %}
        <div style="max-width:400px; margin:100px auto; background:var(--card-bg); padding:40px; border-radius:20px;">
            <h2>Create Account</h2>
            <form action="/auth-signup" method="POST">
                <input type="text" name="fname" placeholder="First Name (Use 'Admin' for dashboard)" style="width:100%; margin-bottom:10px; padding:10px" required>
                <input type="email" name="email" placeholder="Email" style="width:100%; margin-bottom:10px; padding:10px" required>
                <input type="password" name="password" placeholder="Password" style="width:100%; margin-bottom:20px; padding:10px" required>
                <button class="btn-add">Register</button>
            </form>
        </div>
    {% endif %}
</body>
</html>
"""

# --- HELPERS & ROUTES ---
def get_common():
    return {'cart_count': len(session.get('cart', []))}

@app.route('/')
def home():
    products = Product.query.all()
    return render_template_string(MASTER_HTML, page='home', products=products, **get_common())

@app.route('/admin')
def admin():
    if session.get('user_name') != 'Admin':
        flash("Admin Access Required!")
        return redirect(url_for('login'))
    all_p = Product.query.all()
    return render_template_string(MASTER_HTML, page='admin_dash', all_products_list=all_p, **get_common())

@app.route('/admin/add-product', methods=['POST'])
def admin_add_product():
    new_p = Product(name=request.form['name'], price=float(request.form['price']), 
                    category=request.form['category'], icon=request.form['icon'])
    db.session.add(new_p)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete-product/<int:pid>')
def admin_delete_product(pid):
    p = Product.query.get(pid); db.session.delete(p); db.session.commit()
    return redirect(url_for('admin'))

@app.route('/add-to-cart/<int:pid>', methods=['POST'])
def add_to_cart(pid):
    if 'cart' not in session: session['cart'] = []
    p = Product.query.get(pid)
    cart = session['cart']; cart.append(p.id); session['cart'] = cart
    flash(f"{p.name} added!")
    return redirect(url_for('home'))

@app.route('/login')
def login(): return render_template_string(MASTER_HTML, page='login', **get_common())

@app.route('/signup')
def signup(): return render_template_string(MASTER_HTML, page='signup', **get_common())

@app.route('/auth-signup', methods=['POST'])
def auth_signup():
    hashed_pw = generate_password_hash(request.form['password'])
    user = User(first_name=request.form['fname'], email=request.form['email'], password=hashed_pw)
    db.session.add(user); db.session.commit()
    flash("Signup Success!"); return redirect(url_for('login'))

@app.route('/auth-login', methods=['POST'])
def auth_login():
    user = User.query.filter_by(email=request.form['email']).first()
    if user and check_password_hash(user.password, request.form['password']):
        session['user_id'] = user.id
        session['user_name'] = user.first_name
        return redirect(url_for('home'))
    flash("Error!"); return redirect(url_for('login'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('home'))

# --- START SERVER ---
if __name__ == '__main__':
    # Standard AWS Lab ports are 8080 or 5000

    app.run(host='0.0.0.0', port=8080)

