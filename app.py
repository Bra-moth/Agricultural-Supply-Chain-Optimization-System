from flask import Flask, render_template, redirect, url_for, flash, session, abort, Response
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf import CSRFProtect
# Removed unused imports from werkzeug.security
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os
import json
import time
from extensions import db, login_manager
from models import db, User, Crop, Order, Product, RestockOrder
from forms import LoginForm, RegistrationForm, CropForm, CreateOrderForm

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agricultural_scm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['WTF_CSRF_ENABLED'] = True

csrf = CSRFProtect(app)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'  # this should be after the `login_manager` is instantiated
login_manager.init_app(app)

# Define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Assuming User has an 'id' field

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # Use Flask-Login's login_user function
            login_user(user)  # This will manage the session automatically

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to the dashboard page
        flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

# Define a default route
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)

# Only run this once to create the database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


# Define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Assuming User has an 'id' field


# Context processors
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}

@app.context_processor
def inject_now():
    return {'now': datetime.now(datetime.timezone.utc)}

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            location=form.location.data,
            farm_size=form.farm_size.data if form.role.data == 'farmer' else None
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            app.logger.error(f'Registration error: {str(e)}')

    return render_template('Register.html', form=form)




@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user  # Use Flask-Login's current_user to get the logged-in user

    if user.role == 'farmer':
        crops = Crop.query.filter_by(crop_farmer_id=user.id).all()  # Updated to crop_farmer_id
        orders = Order.query.filter_by(order_farmer_id=user.id).all()  # Updated to order_farmer_id
        return render_template('farmer_dashboard.html', 
                            user=user,
                            crops=crops,
                            orders=orders)
    elif user.role == 'distributor':
        return render_template('distributor_dashboard.html', user=user)
    elif user.role == 'retailer':
        return render_template('retailer_dashboard.html', user=user)
    
    return render_template('dashboard.html', user=user)


@app.route('/crop-inventory')
@login_required
@role_required('farmer')
def crop_inventory():
    user = User.query.get(session['user_id'])
    crops = Crop.query.filter_by(crop_farmer_id=user.id).all()  # Updated to crop_farmer_id
    return render_template('crop_inventory.html', crops=crops)



@app.route('/add-crop', methods=['GET', 'POST'])
@login_required
def add_crop():
    form = CropForm()
    if form.validate_on_submit():
        # Process the file upload
        if form.image.data:
            # Secure the filename and save the file
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(filepath)

            # Create a new Crop instance with the uploaded image's path
            new_crop = Crop(
                name=form.name.data,
                variety=form.variety.data,
                planting_season=form.planting_season.data,
                harvest_period=form.harvest_period.data,
                yield_per_acre=form.yield_per_acre.data,
                price_per_unit=form.price_per_unit.data,
                description=form.description.data,
                image_path=filepath  # Save the path to the database
            )

            db.session.add(new_crop)
            try:
                db.session.commit()
                flash('Crop added successfully!', 'success')
                return redirect(url_for('crop_inventory'))
            except Exception as e:
                db.session.rollback()
                flash('Failed to add crop. Please try again.', 'danger')
                app.logger.error(f'Error: {str(e)}')

    return render_template('add_crop.html', form=form)

@app.route('/orders')
@login_required
def orders():
    user = User.query.get(session['user_id'])
    if user.role == 'farmer':
        orders = Order.query.filter_by(order_farmer_id=user.id).all()  # Updated to order_farmer_id
    else:
        orders = Order.query.filter_by(buyer_id=user.id).all()
    return render_template('orders.html', orders=orders)

@app.route('/market-prices')  # Note the dash (-) not underscore (_)
@login_required
def market_prices():
    prices = {
        'Maize': 150,
        'Wheat': 180,
        'Potatoes': 25
    }
    return render_template('market_prices.html', prices=prices)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    user = User.query.get(session['user_id'])
    
    # Check if user is either the farmer or buyer of the order
    if order.order_farmer_id != user.id and order.buyer_id != user.id:  # Updated to order_farmer_id
        abort(403)
    
    return render_template('order_detail.html', order=order)

# Other routes remain the same...

# Distributor Routes
@app.route('/distributor/process_order/<order_id>', methods=['POST'])
@login_required
def process_order(order_id):
    # Logic to process order
    order = Order.query.get_or_404(order_id)
    order.status = 'processing'
    db.session.commit()
    flash('Order is being processed', 'success')
    return redirect(url_for('distributor_dashboard'))

@app.route('/distributor/track_order/<order_id>')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('track_order.html', order=order)

@app.route('/distributor/reorder/<product_id>', methods=['POST'])
@login_required
def reorder_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Add to restock queue
    new_order = RestockOrder(
        product_id=product.id,
        quantity=product.reorder_quantity,
        distributor_id=current_user.id
    )
    db.session.add(new_order)
    db.session.commit()
    flash(f'Restock order placed for {product.name}', 'success')
    return redirect(url_for('distributor_dashboard'))

@app.route('/distributor/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    form = CreateOrderForm()
    if form.validate_on_submit():
        # Process form data
        new_order = Order(
            farmer_id=form.farmer_id.data,
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            distributor_id=current_user.id
        )
        db.session.add(new_order)
        db.session.commit()
        flash('Order created successfully!', 'success')
        return redirect(url_for('distributor_dashboard'))
    return render_template('create_order.html', form=form)

@app.route('/order_updates')
def order_updates():
    def event_stream():
        while True:
            # Check for new updates
            # This should come from your database/queue in real implementation
            yield f"data: {json.dumps({'type': 'order_update', 'order_id': 1001, 'status': 'processing'})}\n\n"
            time.sleep(5)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/logout')
@login_required
def logout():
    logout_user()  # Using Flask-Login's logout_user() function
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers remain the same...
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)