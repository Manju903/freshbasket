from flask import Flask, render_template_string, request, session, redirect, url_for, Response, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# AWS looks for a variable named 'application'
application = Flask(__name__)
application.secret_key = 'fresh_basket_enterprise_edition_v22'

# --- DATABASE CONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
# Absolute path ensures SQLite works correctly on AWS Linux servers
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'freshbasket_pro.db')
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:522814716982:freshbasket'

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

with application.app_context():
    db.create_all()
    if not Product.query.first():
        seeds = [
            Product(name='Royal Gala Apple', price=180, category='fruits', icon='🍎'),
            Product(name='Alphonso Mango', price=450, category='fruits', icon='🥭'),
            Product(name='Organic Strawberry', price=150, category='fruits', icon='🍓'),
            Product(name='Organic Carrots', price=60, category='vegetables', icon='🥕'),
            Product(name='Wild Mushroom', price=120, category='vegetables', icon='🍄'),
            Product(name='Whole Wheat Bread', price=45, category='bakery', icon='🍞'),
            Product(name='Fresh Farm Milk', price=30, category='dairy', icon='🥛'),
            Product(name='Organic Broccoli', price=90, category='vegetables', icon='🥦'),
            Product(name='Fresh Eggs', price=110, category='dairy', icon='🥚')
        ]
        db.session.add_all(seeds)
        db.session.commit()

