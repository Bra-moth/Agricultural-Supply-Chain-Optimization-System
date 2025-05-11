from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length
from extensions import db
from models import User, Crop, Order
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agricultural_scm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB with app
db.init_app(app)

# Create Registration Form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=25)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    role = SelectField('Role', choices=[
        ('farmer', 'Farmer'), 
        ('distributor', 'Distributor'),
        ('retailer', 'Retailer')
    ], validators=[DataRequired()])
    farm_size = StringField('Farm Size (acres)')
    location = StringField('Location', validators=[DataRequired()])

# Context processor for current_user
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            location=form.location.data,
            farm_size=form.farm_size.data if form.role.data == 'farmer' else None
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('Register.html', form=form)

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
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/crop-inventory')
@login_required
@role_required('farmer')
def crop_inventory():
    user = User.query.get(session['user_id'])
    crops = Crop.query.filter_by(farmer_id=user.id).all()
    return render_template('crop_inventory.html', crops=crops)

@app.route('/market-prices')
@login_required
def market_prices():
    prices = {
        'Maize': 150,
        'Wheat': 180,
        'Potatoes': 25
    }
    return render_template('market_prices.html', prices=prices)

@app.route('/orders')
@login_required
def orders():
    user = User.query.get(session['user_id'])
    orders = Order.query.filter_by(user_id=user.id).all()
    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        abort(403)
    return render_template('order_detail.html', order=order)

@app.route('/supply-routes')
@login_required
@role_required('distributor')
def supply_routes():
    # Add your supply routes logic here
    return render_template('supply_routes.html')

@app.route('/farmer-connections')
@login_required
@role_required('distributor')
def farmer_connections():
    # Add your farmer connections logic here
    return render_template('farmer_connections.html')

@app.route('/produce-sourcing')
@login_required
@role_required('retailer')
def produce_sourcing():
    # Add your produce sourcing logic here
    return render_template('produce_sourcing.html')

@app.route('/add-crop', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def add_crop():
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

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)