from flask import Flask, render_template, redirect, url_for, flash, session, abort, Response, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import zoneinfo  # Add this import for timezone support
from functools import wraps
import os
import json
import time
from extensions import db, login_manager
from models import User, Crop, Order, Product, RestockOrder, Inventory, Delivery, Cart, CartItem, InventoryItem, OrderItem
from forms import LoginForm, RegistrationForm, CropForm, CreateOrderForm, PlaceOrderForm
from sqlalchemy import func
import random

app = Flask(__name__)

# Ensure instance folder exists
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, "agricultural_scm.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production!
app.config['WTF_CSRF_ENABLED'] = True

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extensions
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required  # Add Flask-Login's login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                flash(f'Welcome back, {user.username}!', 'success')
                
                # Redirect to role-specific dashboard
                if user.role == 'farmer':
                    return redirect(url_for('farmer_dashboard'))
                elif user.role == 'distributor':
                    return redirect(url_for('distributor_dashboard'))
                elif user.role == 'retailer':
                    return redirect(url_for('retailer_dashboard'))
                
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')
        except Exception as e:
            app.logger.error(f'Login error: {str(e)}')
            flash('An error occurred during login. Please try again.', 'danger')
            
    return render_template('login.html', form=form)

# Define a default route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check for existing user
            existing_user = User.query.filter((User.username == form.username.data) | 
                                          (User.email == form.email.data)).first()
            if existing_user:
                if existing_user.username == form.username.data:
                    flash('Username already exists. Please choose a different one.', 'danger')
                else:
                    flash('Email already registered. Please use a different one.', 'danger')
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
            
            # Add and commit to database
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please login with your credentials.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Registration error: {str(e)}')
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html', form=form)

@app.route('/farmer/dashboard')
@login_required
@role_required('farmer')
def farmer_dashboard():
    if current_user.role != 'farmer':
        flash('Access denied. You must be a farmer to view this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Get active crops
    active_crops = Crop.query.filter_by(
        farmer_id=current_user.id
    ).filter(
        Crop.status.in_(['growing', 'ready_for_harvest'])
    ).all()

    # Get harvest ready crops
    harvest_ready_crops = [crop for crop in active_crops if crop.status == 'ready_for_harvest']

    # Get pending orders
    pending_orders = Order.query.filter_by(
        farmer_id=current_user.id,
        status='pending'
    ).all()

    # Calculate total revenue for this month
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_revenue = sum(
        order.total_amount for order in Order.query.filter_by(
            farmer_id=current_user.id,
            status='completed'
        ).filter(
            Order.created_at >= start_of_month
        ).all()
    )

    # Get market prices
    market_prices = {
        'Maize': 150.00,
        'Wheat': 180.00,
        'Potatoes': 25.00,
        'Tomatoes': 30.00,
        'Onions': 20.00
    }

    # Get connected distributors
    connected_distributors = User.query.join(
        Order, User.id == Order.distributor_id
    ).filter(
        Order.farmer_id == current_user.id
    ).distinct().all()

    # Add total orders for each distributor
    for distributor in connected_distributors:
        distributor.total_orders = Order.query.filter_by(
            farmer_id=current_user.id,
            distributor_id=distributor.id
        ).count()

    # Prepare crop performance data (last 6 months)
    crop_performance_data = []
    crop_performance_labels = []
    revenue_data = []
    revenue_labels = []

    # Get data for the last 6 months
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=i*30)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Get crops harvested in this month
        monthly_crops = Crop.query.filter_by(
            farmer_id=current_user.id,
            status='harvested'
        ).filter(
            Crop.harvest_date.between(month_start, month_end)
        ).all()
        
        # Calculate total yield and revenue for the month
        monthly_yield = sum(crop.quantity for crop in monthly_crops)
        monthly_revenue = sum(
            order.total_amount for order in Order.query.filter_by(
                farmer_id=current_user.id,
                status='completed'
            ).filter(
                Order.created_at.between(month_start, month_end)
            ).all()
        )
        
        crop_performance_labels.append(date.strftime('%b %Y'))
        crop_performance_data.append(monthly_yield)
        revenue_data.append(monthly_revenue)
        revenue_labels.append(date.strftime('%b %Y'))

    return render_template('farmer_dashboard.html',
        user=current_user,
        active_crops=active_crops,
        harvest_ready_crops=harvest_ready_crops,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
        market_prices=market_prices,
        connected_distributors=connected_distributors,
        crop_performance_labels=crop_performance_labels,
        crop_performance_data=crop_performance_data,
        revenue_labels=revenue_labels,
        revenue_data=revenue_data
    )

