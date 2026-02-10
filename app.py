from flask import Flask, render_template_string, request, session, redirect, url_for, Response, flash

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

import os



app = Flask(__name__)

app.secret_key = 'fresh_basket_enterprise_edition_v22'



# --- DATABASE CONFIGURATION ---

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

    role = db.Column(db.String(10), default='user') # 'user' or 'admin'



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

    items_json = db.Column(db.Text) # Stores names of items purchased



with app.app_context():

    db.create_all()

    # Seed Products if empty

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



# --- STYLES & UI ---

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

        body {

            background-color: var(--dark-bg); color: var(--text-main);

            margin: 0; font-family: 'Poppins', sans-serif; line-height: 1.6;

        }



        /* NAVIGATION */

        .navbar {

            background: rgba(0,0,0,0.95); backdrop-filter: blur(10px);

            padding: 1rem 5%; display: flex; justify-content: space-between;

            align-items: center; position: sticky; top: 0; z-index: 1000;

            border-bottom: 2px solid var(--primary);

        }

        .nav-links { display: flex; align-items: center; gap: 20px; }

        .nav-links a { color: white; text-decoration: none; font-weight: 500; font-size: 0.9rem; }

        .nav-links a:hover { color: var(--primary); }

        .logo { font-family: 'Cinzel', serif; color: var(--primary); font-size: 1.8rem; text-decoration: none; }



        /* SEARCH BAR */

        .search-form { background: white; border-radius: 25px; padding: 2px 15px; display: flex; align-items: center; }

        .search-form input { border: none; padding: 8px; outline: none; width: 180px; font-family: inherit; }

        .search-form button { background: none; border: none; cursor: pointer; font-size: 1.1rem; }



        /* HERO SLIDER */

        .slider-container { width: 100%; height: 400px; overflow: hidden; position: relative; }

        .slides { display: flex; width: 300%; height: 100%; animation: slideAnim 15s infinite; }

        .slide {

            width: 33.33%; height: 100%; display: flex; flex-direction: column;

            justify-content: center; align-items: center; background-size: cover;

            background-position: center; background-blend-mode: overlay; background-color: rgba(0,0,0,0.4);

        }

        .slide h1 { font-family: 'Cinzel', serif; font-size: 3.5rem; margin: 0; color: white; text-shadow: 2px 2px 10px rgba(0,0,0,0.5); }

        @keyframes slideAnim {

            0%, 30% { transform: translateX(0); }

            33%, 63% { transform: translateX(-33.33%); }

            66%, 96% { transform: translateX(-66.66%); }

            100% { transform: translateX(0); }

        }



        /* CATEGORY STRIP */

        .cat-strip {

            display: flex; justify-content: center; gap: 50px; padding: 40px 5%;

            background: #161e2e; border-bottom: 1px solid #334155;

        }

        .cat-card { text-align: center; color: white; text-decoration: none; width: 100px; }

        .cat-card span {

            font-size: 3rem; display: block; background: var(--card-bg);

            border-radius: 50%; width: 80px; height: 80px; line-height: 80px;

            margin: 0 auto 10px; border: 2px solid transparent;

        }

        .cat-card:hover span { border-color: var(--primary); transform: scale(1.1); }



        /* PRODUCT SECTIONS */

        .section-header {

            display: flex; justify-content: space-between; align-items: flex-end;

            padding: 40px 5% 20px;

        }

        .section-header h2 { margin: 0; font-family: 'Cinzel', serif; border-left: 5px solid var(--primary); padding-left: 15px; }

        .view-all-btn { color: var(--primary); text-decoration: none; font-weight: 600; border-bottom: 1px solid transparent; }

        .view-all-btn:hover { border-color: var(--primary); }



        .product-grid {

            display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));

            gap: 30px; padding: 20px 5% 60px;

        }

        .product-card {

            background: var(--card-bg); border-radius: 20px; padding: 30px;

            text-align: center; border: 1px solid #334155; position: relative;

        }

        .product-card:hover { transform: translateY(-10px); border-color: var(--primary); }

        .product-card .icon { font-size: 4rem; margin-bottom: 15px; display: block; }

        .product-card h3 { margin: 10px 0; font-size: 1.2rem; }

        .product-card .price { font-size: 1.4rem; color: var(--primary); font-weight: 600; margin: 10px 0; }

       

        /* BUTTONS */

        .btn-add {

            background: var(--primary); color: white; border: none; padding: 12px;

            border-radius: 12px; width: 100%; cursor: pointer; font-weight: 600; font-size: 1rem;

        }

        .btn-add:hover { background: var(--primary-hover); }

       

        /* FORMS & CONTAINERS */

        .auth-container {

            max-width: 450px; margin: 80px auto; background: var(--card-bg);

            padding: 40px; border-radius: 25px; border: 1px solid #334155; text-align: center;

        }

        .form-group { text-align: left; margin-bottom: 20px; }

        .form-group label { display: block; margin-bottom: 8px; color: var(--text-muted); }

        .form-group input {

            width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #334155;

            background: var(--dark-bg); color: white; font-size: 1rem;

        }



        /* ADMIN DASHBOARD */

        .admin-layout { display: grid; grid-template-columns: 250px 1fr; min-height: 90vh; }

        .admin-sidebar { background: #000; padding: 30px; border-right: 1px solid #334155; }

        .admin-content { padding: 40px; }

        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }

        .stat-box { background: var(--card-bg); padding: 30px; border-radius: 20px; text-align: center; border: 1px solid var(--primary); }

       

        .order-table { width: 100%; border-collapse: collapse; margin-top: 20px; }

        .order-table th, .order-table td { padding: 15px; text-align: left; border-bottom: 1px solid #334155; }

       

        /* CART */

        .cart-container { max-width: 900px; margin: 50px auto; padding: 0 5%; }

        .cart-item {

            display: flex; justify-content: space-between; align-items: center;

            background: var(--card-bg); padding: 20px; border-radius: 15px; margin-bottom: 15px;

        }



        /* ALERTS */

        .flash-msg {

            padding: 15px; background: var(--primary); color: white;

            text-align: center; position: fixed; top: 80px; width: 100%; z-index: 999;

        }

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

                    <p>Directly from the fields to your doorstep</p>

                </div>

                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1606787366850-de6330128bfc?w=1200')">

                    <h1>Healthy Living</h1>

                    <p>Up to 30% off on all green vegetables</p>

                </div>

                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=1200')">

                    <h1>Fresh Harvest</h1>

                    <p>Seasonal fruits picked at peak ripeness</p>

                </div>

            </div>

        </div>



        <div class="cat-strip">

            <a href="/category/fruits" class="cat-card"><span>🍎</span>Fruits</a>

            <a href="/category/vegetables" class="cat-card"><span>🥦</span>Veggies</a>

            <a href="/category/bakery" class="cat-card"><span>🍞</span>Bakery</a>

            <a href="/category/dairy" class="cat-card"><span>🥛</span>Dairy</a>

        </div>



        <div class="section-header">

            <h2>Featured Fruits</h2>

            <a href="/category/fruits" class="view-all-btn">View All</a>

        </div>

        <div class="product-grid">

            {% for p in fruits %}

            <div class="product-card">

                <span class="icon">{{ p.icon }}</span>

                <h3>{{ p.name }}</h3>

                <p class="price">₹{{ p.price }}</p>

                <form action="/add-to-cart/{{ p.id }}" method="POST">

                    <button class="btn-add">Add to Basket</button>

                </form>

            </div>

            {% endfor %}

        </div>



        <div class="section-header">

            <h2>Daily Essentials</h2>

            <a href="/view-all" class="view-all-btn">Explore All</a>

        </div>

        <div class="product-grid">

            {% for p in essentials %}

            <div class="product-card">

                <span class="icon">{{ p.icon }}</span>

                <h3>{{ p.name }}</h3>

                <p class="price">₹{{ p.price }}</p>

                <form action="/add-to-cart/{{ p.id }}" method="POST">

                    <button class="btn-add">Add to Basket</button>

                </form>

            </div>

            {% endfor %}

        </div>



    {% elif page == 'login' %}

        <div class="auth-container">

            <h1 style="font-family:'Cinzel'">Welcome Back</h1>

            <form action="/auth-login" method="POST">

                <div class="form-group">

                    <label>Email Address</label>

                    <input type="email" name="email" required>

                </div>

                <div class="form-group">

                    <label>Password</label>

                    <input type="password" name="password" required>

                </div>

                <button class="btn-add">Sign In</button>

            </form>

            <p style="margin-top:20px;">New here? <a href="/signup" style="color:var(--primary)">Create Account</a></p>

        </div>



    {% elif page == 'signup' %}

        <div class="auth-container">

            <h1 style="font-family:'Cinzel'">Create Account</h1>

            <form action="/auth-signup" method="POST">

                <div class="form-group">

                    <label>First Name</label>

                    <input type="text" name="fname" required>

                </div>

                <div class="form-group">

                    <label>Email Address</label>

                    <input type="email" name="email" required>

                </div>

                <div class="form-group">

                    <label>Password</label>

                    <input type="password" name="password" required>

                </div>

                <button class="btn-add">Register Now</button>

            </form>

            <p style="margin-top:20px;">Already a member? <a href="/login" style="color:var(--primary)">Login</a></p>

        </div>



    {% elif page == 'cart' %}

        <div class="cart-container">

            <h1 style="font-family:'Cinzel'">Shopping Basket</h1>

            {% for item in items %}

            <div class="cart-item">

                <div style="display:flex; align-items:center; gap:20px;">

                    <span style="font-size:2rem">{{ item.icon }}</span>

                    <div>

                        <h4 style="margin:0">{{ item.name }}</h4>

                        <small style="color:var(--text-muted)">Premium Quality</small>

                    </div>

                </div>

                <div style="font-weight:bold; font-size:1.2rem">₹{{ item.price }}</div>

            </div>

            {% else %}

                <div style="text-align:center; padding:50px;">

                    <h3>Your basket is empty!</h3>

                    <a href="/" class="view-all-btn">Go Shopping</a>

                </div>

            {% endfor %}

           

            {% if items %}

                <div style="text-align:right; margin-top:30px; background:var(--card-bg); padding:30px; border-radius:20px;">

                    <h2 style="margin:0">Total Amount: <span style="color:var(--primary)">₹{{ total }}</span></h2>

                    <p style="color:var(--text-muted)">Inclusive of all taxes</p>

                    <a href="/checkout" class="btn-add" style="display:inline-block; width:250px; text-decoration:none;">Proceed to Checkout</a>

                </div>

            {% endif %}

        </div>



    {% elif page == 'admin_dash' %}

        <div class="admin-layout">

            <div class="admin-sidebar">

                <h3 style="color:var(--primary)">Management</h3>

                <a href="/admin" class="nav-links" style="display:block; margin:20px 0; color:white; text-decoration:none;">Orders</a>

                <a href="/logout" class="nav-links" style="display:block; margin:20px 0; color:var(--danger); text-decoration:none;">Logout</a>

            </div>

            <div class="admin-content">

                <h1 style="font-family:'Cinzel'">Executive Overview</h1>

   

                <div class="stats-grid">

                <div class="stat-box"><small>Total Revenue</small><h2>₹{{ revenue }}</h2></div>

                <div class="stat-box"><small>Total Orders</small><h2>{{ orders|length }}</h2></div>

                <div class="stat-box"><small>Inventory</small><h2>{{ products_count }} Items</h2></div>

            </div>



            <div style="background:var(--card-bg); padding:30px; border-radius:20px; border:1px solid var(--primary); margin-bottom:40px;">

                <h3>Add New Product</h3>

                <form action="/admin/add-product" method="POST" style="display:grid; grid-template-columns: 1fr 1fr 1fr 1fr 150px; gap:10px; align-items:end;">

                <div class="form-group" style="margin:0;">

                    <label>Name</label><input type="text" name="name" required placeholder="e.g. Grapes">

            </div>

            <div class="form-group" style="margin:0;">

                <label>Price</label><input type="number" name="price" required placeholder="100">

            </div>

            <div class="form-group" style="margin:0;">

                <label>Category</label>

                <select name="category" style="width:100%; padding:12px; border-radius:10px; background:var(--dark-bg); color:white; border:1px solid #334155;">

                    <option value="fruits">Fruits</option>

                    <option value="vegetables">Veggies</option>

                    <option value="bakery">Bakery</option>

                    <option value="dairy">Dairy</option>

                </select>

            </div>

            <div class="form-group" style="margin:0;">

                <label>Icon</label><input type="text" name="icon" required placeholder="🍇">

            </div>

            <button class="btn-add" style="margin:0;">Add Item</button>

        </form>

    </div>



    <h3>Inventory Management</h3>

    <table class="order-table" style="margin-bottom:40px;">

        <thead>

            <tr><th>Icon</th><th>Name</th><th>Category</th><th>Price</th><th>Action</th></tr>

        </thead>

        <tbody>

            {% for p in all_products_list %}

            <tr>

                <td>{{ p.icon }}</td>

                <td>{{ p.name }}</td>

                <td>{{ p.category }}</td>

                <td>₹{{ p.price }}</td>

                <td><a href="/admin/delete-product/{{ p.id }}" style="color:var(--danger)">Remove</a></td>

            </tr>

            {% endfor %}

        </tbody>

    </table>



    <h3>Recent Transactions</h3>

    <table class="order-table">

        <thead>

            <tr><th>Order ID</th><th>Customer</th><th>Total</th><th>Date</th><th>Action</th></tr>

        </thead>

        <tbody>

            {% for o in orders %}

            <tr>

                <td>#{{ o.id }}</td>

                <td>{{ o.customer_name }}</td>

                <td>₹{{ o.total }}</td>

                <td>{{ o.date.strftime('%Y-%m-%d') }}</td>

                <td><a href="/del-order/{{ o.id }}" style="color:var(--danger)">Cancel</a></td>

            </tr>

            {% endfor %}

        </tbody>

    </table>

</div>

        </div>



    {% elif page == 'history' %}

        <div class="cart-container">

            <h1 style="font-family:'Cinzel'">Purchase History</h1>

            {% for o in orders %}

            <div class="cart-item" style="border-left:5px solid var(--primary)">

                <div>

                    <h4 style="margin:0">Order #{{ o.id }}</h4>

                    <small>{{ o.date.strftime('%B %d, %Y') }}</small>

                </div>

                <div style="text-align:right">

                    <div style="font-weight:bold; color:var(--primary)">₹{{ o.total }}</div>

                    <a href="/download/{{ o.id }}" style="font-size:0.7rem; color:var(--accent)">Download Receipt</a>

                </div>

            </div>

            {% endfor %}

        </div>



    {% elif page == 'results' %}

        <div class="section-header">

            <h2>{{ title }}</h2>

        </div>

        <div class="product-grid">

            {% for p in items %}

            <div class="product-card">

                <span class="icon">{{ p.icon }}</span>

                <h3>{{ p.name }}</h3>

                <p class="price">₹{{ p.price }}</p>

                <form action="/add-to-cart/{{ p.id }}" method="POST">

                    <button class="btn-add">Add to Basket</button>

                </form>

            </div>

            {% endfor %}

        </div>

    {% endif %}



    <footer style="padding:60px 5%; background:#000; border-top:1px solid #334155; margin-top:100px; text-align:center; color:var(--text-muted)">

        <h2 class="logo">FreshBasket</h2>

        <p>Premium Grocery Delivery Service &copy; 2026</p>

    </footer>

</body>

</html>

"""



# --- CONTEXT HELPER ---

def get_common():

    cart = session.get('cart', [])

    return {'cart_count': len(cart)}



# --- CORE ROUTES ---

@app.route('/')

def home():

    fruits = Product.query.filter_by(category='fruits').limit(4).all()

    essentials = Product.query.limit(4).all()

    return render_template_string(MASTER_HTML, page='home', fruits=fruits, essentials=essentials, **get_common())



@app.route('/category/<cat>')

def category(cat):

    items = Product.query.filter_by(category=cat).all()

    return render_template_string(MASTER_HTML, page='results', items=items, title=cat.capitalize(), **get_common())



@app.route('/search')

def search():

    q = request.args.get('q', '')

    items = Product.query.filter(Product.name.contains(q)).all()

    return render_template_string(MASTER_HTML, page='results', items=items, title=f"Search Results for '{q}'", **get_common())



@app.route('/view-all')

def view_all():

    items = Product.query.all()

    return render_template_string(MASTER_HTML, page='results', items=items, title="All Products", **get_common())



# --- CART SYSTEM ---

@app.route('/add-to-cart/<int:pid>', methods=['POST'])

def add_to_cart(pid):

    if 'cart' not in session: session['cart'] = []

    p = Product.query.get(pid)

    if p:

        cart = session['cart']

        cart.append({'id': p.id, 'name': p.name, 'price': p.price, 'icon': p.icon})

        session['cart'] = cart

        session.modified = True

        flash(f"{p.name} added to basket!")

    return redirect(request.referrer or url_for('home'))



@app.route('/cart')

def cart():

    items = session.get('cart', [])

    total = sum(i['price'] for i in items)

    return render_template_string(MASTER_HTML, page='cart', items=items, total=total, **get_common())



@app.route('/checkout')

def checkout():

    cart = session.get('cart', [])

    if not cart: return redirect(url_for('home'))

   

    total = sum(i['price'] for i in cart)

    item_names = ", ".join([i['name'] for i in cart])

   

    new_o = Order(

        user_id=session.get('user_id'),

        customer_name=session.get('user_name', 'Guest'),

        total=total,

        items_json=item_names

    )

    db.session.add(new_o)

    db.session.commit()

    session.pop('cart', None)

    flash("Order Placed Successfully!")

    return redirect(url_for('orders'))



# --- AUTH SYSTEM ---

@app.route('/login')

def login(): return render_template_string(MASTER_HTML, page='login', **get_common())



@app.route('/signup')

def signup(): return render_template_string(MASTER_HTML, page='signup', **get_common())



@app.route('/auth-signup', methods=['POST'])

def auth_signup():

    email = request.form['email']

    if User.query.filter_by(email=email).first():

        flash("Email already exists!")

        return redirect(url_for('signup'))

   

    hashed_pw = generate_password_hash(request.form['password'])

    new_user = User(first_name=request.form['fname'], email=email, password=hashed_pw)

    db.session.add(new_user)

    db.session.commit()

    flash("Account created! Please login.")

    return redirect(url_for('login'))



@app.route('/auth-login', methods=['POST'])

def auth_login():

    user = User.query.filter_by(email=request.form['email']).first()

    if user and check_password_hash(user.password, request.form['password']):

        session['user_id'] = user.id

        session['user_name'] = user.first_name

        session['role'] = user.role

        return redirect(url_for('home'))

    flash("Invalid credentials!")

    return redirect(url_for('login'))



@app.route('/logout')

def logout():

    session.clear()

    return redirect(url_for('home'))



# --- USER PROFILE ---

@app.route('/orders')

def orders():

    if 'user_id' not in session: return redirect(url_for('login'))

    user_orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.date.desc()).all()

    return render_template_string(MASTER_HTML, page='history', orders=user_orders, **get_common())



@app.route('/download/<int:oid>')

def download(oid):

    o = Order.query.get(oid)

    if not o: return "Not Found"

    receipt = f"FRESHBASKET PREMIUM RECEIPT\n{'='*30}\nOrder ID: #{o.id}\nDate: {o.date}\nCustomer: {o.customer_name}\nItems: {o.items_json}\nTOTAL: Rs.{o.total}\n{'='*30}\nThank you for shopping!"

    return Response(receipt, mimetype="text/plain", headers={"Content-disposition": f"attachment; filename=receipt_{oid}.txt"})



# --- ADMIN SYSTEM ---

@app.route('/admin')

def admin():

    # Hardcoded check for testing: check if user is logged in

    if not session.get('user_id'):

        flash("Please login first")

        return redirect(url_for('login'))

   

    all_orders = Order.query.order_by(Order.date.desc()).all()

    all_products = Product.query.all() # Fetch all products

    revenue = sum(o.total for o in all_orders)

    p_count = len(all_products)

   

    return render_template_string(

        MASTER_HTML,

        page='admin_dash',

        orders=all_orders,

        all_products_list=all_products, # Pass this to HTML

        revenue=revenue,

        products_count=p_count,

        **get_common()

    )



@app.route('/del-order/<int:oid>')

def del_order(oid):

    o = Order.query.get(oid)

    if o:

        db.session.delete(o)

        db.session.commit()

        flash("Order Cancelled")

    return redirect(url_for('admin'))



# --- PRODUCT MANAGEMENT ROUTES ---



@app.route('/admin/add-product', methods=['POST'])

def admin_add_product():

    # Only allow if logged in (simplified check)

    if not session.get('user_id'):

        return redirect(url_for('login'))

       

    name = request.form.get('name')

    price = float(request.form.get('price'))

    category = request.form.get('category')

    icon = request.form.get('icon')

   

    new_p = Product(name=name, price=price, category=category, icon=icon)

    db.session.add(new_p)

    db.session.commit()

    flash(f"Product '{name}' added successfully!")

    return redirect(url_for('admin'))



@app.route('/admin/delete-product/<int:pid>')

def admin_delete_product(pid):

    p = Product.query.get(pid)

    if p:

        db.session.delete(p)

        db.session.commit()

        flash("Product removed from inventory.")

    return redirect(url_for('admin'))



if __name__ == '__main__':

    app.run(debug=True, port=5000)
