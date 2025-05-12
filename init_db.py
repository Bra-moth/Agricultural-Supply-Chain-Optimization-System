import os
from app import app, db
from extensions import db
from models import User, Crop, Product, Order, RestockOrder, Supplier

db_path = "agricultural_scm.db"

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"🗑️  Removed existing database '{db_path}'.")





# Recreate the database
with app.app_context():
    print("🔧 Creating new database tables...")
    db.create_all()
    print(f"✅ Database '{db_path}' created successfully.")