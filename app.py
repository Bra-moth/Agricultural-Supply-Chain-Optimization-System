from flask import Flask, render_template, redirect, url_for, flash, session, abort, Response, request, jsonify
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import zoneinfo  # Add this import for timezone support
from functools import wraps
import os
import json
import time
from extensions import db, login_manager
from models import User, Crop, Order, Product, RestockOrder, Inventory, Delivery, Cart, CartItem, InventoryItem
from forms import LoginForm, RegistrationForm, CropForm, CreateOrderForm
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
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

    # Get available distributors (not yet connected)
    connected_distributor_ids = [d.id for d in connected_distributors]
    available_distributors = User.query.filter_by(
        role='distributor'
    ).filter(
        ~User.id.in_(connected_distributor_ids) if connected_distributor_ids else True
    ).limit(5).all()

    # Prepare chart data
    # Crop performance data (last 6 crops)
    recent_crops = Crop.query.filter_by(
        farmer_id=current_user.id,
        status='harvested'
    ).order_by(Crop.harvest_date.desc()).limit(6).all()
    
    crop_performance_labels = [crop.name for crop in recent_crops]
    crop_performance_data = [crop.quantity for crop in recent_crops]

    # Revenue data (last 6 months)
    revenue_labels = []
    revenue_data = []
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=i*30)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        monthly_revenue = sum(
            order.total_amount for order in Order.query.filter_by(
                farmer_id=current_user.id,
                status='completed'
            ).filter(
                Order.created_at.between(month_start, month_end)
            ).all()
        )
        
        revenue_labels.append(date.strftime('%b %Y'))
        revenue_data.append(monthly_revenue)

    return render_template('farmer_dashboard.html',
        user=current_user,
        active_crops=active_crops,
        harvest_ready_crops=harvest_ready_crops,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
        market_prices=market_prices,
        connected_distributors=connected_distributors,
        available_distributors=available_distributors,
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

    # Calculate total purchases for this month
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_purchases = db.session.query(func.sum(Order.total_amount)).filter(
        Order.retailer_id == current_user.id,
        Order.status == 'completed',
        Order.completed_at >= start_of_month
    ).scalar() or 0.0

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

    # Get unique categories and suppliers for filters
    categories = db.session.query(Product.category).distinct().all()
    suppliers = User.query.filter_by(role='distributor').all()

    return render_template('retailer_dashboard.html',
        user=current_user,
        active_orders=active_orders,
        total_purchases=total_purchases,
        products=products,
        low_stock_products=low_stock_products,
        recent_orders=recent_orders,
        categories=[c[0] for c in categories],
        suppliers=suppliers
    )

@app.route('/crop-inventory')
@login_required
@role_required('farmer')
def crop_inventory():
    crops = Crop.query.filter_by(farmer_id=current_user.id).all()
    return render_template('crop_inventory.html', crops=crops)

@app.route('/farmer/add-crop', methods=['GET', 'POST'])
@login_required
@role_required('farmer')
def add_crop():
    form = CropForm()
    
    if form.validate_on_submit():
        try:
            # Handle image upload
            image_filename = None
            if form.image.data:
                image = form.image.data
                image_filename = secure_filename(f"{current_user.id}_{int(time.time())}_{image.filename}")
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            # Create new crop
            new_crop = Crop(
                name=form.name.data,
                variety=form.variety.data,
                planting_season=form.planting_season.data,
                harvest_period=form.harvest_period.data,
                yield_per_acre=form.yield_per_acre.data,
                price_per_unit=form.price_per_unit.data,
                description=form.description.data,
                image=image_filename,
                farmer_id=current_user.id,
                status='growing',
                planting_date=datetime.now()
            )
            
            db.session.add(new_crop)
            db.session.commit()
            
            flash('Crop added successfully!', 'success')
            return redirect(url_for('farmer_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the crop. Please try again.', 'danger')
            app.logger.error(f"Error adding crop: {str(e)}")
    
    return render_template('add_crop.html', form=form)

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
    return render_template('market_prices.html', prices=prices)

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
        new_order = Order(
            farmer_id=form.farmer_id.data,
            product_id=form.product_id.data,
            quantity=form.quantity.data,
            distributor_id=current_user.id,
            status='pending'
        )
        db.session.add(new_order)
        db.session.commit()
        flash('Order created successfully!', 'success')
        return redirect(url_for('distributor_dashboard'))
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
    return {'now': datetime.now(zoneinfo.ZoneInfo('Africa/Johannesburg'))}

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
@role_required('farmer')
def crop_detail(crop_id):
    # Get the crop
    crop = Crop.query.get_or_404(crop_id)
    
    # Verify ownership
    if crop.farmer_id != current_user.id:
        abort(403)
    
    # Get current market price for this crop
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
        market_price=market_price
    )

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
@role_required('distributor')
def update_order_status(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        if order.distributor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['pending', 'processing', 'completed', 'cancelled']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        order.status = new_status
        if new_status == 'completed':
            order.completed_at = datetime.now()
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating order status: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/deliveries/<int:delivery_id>/status', methods=['PUT'])
@login_required
@role_required('distributor')
def update_delivery_status(delivery_id):
    try:
        delivery = Delivery.query.get_or_404(delivery_id)
        
        if delivery.distributor_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['scheduled', 'in_transit', 'completed', 'failed']:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        delivery.status = new_status
        if new_status == 'completed':
            delivery.completed_at = datetime.now()
            # Update associated order status
            if delivery.order:
                delivery.order.status = 'completed'
                delivery.order.completed_at = datetime.now()
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating delivery status: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/market-insights/<period>')
@login_required
@role_required('retailer')
def get_market_insights(period):
    try:
        today = datetime.now()
        if period == 'weekly':
            start_date = today - timedelta(days=7)
            labels = [(start_date + timedelta(days=i)).strftime('%a') for i in range(8)]
        elif period == 'monthly':
            start_date = today - timedelta(days=30)
            labels = [(start_date + timedelta(days=i)).strftime('%d %b') for i in range(31)]
        elif period == 'yearly':
            start_date = today - timedelta(days=365)
            labels = [(start_date + timedelta(days=i*30)).strftime('%b') for i in range(12)]
        else:
            return jsonify({'error': 'Invalid period'}), 400

        # Get average prices for the period
        # This is a placeholder - you should implement actual price tracking
        prices = [random.uniform(10, 100) for _ in labels]

        return jsonify({
            'labels': labels,
            'prices': prices
        })

    except Exception as e:
        app.logger.error(f"Error getting market insights: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/cart/add', methods=['POST'])
@login_required
@role_required('retailer')
def add_to_cart():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        if not product_id:
            return jsonify({'success': False, 'message': 'Product ID is required'}), 400

        product = Product.query.get_or_404(product_id)

        if product.quantity < quantity:
            return jsonify({
                'success': False,
                'message': f'Only {product.quantity} units available'
            }), 400

        # Get or create cart
        cart = Cart.query.filter_by(retailer_id=current_user.id, status='active').first()
        if not cart:
            cart = Cart(retailer_id=current_user.id, status='active')
            db.session.add(cart)

        # Add item to cart
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                price_per_unit=product.price_per_unit
            )
            db.session.add(cart_item)

        db.session.commit()

        # Get updated cart count
        cart_count = CartItem.query.filter_by(cart_id=cart.id).count()

        return jsonify({
            'success': True,
            'cart_count': cart_count
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding to cart: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        order = Order.query.get_or_404(order_id)
        
        # Only retailer who placed the order can cancel it
        if order.retailer_id != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Can only cancel pending orders
        if order.status != 'pending':
            return jsonify({'success': False, 'message': 'Only pending orders can be cancelled'}), 400
        
        order.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error cancelling order: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

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

if __name__ == '__main__':
    app.run(debug=True)