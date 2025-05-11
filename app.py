from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from extensions import db
from models import User, Crop, Order

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agricultural_scm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB with app
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        location = request.form['location']
        farm_size = request.form.get('farm_size', '')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(
            username=username,
            email=email,
            role=role,
            location=location,
            farm_size=farm_size if role == 'farmer' else None
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/crop-inventory')
def crop_inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    crops = Crop.query.filter_by(farmer_id=user.id).all()
    return render_template('crop_inventory.html', crops=crops)

@app.route('/market-prices')
def market_prices():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Sample data - replace with real API integration
    prices = {
        'Maize': 150,
        'Wheat': 180,
        'Potatoes': 25
    }
    return render_template('market_prices.html', prices=prices)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).all()
    return render_template('orders.html', orders=orders)

@app.route('/add-crop', methods=['GET', 'POST'])
def add_crop():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        crop_type = request.form['crop_type']
        quantity = request.form['quantity']
        planting_date = datetime.strptime(request.form['planting_date'], '%Y-%m-%d')
        
        new_crop = Crop(
            crop_type=crop_type,
            quantity=quantity,
            planting_date=planting_date,
            farmer_id=user.id
        )
        db.session.add(new_crop)
        db.session.commit()
        flash('Crop added successfully!', 'success')
        return redirect(url_for('crop_inventory'))
    
    return render_template('add_crop.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)