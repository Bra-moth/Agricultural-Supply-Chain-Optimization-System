from datetime import datetime  # Add this import at the top
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100))
    farm_size = db.Column(db.Float)
    crops = db.relationship('Crop', backref='farmer', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    planting_date = db.Column(db.Date, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float)
    status = db.Column(db.String(50), default='Pending')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))