# --- UI TEMPLATE ---
# Note: I have updated the "Icon" input to a <select> dropdown for easier use!
MASTER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FreshBasket | Premium Grocery</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #22c55e; --primary-hover: #16a34a;
            --dark-bg: #0f172a; --card-bg: #1e293b;
            --text-main: #f8fafc; --text-muted: #94a3b8;
            --danger: #ef4444; --accent: #3b82f6;
        }
        * { box-sizing: border-box; transition: all 0.2s ease-in-out; }
        body { background-color: var(--dark-bg); color: var(--text-main); margin: 0; font-family: 'Poppins', sans-serif; line-height: 1.6; }
        .navbar { background: rgba(0,0,0,0.95); backdrop-filter: blur(10px); padding: 1rem 5%; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; border-bottom: 2px solid var(--primary); }
        .nav-links { display: flex; align-items: center; gap: 20px; }
        .nav-links a { color: white; text-decoration: none; font-weight: 500; font-size: 0.9rem; }
        .nav-links a:hover { color: var(--primary); }
        .logo { font-family: 'Cinzel', serif; color: var(--primary); font-size: 1.8rem; text-decoration: none; }
        .search-form { background: white; border-radius: 25px; padding: 2px 15px; display: flex; align-items: center; }
        .search-form input { border: none; padding: 8px; outline: none; width: 180px; font-family: inherit; }
        .search-form button { background: none; border: none; cursor: pointer; font-size: 1.1rem; }
        .slider-container { width: 100%; height: 400px; overflow: hidden; position: relative; }
        .slides { display: flex; width: 300%; height: 100%; animation: slideAnim 15s infinite; }
        .slide { width: 33.33%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background-size: cover; background-position: center; background-blend-mode: overlay; background-color: rgba(0,0,0,0.4); }
        .slide h1 { font-family: 'Cinzel', serif; font-size: 3.5rem; margin: 0; color: white; text-shadow: 2px 2px 10px rgba(0,0,0,0.5); }
        @keyframes slideAnim { 0%, 30% { transform: translateX(0); } 33%, 63% { transform: translateX(-33.33%); } 66%, 96% { transform: translateX(-66.66%); } 100% { transform: translateX(0); } }
        .cat-strip { display: flex; justify-content: center; gap: 50px; padding: 40px 5%; background: #161e2e; border-bottom: 1px solid #334155; }
        .cat-card { text-align: center; color: white; text-decoration: none; width: 100px; }
        .cat-card span { font-size: 3rem; display: block; background: var(--card-bg); border-radius: 50%; width: 80px; height: 80px; line-height: 80px; margin: 0 auto 10px; border: 2px solid transparent; }
        .cat-card:hover span { border-color: var(--primary); transform: scale(1.1); }
        .section-header { display: flex; justify-content: space-between; align-items: flex-end; padding: 40px 5% 20px; }
        .section-header h2 { margin: 0; font-family: 'Cinzel', serif; border-left: 5px solid var(--primary); padding-left: 15px; }
        .view-all-btn { color: var(--primary); text-decoration: none; font-weight: 600; border-bottom: 1px solid transparent; }
        .view-all-btn:hover { border-color: var(--primary); }
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 30px; padding: 20px 5% 60px; }
        .product-card { background: var(--card-bg); border-radius: 20px; padding: 30px; text-align: center; border: 1px solid #334155; position: relative; }
        .product-card:hover { transform: translateY(-10px); border-color: var(--primary); }
        .product-card .icon { font-size: 4rem; margin-bottom: 15px; display: block; }
        .product-card h3 { margin: 10px 0; font-size: 1.2rem; }
        .product-card .price { font-size: 1.4rem; color: var(--primary); font-weight: 600; margin: 10px 0; }
        .btn-add { background: var(--primary); color: white; border: none; padding: 12px; border-radius: 12px; width: 100%; cursor: pointer; font-weight: 600; font-size: 1rem; }
        .btn-add:hover { background: var(--primary-hover); }
        .auth-container { max-width: 450px; margin: 80px auto; background: var(--card-bg); padding: 40px; border-radius: 25px; border: 1px solid #334155; text-align: center; }
        .form-group { text-align: left; margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; color: var(--text-muted); }
        .form-group input, .form-group select { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #334155; background: var(--dark-bg); color: white; font-size: 1rem; }
        .admin-layout { display: grid; grid-template-columns: 250px 1fr; min-height: 90vh; }
        .admin-sidebar { background: #000; padding: 30px; border-right: 1px solid #334155; }
        .admin-content { padding: 40px; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }
        .stat-box { background: var(--card-bg); padding: 30px; border-radius: 20px; text-align: center; border: 1px solid var(--primary); }
        .order-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .order-table th, .order-table td { padding: 15px; text-align: left; border-bottom: 1px solid #334155; }
        .flash-msg { padding: 15px; background: var(--primary); color: white; text-align: center; position: fixed; top: 80px; width: 100%; z-index: 999; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-links">
            <a href="/">Home</a>
            <form action="/search" method="GET" class="search-form">
                <input type="text" name="q" placeholder="Search Freshness...">
                <button type="submit">🔍</button>
            </form>
            <a href="/cart">🛒 <span id="cart-count">{{ cart_count }}</span></a>
            {% if session.get('user_id') %}
                <a href="/orders">History</a>
                <a href="/logout" style="color:var(--danger)">Logout</a>
            {% else %}
                <a href="/login">👤 Login</a>
            {% endif %}
            <a href="/admin" style="background:var(--primary); padding:5px 12px; border-radius:20px; color:black; font-weight:bold;">Admin</a>
        </div>
        <a href="/" class="logo">FreshBasket</a>
    </nav>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for message in messages %}
          <div class="flash-msg">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {% if page == 'home' %}
        <div class="slider-container">
            <div class="slides">
                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200')">
                    <h1>Organic Excellence</h1>
                </div>
                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1606787366850-de6330128bfc?w=1200')">
                    <h1>Healthy Living</h1>
                </div>
                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=1200')">
                    <h1>Fresh Harvest</h1>
                </div>
            </div>
        </div>

        <div class="cat-strip">
            <a href="/category/fruits" class="cat-card"><span>🍎</span>Fruits</a>
            <a href="/category/vegetables" class="cat-card"><span>🥦</span>Veggies</a>
            <a href="/category/bakery" class="cat-card"><span>🍞</span>Bakery</a>
            <a href="/category/dairy" class="cat-card"><span>🥛</span>Dairy</a>
        </div>

        <div class="section-header"><h2>Featured Fruits</h2></div>
        <div class="product-grid">
            {% for p in fruits %}
            <div class="product-card">
                <span class="icon">{{ p.icon }}</span>
                <h3>{{ p.name }}</h3>
                <p class="price">₹{{ p.price }}</p>
                <form action="/add-to-cart/{{ p.id }}" method="POST"><button class="btn-add">Add to Basket</button></form>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'admin_dash' %}
        <div class="admin-layout">
            <div class="admin-sidebar">
                <h3 style="color:var(--primary)">Management</h3>
                <a href="/admin" style="color:white; text-decoration:none;">Refresh Dashboard</a>
            </div>
            <div class="admin-content">
                <h1>Admin Console</h1>
                <div class="stats-grid">
                    <div class="stat-box"><small>Revenue</small><h2>₹{{ revenue }}</h2></div>
                    <div class="stat-box"><small>Orders</small><h2>{{ orders|length }}</h2></div>
                    <div class="stat-box"><small>Items</small><h2>{{ products_count }}</h2></div>
                </div>

                <div style="background:var(--card-bg); padding:30px; border-radius:20px; border:1px solid var(--primary);">
                    <h3>Add New Product</h3>
                    <form action="/admin/add-product" method="POST" style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr 150px; gap:10px; align-items:end;">
                        <div class="form-group"><label>Name</label><input type="text" name="name" required></div>
                        <div class="form-group"><label>Price</label><input type="number" name="price" required></div>
                        <div class="form-group">
                            <label>Category</label>
                            <select name="category">
                                <option value="fruits">Fruits</option>
                                <option value="vegetables">Veggies</option>
                                <option value="bakery">Bakery</option>
                                <option value="dairy">Dairy</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Icon (Select One)</label>
                            <select name="icon">
                                <option value="🍎">🍎 Apple</option><option value="🍌">🍌 Banana</option>
                                <option value="🍇">🍇 Grapes</option><option value="🥭">🥭 Mango</option>
                                <option value="🥦">🥦 Broccoli</option><option value="🥕">🥕 Carrot</option>
                                <option value="🍞">🍞 Bread</option><option value="🥛">🥛 Milk</option>
                                <option value="🥚">🥚 Eggs</option><option value="🥩">🥩 Meat</option>
                            </select>
                        </div>
                        <button class="btn-add">Add Item</button>
                    </form>
                </div>

                <h3>Inventory</h3>
                <table class="order-table">
                    <thead><tr><th>Icon</th><th>Name</th><th>Price</th><th>Action</th></tr></thead>
                    <tbody>
                        {% for p in all_products_list %}
                        <tr><td>{{ p.icon }}</td><td>{{ p.name }}</td><td>₹{{ p.price }}</td><td><a href="/admin/delete-product/{{ p.id }}" style="color:var(--danger)">Remove</a></td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% elif page == 'login' %}
        <div class="auth-container">
            <h1>Login</h1>
            <form action="/auth-login" method="POST">
                <div class="form-group"><label>Email</label><input type="email" name="email" required></div>
                <div class="form-group"><label>Password</label><input type="password" name="password" required></div>
                <button class="btn-add">Sign In</button>
            </form>
        </div>
    {% elif page == 'cart' %}
        <div class="auth-container">
            <h1>Your Basket</h1>
            {% for item in items %}
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span>{{ item.icon }} {{ item.name }}</span>
                    <span>₹{{ item.price }}</span>
                </div>
            {% endfor %}
            <a href="/checkout" class="btn-add" style="display:block; text-decoration:none;">Checkout Total: ₹{{ total }}</a>
        </div>
    {% endif %}
    <footer style="text-align:center; padding:50px; color:var(--text-muted)">FreshBasket Premium &copy; 2026</footer>
</body>
</html>
"""

# --- ROUTES ---
def get_common():
    cart = session.get('cart', [])
    return {'cart_count': len(cart)}

@application.route('/')
def home():
    fruits = Product.query.filter_by(category='fruits').limit(4).all()
    return render_template_string(MASTER_HTML, page='home', fruits=fruits, **get_common())

@application.route('/admin')
def admin():
    if not session.get('user_id'): return redirect(url_for('login'))
    all_orders = Order.query.all()
    all_products = Product.query.all()
    revenue = sum(o.total for o in all_orders)
    return render_template_string(MASTER_HTML, page='admin_dash', orders=all_orders, all_products_list=all_products, revenue=revenue, products_count=len(all_products), **get_common())

@application.route('/admin/add-product', methods=['POST'])
def admin_add_product():
    new_p = Product(name=request.form['name'], price=float(request.form['price']), category=request.form['category'], icon=request.form['icon'])
    db.session.add(new_p)
    db.session.commit()
    flash("Product Added!")
    return redirect(url_for('admin'))

@application.route('/admin/delete-product/<int:pid>')
def admin_delete_product(pid):
    p = Product.query.get(pid)
    if p:
        db.session.delete(p)
        db.session.commit()
    return redirect(url_for('admin'))

@application.route('/add-to-cart/<int:pid>', methods=['POST'])
def add_to_cart(pid):
    if 'cart' not in session: session['cart'] = []
    p = Product.query.get(pid)
    if p:
        cart = session['cart']
        cart.append({'name': p.name, 'price': p.price, 'icon': p.icon})
        session['cart'] = cart
        session.modified = True
    return redirect(url_for('home'))

@application.route('/cart')
def cart():
    items = session.get('cart', [])
    total = sum(i['price'] for i in items)
    return render_template_string(MASTER_HTML, page='cart', items=items, total=total, **get_common())

@application.route('/checkout')
def checkout():
    cart = session.get('cart', [])
    if not cart: return redirect(url_for('home'))
    new_o = Order(customer_name=session.get('user_name', 'Guest'), total=sum(i['price'] for i in cart))
    db.session.add(new_o)
    db.session.commit()
    session.pop('cart', None)
    flash("Order Placed!")
    return redirect(url_for('home'))

@application.route('/login')
def login(): return render_template_string(MASTER_HTML, page='login', **get_common())

@application.route('/auth-login', methods=['POST'])
def auth_login():
    # Simple logic: creates a session for any login for demo purposes
    session['user_id'] = 1
    session['user_name'] = 'Admin'
    return redirect(url_for('home'))

@application.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Health check for AWS Load Balancers
@application.route('/health')
def health(): return "Healthy", 200

if __name__ == '__main__':
    # AWS EB usually runs on port 80 or 8080, but Flask's default 5000 is fine locally
    application.run(host='0.0.0.0', port=5000)
