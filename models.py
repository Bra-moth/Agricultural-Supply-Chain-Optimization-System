from flask_login import UserMixin
from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SelectField, FloatField, TextAreaField, FileField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email, ValidationError, EqualTo
from flask_wtf import FlaskForm
from flask import url_for

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='farmer')
    location = db.Column(db.String(100))
    farm_size = db.Column(db.String(50))
    
    # Relationships
    crops = db.relationship('Crop', backref='farmer', lazy=True)
    restock_orders = db.relationship('RestockOrder', backref='distributor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Crop(db.Model):
    __tablename__ = 'crops'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100))
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default='growing')  # Options: growing, ready_for_harvest, harvested
    expected_harvest_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    planting_date = db.Column(db.DateTime, nullable=False)
    harvest_date = db.Column(db.DateTime)
    planting_season = db.Column(db.String(50))  # Store the planting season
    harvest_period = db.Column(db.Integer)  # Store the harvest period in days
    yield_per_acre = db.Column(db.Float)  # Store the expected yield per acre
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def image_url(self):
        if self.image:
            return url_for('static', filename=f'uploads/{self.image}')
        return url_for('static', filename='images/default-crop.jpg')

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), default='available')  # available, reserved, sold
    price_per_unit = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farmer = db.relationship('User', backref=db.backref('inventory_items', lazy=True))

class CropForm(FlaskForm):
    name = StringField('Crop Name', validators=[DataRequired()])
    variety = StringField('Variety', validators=[Optional()])
    planting_season = SelectField('Planting Season', choices=[
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'), 
        ('winter', 'Winter')
    ], validators=[DataRequired()])
    harvest_period = StringField('Harvest Period (days)', validators=[Optional()])
    yield_per_acre = FloatField('Yield per Acre', validators=[Optional()])
    price_per_unit = FloatField('Price per Unit', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    image = FileField('Crop Image', validators=[Optional()])

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    unit = db.Column(db.String(20))  # kg, lb, etc.
    current_stock = db.Column(db.Float, default=0)
    reorder_level = db.Column(db.Float, default=10)
    price_per_unit = db.Column(db.Float)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', name='fk_product_supplier'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = db.relationship('Supplier', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return f'<Product {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Can be null initially
    parent_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # For linking farmer orders to main order
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref=db.backref('orders_as_farmer', lazy=True))
    retailer = db.relationship('User', foreign_keys=[retailer_id], backref=db.backref('orders_as_retailer', lazy=True))
    distributor = db.relationship('User', foreign_keys=[distributor_id], backref=db.backref('orders_as_distributor', lazy=True))
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    parent_order = db.relationship('Order', remote_side=[id], backref=db.backref('child_orders', lazy=True))

    @property
    def status_color(self):
        status_colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'secondary')

class RestockOrder(db.Model):
    __tablename__ = 'restock_orders'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='requested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='restock_orders')

class Supplier(db.Model):
    __tablename__ = 'suppliers'  # Fixed tablename to be plural
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, completed, abandoned
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    retailer = db.relationship('User', backref=db.backref('carts', lazy=True))
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

    @property
    def subtotal(self):
        return self.quantity * self.price_per_unit

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    min_quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    distributor = db.relationship('User', backref=db.backref('distributor_inventory', lazy=True))

    @property
    def status(self):
        if self.quantity <= 0:
            return 'out_of_stock'
        elif self.quantity <= self.min_quantity:
            return 'low_stock'
        else:
            return 'in_stock'

    @property
    def status_color(self):
        status_colors = {
            'out_of_stock': 'danger',
            'low_stock': 'warning',
            'in_stock': 'success'
        }
        return status_colors.get(self.status, 'secondary')

class Delivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_transit, completed, failed
    scheduled_date = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    delivery_address = db.Column(db.Text, nullable=False)
    tracking_number = db.Column(db.String(50), unique=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = db.relationship('Order', backref=db.backref('order_deliveries', lazy=True))
    distributor = db.relationship('User', backref=db.backref('distributor_deliveries', lazy=True))

    @property
    def status_color(self):
        status_colors = {
            'scheduled': 'info',
            'in_transit': 'primary',
            'completed': 'success',
            'failed': 'danger'
        }
        return status_colors.get(self.status, 'secondary')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    
    # Relationships
    crop = db.relationship('Crop', backref=db.backref('order_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))
    
    @property
    def total_amount(self):
        return self.quantity * self.price_per_unit
        
    @property
    def item_name(self):
        if self.crop:
            return self.crop.name
        elif self.product:
            return self.product.name
        return "Unknown Item"

    