@app.route('/distributor/dashboard')
@login_required
@role_required('distributor')
def distributor_dashboard():
    if current_user.role != 'distributor':
        flash('Access denied. You must be a distributor to view this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Get active orders
    active_orders = Order.query.filter(
        Order.distributor_id == current_user.id,
        Order.status.in_(['pending', 'processing'])
    ).all()

    # Calculate total revenue for this month
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.distributor_id == current_user.id,
        Order.status == 'completed',
        Order.completed_at >= start_of_month
    ).scalar() or 0.0

    # Get inventory items
    inventory_items = InventoryItem.query.filter_by(
        distributor_id=current_user.id
    ).all()

    # Get pending deliveries
    pending_deliveries = Delivery.query.filter(
        Delivery.distributor_id == current_user.id,
        Delivery.status.in_(['scheduled', 'in_transit'])
    ).all()

    return render_template('distributor_dashboard.html',
        user=current_user,
        active_orders=active_orders,
        total_revenue=total_revenue,
        inventory_items=inventory_items,
        pending_deliveries=pending_deliveries
    )

@app.route('/retailer/dashboard')
@login_required
@role_required('retailer')
def retailer_dashboard():
    if current_user.role != 'retailer':
        flash('Access denied. You must be a retailer to view this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Get active orders
    active_orders = Order.query.filter(
        Order.retailer_id == current_user.id,
        Order.status.in_(['pending', 'processing'])
    ).all()

    # Calculate total purchases and revenue for this month
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_purchases = db.session.query(func.sum(Order.total_amount)).filter(
        Order.retailer_id == current_user.id,
        Order.status == 'completed',
        Order.completed_at >= start_of_month
    ).scalar() or 0.0

    # Calculate total revenue (assuming a 20% markup)
    total_revenue = total_purchases * 1.2

    # Get available products
    products = Product.query.filter(
        Product.current_stock > 0
    ).all()

    # Get low stock products
    low_stock_products = [p for p in products if p.current_stock <= p.reorder_level]

    # Get recent orders
    recent_orders = Order.query.filter_by(
        retailer_id=current_user.id
    ).order_by(
        Order.created_at.desc()
    ).limit(5).all()

    # Get sales data for the last 6 months
    sales_data = []
    sales_labels = []
    profit_data = []
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=i*30)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        # Calculate total sales and profit for the month
        monthly_sales = db.session.query(func.sum(Order.total_amount)).filter(
            Order.retailer_id == current_user.id,
            Order.status == 'completed',
            Order.completed_at.between(month_start, month_end)
        ).scalar() or 0.0
        
        monthly_profit = monthly_sales * 0.2  # Assuming 20% profit margin
        
        sales_data.append(monthly_sales)
        profit_data.append(monthly_profit)
        sales_labels.append(date.strftime('%b %Y'))

    # Get popular products data
    popular_products = db.session.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.price_per_unit).label('total_revenue')
    ).join(Order).filter(
        Order.retailer_id == current_user.id,
        Order.status == 'completed'
    ).group_by(
        OrderItem.product_id
    ).order_by(
        func.sum(OrderItem.quantity).desc()
    ).limit(5).all()

    # Get product names and prepare chart data
    product_labels = []
    product_quantities = []
    product_revenues = []
    for prod_id, quantity, revenue in popular_products:
        product = Product.query.get(prod_id)
        if product:
            product_labels.append(product.name)
            product_quantities.append(float(quantity))
            product_revenues.append(float(revenue))

    # Calculate year-over-year growth
    last_year_start = datetime.now() - timedelta(days=365)
    last_year_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.retailer_id == current_user.id,
        Order.status == 'completed',
        Order.completed_at >= last_year_start
    ).scalar() or 0.0

    previous_year_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.retailer_id == current_user.id,
        Order.status == 'completed',
        Order.completed_at.between(
            last_year_start - timedelta(days=365),
            last_year_start
        )
    ).scalar() or 0.0

    yoy_growth = ((last_year_sales - previous_year_sales) / previous_year_sales * 100) if previous_year_sales > 0 else 0

    # Get category performance
    category_performance = db.session.query(
        Product.category,
        func.sum(OrderItem.quantity * OrderItem.price_per_unit).label('total_revenue')
    ).join(
        OrderItem, Product.id == OrderItem.product_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        Order.retailer_id == current_user.id,
        Order.status == 'completed',
        Product.category.isnot(None)  # Exclude products without categories
    ).group_by(
        Product.category
    ).order_by(
        func.sum(OrderItem.quantity * OrderItem.price_per_unit).desc()
    ).all()

    category_labels = []
    category_revenues = []
    for category, revenue in category_performance:
        category_labels.append(category)
        category_revenues.append(float(revenue))

    # If no categories found, add a default one
    if not category_labels:
        category_labels = ['No Data']
        category_revenues = [0.0]

    return render_template('retailer_dashboard.html',
        user=current_user,
        active_orders=active_orders,
        total_purchases=total_purchases,
        total_revenue=total_revenue,
        products=products,
        low_stock_products=low_stock_products,
        recent_orders=recent_orders,
        sales_labels=sales_labels,
        sales_data=sales_data,
        profit_data=profit_data,
        product_labels=product_labels,
        product_quantities=product_quantities,
        product_revenues=product_revenues,
        yoy_growth=yoy_growth,
        category_labels=category_labels,
        category_revenues=category_revenues
    )

