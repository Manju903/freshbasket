from flask import Flask, render_template_string, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'fresh_basket_v9_db_master'
app.config['SQLALCHEMY_DATABASE_SETTING'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# --- PRODUCT DATA ---
ALL_PRODUCTS = {
    'apple': {'name': 'Royal Gala Apple', 'price': 180, 'icon': '🍎', 'cat': 'fruits'},
    'mango': {'name': 'Alphonso Mango', 'price': 450, 'icon': '🥭', 'cat': 'fruits'},
    'strawberry': {'name': 'Organic Strawberry', 'price': 150, 'icon': '🍓', 'cat': 'fruits'},
    'carrot': {'name': 'Organic Carrots', 'price': 60, 'icon': '🥕', 'cat': 'vegetables'},
    'mushroom': {'name': 'Wild Mushroom', 'price': 120, 'icon': '🍄', 'cat': 'vegetables'},
    'bread': {'name': 'Whole Wheat Bread', 'price': 45, 'icon': '🍞', 'cat': 'bakery'},
    'milk': {'name': 'Fresh Farm Milk', 'price': 30, 'icon': '🥛', 'cat': 'dairy'}
}

ORDERS = [{'id': 1001, 'name': 'Rahul Kumar', 'total': 540}]

# --- HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>FreshBasket | Premium Store</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #22c55e; --dark-bg: #0f172a; --card-bg: #1e293b; --text: #f8fafc; --royal-font: 'Cinzel', serif; }
        body { background-color: var(--dark-bg); color: var(--text); margin: 0; font-family: 'Poppins', sans-serif; overflow-x: hidden; }
        
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 15px 5%; background: #000; position: sticky; top: 0; z-index: 1000; border-bottom: 2px solid var(--primary); }
        .nav-left { display: flex; align-items: center; gap: 20px; }
        .nav-btn { color: white; text-decoration: none; font-weight: 600; }
        .royal-logo { font-family: var(--royal-font); color: var(--primary); font-size: 2rem; text-decoration: none; }
        .search-container { display: flex; background: white; border-radius: 20px; padding: 2px 10px; }
        .search-container input { border: none; padding: 8px; outline: none; border-radius: 20px; width: 120px; }

        /* SLIDER */
        .slider-wrapper { width: 100%; height: 280px; overflow: hidden; position: relative; }
        .slides { display: flex; width: 300%; height: 100%; animation: slideMove 10s infinite; }
        .slide { width: 33.33%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background-size: cover; background-position: center; background-blend-mode: overlay; background-color: rgba(0,0,0,0.5); }
        @keyframes slideMove { 0%, 30% { transform: translateX(0); } 33%, 63% { transform: translateX(-33.33%); } 66%, 96% { transform: translateX(-66.66%); } 100% { transform: translateX(0); } }

        .category-strip { display: flex; justify-content: center; gap: 40px; padding: 20px; background: #161e2e; }
        .cat-item { text-align: center; color: white; text-decoration: none; font-size: 0.9rem; }
        
        .section-head { display: flex; justify-content: space-between; align-items: center; padding: 20px 5%; }
        .view-all-btn { border: 1px solid var(--primary); color: var(--primary); padding: 5px 15px; border-radius: 5px; text-decoration: none; font-size: 0.8rem; }
        
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 20px; padding: 0 5% 40px 5%; }
        .product-card { background: var(--card-bg); padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #334155; position: relative; }
        .add-btn { background: var(--primary); color: white; border: none; width: 35px; height: 35px; border-radius: 50%; cursor: pointer; position: absolute; bottom: 15px; right: 15px; }

        .form-container { max-width: 400px; margin: 50px auto; background: var(--card-bg); padding: 30px; border-radius: 15px; border: 1px solid var(--primary); }
        .form-container input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: none; }
        .primary-btn { width: 100%; background: var(--primary); color: white; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="nav-left">
            <a href="/" class="nav-btn">Home</a>
            <div class="search-container"><input type="text" placeholder="Search..."><button>🔍</button></div>
            <a href="/account" class="nav-btn">👤 {% if user_name %}{{ user_name }}{% endif %}</a>
            <a href="/cart" class="nav-btn">🛒 <span style="color:var(--primary)">{{ cart_count }}</span></a>
            <a href="/admin" class="nav-btn" style="color:var(--primary); font-size:0.7rem; border:1px solid var(--primary); padding:2px 5px; border-radius:4px;">ADMIN</a>
        </div>
        <div class="nav-right"><a href="/" class="royal-logo">FreshBasket</a></div>
    </nav>

    {% if page == 'home' %}
        <section class="category-strip">
            <a href="/view-all/fruits" class="cat-item">🍎<br>Fruits</a>
            <a href="/view-all/vegetables" class="cat-item">🥦<br>Veggies</a>
            <a href="/view-all/bakery" class="cat-item">🍞<br>Bakery</a>
            <a href="/view-all/dairy" class="cat-item">🥛<br>Dairy</a>
        </section>

        <div class="slider-wrapper">
            <div class="slides">
                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1542838132-92c53300491e?w=800')"><h1>Premium Organic Produce</h1></div>
                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1606787366850-de6330128bfc?w=800')"><h1>20% Off First Order</h1></div>
                <div class="slide" style="background-image: url('https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=800')"><h1>Farm to Table Daily</h1></div>
            </div>
        </div>

        <div class="section-head"><h2>New Arrivals</h2><a href="/view-all/all" class="view-all-btn">View All</a></div>
        <div class="product-grid">
            {% for id in ['strawberry', 'mushroom', 'bread'] %}
            <div class="product-card">
                <div style="font-size:3rem">{{ all_prods[id].icon }}</div>
                <h4>{{ all_prods[id].name }}</h4>
                <span style="color:var(--primary)">₹{{ all_prods[id].price }}</span>
                <form action="/add-to-cart/{{ id }}" method="POST"><button class="add-btn">+</button></form>
            </div>
            {% endfor %}
        </div>

        <div class="section-head"><h2>Fresh Fruits</h2><a href="/view-all/fruits" class="view-all-btn">View All</a></div>
        <div class="product-grid">
            {% for id, item in all_prods.items() if item.cat == 'fruits' %}
            <div class="product-card">
                <div style="font-size:3rem">{{ item.icon }}</div>
                <h4>{{ item.name }}</h4>
                <span style="color:var(--primary)">₹{{ item.price }}</span>
                <form action="/add-to-cart/{{ id }}" method="POST"><button class="add-btn">+</button></form>
            </div>
            {% endfor %}
        </div>

    {% elif page == 'account' %}
        <div class="form-container">
            <h2>Login</h2>
            <form action="/login" method="POST">
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button class="primary-btn">Login</button>
            </form>
            <p style="text-align:center; margin-top:20px;">New here? <a href="/signup" style="color:var(--primary)">Create account</a></p>
        </div>

    {% elif page == 'signup' %}
        <div class="form-container">
            <h2>Register</h2>
            <form action="/register" method="POST">
                <input type="text" name="fname" placeholder="First Name" required>
                <input type="text" name="lname" placeholder="Last Name" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="password" name="password" placeholder="Password" required>
                <button class="primary-btn">Sign Up</button>
            </form>
        </div>
    {% endif %}
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def home():
    user_name = session.get('user_name')
    return render_template_string(HTML_TEMPLATE, page='home', all_prods=ALL_PRODUCTS, cart_count=len(session.get('cart', [])), user_name=user_name)

@app.route('/register', methods=['POST'])
def register():
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')
    pwd = request.form.get('password')
    
    if User.query.filter_by(email=email).first():
        return "Email already exists!"
    
    new_user = User(first_name=fname, last_name=lname, email=email, password=generate_password_hash(pwd))
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('account'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    pwd = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, pwd):
        session['user_id'] = user.id
        session['user_name'] = user.first_name
        return redirect(url_for('home'))
    return "Invalid Credentials"

@app.route('/account')
def account():
    return render_template_string(HTML_TEMPLATE, page='account', cart_count=len(session.get('cart', [])))

@app.route('/signup')
def signup():
    return render_template_string(HTML_TEMPLATE, page='signup', cart_count=len(session.get('cart', [])))

@app.route('/view-all/<category>')
def view_all(category):
    filtered = ALL_PRODUCTS if category in ['all', 'new'] else {k: v for k, v in ALL_PRODUCTS.items() if v.get('cat') == category}
    return render_template_string(HTML_TEMPLATE, page='view_all', filtered=filtered, title=category.capitalize(), cart_count=len(session.get('cart', [])))

@app.route('/add-to-cart/<prod_id>', methods=['POST'])
def add_to_cart(prod_id):
    if 'cart' not in session: session['cart'] = []
    product = ALL_PRODUCTS.get(prod_id)
    if product:
        cart_list = session['cart']
        cart_list.append(product)
        session['cart'] = cart_list
        session.modified = True
    return redirect(request.referrer or url_for('home'))

@app.route('/admin')
def admin():
    return render_template_string(HTML_TEMPLATE, page='admin', orders_list=ORDERS, cart_count=len(session.get('cart', [])))

if __name__ == '__main__':
    app.run(debug=True)