from flask_login import UserMixin
from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100))
    farm_size = db.Column(db.String(50))
    
    # Updated relationships with explicit foreign_keys
    crops = db.relationship('Crop', backref='crop_farmer', lazy=True, 
                          foreign_keys='Crop.crop_farmer_id')
    
    # Split orders into two separate relationships
    farmer_orders = db.relationship('Order', 
                                  backref='selling_farmer', 
                                  lazy=True,
                                  foreign_keys='Order.order_farmer_id')
    
    buyer_orders = db.relationship('Order',
                                 backref='purchasing_buyer',
                                 lazy=True,
                                 foreign_keys='Order.buyer_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Crop(db.Model):
    __tablename__ = 'crops'
    id = db.Column(db.Integer, primary_key=True)
    crop_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    planting_date = db.Column(db.Date, nullable=False)
    crop_farmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    distributor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime)
    farmer = db.relationship('User', foreign_keys=[farmer_id], backref='orders_as_farmer')
    distributor = db.relationship('User', foreign_keys=[distributor_id], backref='orders_as_distributor')
    product = db.relationship('Product', backref='orders')


class RestockOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Float)
    distributor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='requested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref='restock_orders')
    distributor = db.relationship('User')