@app.route('/crop-inventory')
@login_required
@role_required('farmer')
def crop_inventory():
    crops = Crop.query.filter_by(farmer_id=current_user.id).all()
    return render_template('crop_inventory.html', crops=crops)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_crop_image(form_image):
    if form_image and form_image.filename and allowed_file(form_image.filename):
        filename = secure_filename(form_image.filename)
        # Add timestamp to filename to prevent duplicates
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        form_image.save(filepath)
        return filename
    return None

@app.route('/add_crop', methods=['GET', 'POST'])
@login_required
def add_crop():
    if current_user.role != 'farmer':
        flash('Access denied. Only farmers can add crops.', 'danger')
        return redirect(url_for('home'))

    form = CropForm()
    if form.validate_on_submit():
        try:
            # Handle image upload
            image_filename = save_crop_image(form.image.data)
            
            crop = Crop(
                farmer_id=current_user.id,
                name=form.name.data,
                variety=form.variety.data,
                quantity=form.quantity.data,
                unit=form.unit.data,
                planting_date=form.planting_date.data,
                expected_harvest_date=form.expected_harvest_date.data,
                price_per_unit=form.price_per_unit.data,
                description=form.description.data,
                image=image_filename
            )
            
            db.session.add(crop)
            db.session.commit()
            flash('Crop added successfully!', 'success')
            return redirect(url_for('crop_inventory'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding crop: {str(e)}', 'danger')
            
    return render_template('add_crop.html', form=form)

@app.route('/edit_crop/<int:crop_id>', methods=['GET', 'POST'])
@login_required
def edit_crop(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    
    # Verify ownership
    if crop.farmer_id != current_user.id:
        flash('You can only edit your own crops.', 'danger')
        return redirect(url_for('crop_inventory'))
        
    form = CropForm(obj=crop)
    
    if form.validate_on_submit():
        try:
            # Handle image upload
            if form.image.data:
                # Delete old image if it exists
                if crop.image:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], crop.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Save new image
                image_filename = save_crop_image(form.image.data)
                crop.image = image_filename
            
            # Update other fields
            form.populate_obj(crop)
            
            db.session.commit()
            flash('Crop updated successfully!', 'success')
            return redirect(url_for('crop_detail', crop_id=crop.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating crop: {str(e)}', 'danger')
    
    return render_template('edit_crop.html', form=form, crop=crop)

# Add image_url property to Crop model
@property
def image_url(self):
    if self.image:
        return url_for('static', filename=f'uploads/{self.image}')
    return url_for('static', filename='images/default-crop.png')  # Provide a default image

Crop.image_url = image_url

@app.route('/orders')
@login_required
def orders():
    if current_user.role == 'farmer':
        orders = Order.query.filter_by(farmer_id=current_user.id).all()
    else:
        orders = Order.query.filter_by(distributor_id=current_user.id).all()
    return render_template('orders.html', orders=orders)

@app.route('/market-prices')  # Note the dash (-) not underscore (_)
@login_required
def market_prices():
    prices = {
        'Maize': 150,
        'Wheat': 180,
        'Potatoes': 25
    }
    return render_template('market_prices.html', prices=prices, datetime=datetime)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.farmer_id != current_user.id and order.distributor_id != current_user.id:
        abort(403)
    return render_template('order_detail.html', order=order)

# Distributor Routes
@app.route('/distributor/process_order/<int:order_id>', methods=['POST'])
@login_required
@role_required('distributor')
def process_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.distributor_id != current_user.id:
        abort(403)
    order.status = 'processing'
    db.session.commit()
    flash('Order is being processed', 'success')
    return redirect(url_for('distributor_dashboard'))

@app.route('/distributor/track_order/<int:order_id>')
@login_required
@role_required('distributor')
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.distributor_id != current_user.id:
        abort(403)
    return render_template('track_order.html', order=order)

@app.route('/distributor/reorder/<int:product_id>', methods=['POST'])
@login_required
@role_required('distributor')
def reorder_product(product_id):
    product = Product.query.get_or_404(product_id)
    new_order = RestockOrder(
        product_id=product.id,
        quantity=product.reorder_level,
        distributor_id=current_user.id
    )
    db.session.add(new_order)
    db.session.commit()
    flash(f'Restock order placed for {product.name}', 'success')
    return redirect(url_for('distributor_dashboard'))

@app.route('/distributor/create_order', methods=['GET', 'POST'])
@login_required
@role_required('distributor')
def create_order():
    form = CreateOrderForm()
    if form.validate_on_submit():
        try:
            # Get the product to calculate total amount
            product = Product.query.get_or_404(form.product_id.data)
            if not product:
                flash('Selected product not found.', 'danger')
                return render_template('create_order.html', form=form)

            # Validate quantity is available
            if product.current_stock < form.quantity.data:
                flash(f'Only {product.current_stock} {product.unit} available.', 'danger')
                return render_template('create_order.html', form=form)

            # Calculate total amount
            total_amount = form.quantity.data * product.price_per_unit

            # Create new order
            new_order = Order(
                farmer_id=form.farmer_id.data,
                distributor_id=current_user.id,
                retailer_id=None,  # This will be set when a retailer claims the order
                status='pending',
                total_amount=total_amount,
                created_at=datetime.now()
            )
            db.session.add(new_order)
            db.session.flush()  # This gets us the order ID

            # Create order item
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=form.product_id.data,
                quantity=form.quantity.data,
                price_per_unit=product.price_per_unit
            )
            db.session.add(order_item)

            # Update product stock
            product.current_stock -= form.quantity.data
            
            db.session.commit()
            flash('Order created successfully!', 'success')
            return redirect(url_for('distributor_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating order: {str(e)}')
            flash('An error occurred while creating the order. Please try again.', 'danger')
            
    return render_template('create_order.html', form=form)

@app.route('/order_updates')
@login_required
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
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

# Context processors
@app.context_processor
def inject_now():
    try:
        return {'now': datetime.now(zoneinfo.ZoneInfo('Africa/Johannesburg'))}
    except zoneinfo.ZoneInfoNotFoundError:
        # Fallback to UTC if Africa/Johannesburg timezone is not available
        return {'now': datetime.now(zoneinfo.ZoneInfo('UTC'))}

# API Endpoints for Dashboard Functionality
@app.route('/api/products/<int:product_id>')
@login_required
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'price_per_unit': product.price_per_unit,
        'current_stock': product.current_stock,
        'unit': product.unit
    })

@app.route('/api/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.get_json()
    try:
        # Create new order
        for item in data['items']:
            order = Order(
                product_id=item['id'],
                retailer_id=current_user.id,
                quantity=item['quantity'],
                status='pending',
                total_price=item['quantity'] * item['price_per_unit']
            )
            db.session.add(order)
            
            # Update product stock
            product = Product.query.get(item['id'])
            product.current_stock -= item['quantity']
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# Farmer API Endpoints
@app.route('/api/harvest_crop/<int:crop_id>', methods=['POST'])
@login_required
def harvest_crop(crop_id):
    if current_user.role != 'farmer':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    try:
        crop = Crop.query.get_or_404(crop_id)
        
        # Verify crop belongs to the current farmer
        if crop.farmer_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            
        # Update crop status
        crop.status = 'harvested'
        crop.harvest_date = datetime.now()
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/crop/<int:crop_id>')
@login_required
def crop_detail(crop_id):
    # Get the crop
    crop = Crop.query.get_or_404(crop_id)
    
    # For farmers, ensure they own the crop
    if current_user.role == 'farmer' and crop.farmer_id != current_user.id:
        flash('You do not have permission to view this crop.', 'danger')
        return redirect(url_for('crop_inventory'))
    
    # For distributors and retailers, only allow viewing ready_for_harvest crops
    if current_user.role in ['distributor', 'retailer'] and crop.status != 'ready_for_harvest':
        flash('This crop is not available for viewing.', 'danger')
        return redirect(url_for('available_crops'))
    
    # Get current market price (mock data for now)
    market_prices = {
        'Maize': 150.00,
        'Wheat': 180.00,
        'Potatoes': 25.00,
        'Tomatoes': 30.00,
        'Onions': 20.00
    }
    market_price = market_prices.get(crop.name, 0.00)
    
    return render_template('crop_detail.html',
                         crop=crop,
                         market_price=market_price)

@app.route('/order-history')
@login_required
def order_history():
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)

        # Base query
        query = Order.query

        # Apply role-specific filters
        if current_user.role == 'retailer':
            query = query.filter_by(retailer_id=current_user.id)
        elif current_user.role == 'distributor':
            query = query.filter_by(distributor_id=current_user.id)
        else:
            flash('Access denied. Invalid user role.', 'danger')
            return redirect(url_for('dashboard'))

        # Apply date filters
        if start_date:
            query = query.filter(Order.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Order.created_at <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))

        # Apply price filters
        if min_price is not None:
            query = query.filter(Order.total_amount >= min_price)
        if max_price is not None:
            query = query.filter(Order.total_amount <= max_price)

        # Get orders sorted by date
        orders = query.order_by(Order.created_at.desc()).all()

        return render_template('order_history.html',
            user=current_user,
            orders=orders
        )

    except Exception as e:
        app.logger.error(f"Error in order history: {str(e)}")
        flash('An error occurred while loading order history.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/inventory-management')
@login_required
@role_required('distributor')
def inventory_management():
    try:
        inventory_items = InventoryItem.query.filter_by(
            distributor_id=current_user.id
        ).order_by(
            InventoryItem.category,
            InventoryItem.name
        ).all()

        return render_template('inventory_management.html',
            user=current_user,
            inventory_items=inventory_items
        )

    except Exception as e:
        app.logger.error(f"Error in inventory management: {str(e)}")
        flash('An error occurred while loading inventory.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/api/inventory/add', methods=['POST'])
@login_required
@role_required('distributor')
def add_inventory_item():
    try:
        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                image_filename = secure_filename(f"{current_user.id}_{int(time.time())}_{image.filename}")
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Create new inventory item
        new_item = InventoryItem(
            distributor_id=current_user.id,
            name=request.form['name'],
            category=request.form['category'],
            quantity=float(request.form['quantity']),
            unit=request.form['unit'],
            min_quantity=float(request.form['min_quantity']),
            price_per_unit=float(request.form['price_per_unit']),
            description=request.form.get('description', ''),
            image=image_filename
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding inventory item: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/inventory/<int:item_id>', methods=['GET'])
@login_required
@role_required('distributor')
def get_inventory_item(item_id):
    try:
        item = InventoryItem.query.get_or_404(item_id)
        
        if item.distributor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'product': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'quantity': item.quantity,
                'unit': item.unit,
                'min_quantity': item.min_quantity,
                'price_per_unit': item.price_per_unit,
                'description': item.description,
                'image': item.image
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting inventory item: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/inventory/<int:item_id>/stock', methods=['PUT'])
@login_required
@role_required('distributor')
def update_inventory_stock(item_id):
    try:
        item = InventoryItem.query.get_or_404(item_id)
        
        if item.distributor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        adjustment_type = data.get('adjustment_type')
        quantity = float(data.get('quantity', 0))
        
        if adjustment_type == 'add':
            item.quantity += quantity
        elif adjustment_type == 'remove':
            if item.quantity < quantity:
                return jsonify({
                    'success': False,
                    'message': f'Cannot remove {quantity} {item.unit}. Only {item.quantity} {item.unit} available.'
                }), 400
            item.quantity -= quantity
        else:
            return jsonify({'success': False, 'message': 'Invalid adjustment type'}), 400
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating inventory stock: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
@login_required
@role_required('distributor')
def delete_inventory_item(item_id):
    try:
        item = InventoryItem.query.get_or_404(item_id)
        
        if item.distributor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Delete associated image if exists
        if item.image:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting inventory item: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/inventory/edit/<int:item_id>')
@login_required
@role_required('distributor')
def edit_inventory_item(item_id):
    try:
        item = InventoryItem.query.get_or_404(item_id)
        
        if item.distributor_id != current_user.id:
            flash('Access denied. You can only edit your own inventory items.', 'danger')
            return redirect(url_for('inventory_management'))
        
        return render_template('edit_inventory_item.html',
            user=current_user,
            item=item
        )
        
    except Exception as e:
        app.logger.error(f"Error loading inventory item edit page: {str(e)}")
        flash('An error occurred while loading the item.', 'danger')
        return redirect(url_for('inventory_management'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'farmer':
        return redirect(url_for('farmer_dashboard'))
    elif current_user.role == 'distributor':
        return redirect(url_for('distributor_dashboard'))
    elif current_user.role == 'retailer':
        return redirect(url_for('retailer_dashboard'))
    else:
        flash('Invalid user role.', 'danger')
        return redirect(url_for('home'))

@app.route('/available_crops')
@login_required
def available_crops():
    # For distributors and retailers, show all ready-for-harvest crops
    if current_user.role in ['distributor', 'retailer']:
        crops = Crop.query.filter_by(status='ready_for_harvest').all()
        return render_template('available_crops.html', crops=crops)
    else:
        flash('Access denied. This page is only for distributors and retailers.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/place_order/<int:crop_id>', methods=['GET', 'POST'])
@login_required
@role_required('retailer')
def place_order(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    
    # Ensure crop is ready for harvest
    if crop.status != 'ready_for_harvest':
        flash('This crop is not available for ordering.', 'danger')
        return redirect(url_for('available_crops'))
    
    form = PlaceOrderForm()
    
    if form.validate_on_submit():
        try:
            # Validate quantity is available
            if form.quantity.data > crop.quantity:
                flash(f'Only {crop.quantity} {crop.unit} available.', 'danger')
                return render_template('place_order.html', form=form, crop=crop)
            
            # Create new order
            order = Order(
                farmer_id=crop.farmer_id,
                retailer_id=current_user.id,
                status='pending',
                total_amount=form.quantity.data * crop.price_per_unit,
                notes=form.notes.data
            )
            db.session.add(order)
            db.session.flush()  # Get the order ID
            
            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                crop_id=crop.id,
                quantity=form.quantity.data,
                price_per_unit=crop.price_per_unit
            )
            db.session.add(order_item)
            
            # Update crop quantity
            crop.quantity -= form.quantity.data
            
            db.session.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('orders'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error placing order: {str(e)}')
            flash('An error occurred while placing the order. Please try again.', 'danger')
    
    return render_template('place_order.html', form=form, crop=crop)

@app.route('/api/mark_ready_for_harvest/<int:crop_id>', methods=['POST'])
@login_required
def mark_ready_for_harvest(crop_id):
    if current_user.role != 'farmer':
        return jsonify({'success': False, 'error': 'Only farmers can mark crops as ready for harvest'}), 403
    
    crop = Crop.query.get_or_404(crop_id)
    
    # Check if the crop belongs to the current farmer
    if crop.farmer_id != current_user.id:
        return jsonify({'success': False, 'error': 'You can only mark your own crops as ready for harvest'}), 403
    
    # Check if the crop is in the correct state
    if crop.status != 'growing':
        return jsonify({'success': False, 'error': 'This crop cannot be marked as ready for harvest'}), 400
    
    try:
        crop.status = 'ready_for_harvest'
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)