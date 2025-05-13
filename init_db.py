import os
from app import app, db
from models import User, Crop, Product, Order, RestockOrder, Supplier, Cart, CartItem, InventoryItem, Delivery, OrderItem
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def initialize_database():
    # Ensure instance folder exists
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"📁 Created instance directory at '{instance_path}'")
    
    db_path = os.path.join(instance_path, "agricultural_scm.db")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"🗑️ Removed existing database '{db_path}'")
        except Exception as e:
            print(f"⚠️ Failed to remove existing database: {e}")
            return False
    
    # Create new database and tables
    with app.app_context():
        try:
            print("🔧 Creating database tables...")
            db.create_all()
            
            # Add sample data
            print("📝 Adding sample data...")
            add_sample_data()
            
            print(f"✅ Database initialized successfully at '{db_path}'")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize database: {e}")
            return False

def add_sample_data():
    try:
        # Create sample users
        users = [
            User(
                username="farmer_john",
                email="john@example.com",
                role="farmer",
                location="Kimberley, Northern Cape",
                farm_size="50 acres"
            ),
            User(
                username="distributor_sam",
                email="sam@example.com",
                role="distributor",
                location="Bloemfontein, Free State"
            ),
            User(
                username="retailer_mary",
                email="mary@example.com",
                role="retailer",
                location="Cape Town, Western Cape"
            )
        ]
        
        # Set passwords
        users[0].set_password("farm123")
        users[1].set_password("dist123")
        users[2].set_password("retail123")
        
        db.session.add_all(users)
        db.session.commit()
        print("👥 Added sample users")

        # Create sample products
        products = [
            Product(
                name="Maize",
                description="High quality maize",
                category="Cereals",
                unit="kg",
                current_stock=1000,
                reorder_level=200,
                price_per_unit=0.50
            ),
            Product(
                name="Beans",
                description="Organic beans",
                category="Legumes",
                unit="kg",
                current_stock=500,
                reorder_level=100,
                price_per_unit=1.20
            )
        ]
        db.session.add_all(products)
        db.session.commit()
        print("📦 Added sample products")

        # Create sample crops
        crops = [
            Crop(
                name="Maize",
                variety="Yellow Maize",
                quantity=1000,
                unit="kg",
                planting_date=datetime.utcnow() - timedelta(days=60),
                expected_harvest_date=datetime.utcnow() + timedelta(days=30),
                status="growing",
                description="Yellow maize variety, healthy growth",
                farmer_id=users[0].id,
                planting_season="spring",
                harvest_period=90,
                yield_per_acre=1000,
                price_per_unit=150.0
            ),
            Crop(
                name="Beans",
                variety="Red Kidney",
                quantity=500,
                unit="kg",
                planting_date=datetime.utcnow() - timedelta(days=30),
                expected_harvest_date=datetime.utcnow() + timedelta(days=30),
                status="growing",
                description="Red kidney beans, organic farming",
                farmer_id=users[0].id,
                planting_season="summer",
                harvest_period=90,
                yield_per_acre=500,
                price_per_unit=30.0
            )
        ]
        db.session.add_all(crops)
        db.session.commit()
        print("🌾 Added sample crops")

        # Create sample orders
        orders = [
            Order(
                farmer_id=users[0].id,
                retailer_id=users[2].id,
                distributor_id=users[1].id,
                status="completed",
                total_amount=100.00,
                created_at=datetime.utcnow() - timedelta(days=10),
                completed_at=datetime.utcnow() - timedelta(days=5),
                notes="First order completed successfully"
            ),
            Order(
                farmer_id=users[0].id,
                retailer_id=users[2].id,
                distributor_id=users[1].id,
                status="pending",
                total_amount=120.00,
                created_at=datetime.utcnow() - timedelta(days=2),
                notes="Second order pending"
            )
        ]
        db.session.add_all(orders)
        db.session.commit()
        print("📋 Added sample orders")

        # Create sample suppliers
        suppliers = [
            Supplier(
                name="AgriSupplies Ltd",
                address="123 Farm Road, Kimberley",
                contact_email="info@agrisupplies.com",
                contact_phone="+27123456789"
            ),
            Supplier(
                name="Seed & Grain Co",
                address="456 Harvest Avenue, Bloemfontein",
                contact_email="contact@seedgrain.com",
                contact_phone="+27987654321"
            )
        ]
        db.session.add_all(suppliers)
        db.session.commit()
        print("🏢 Added sample suppliers")

        # Create test users
        test_users = [
            {
                'username': 'farmer1',
                'email': 'farmer1@example.com',
                'role': 'farmer',
                'location': '123 Farm Road',
                'farm_size': '50 acres'
            },
            {
                'username': 'distributor1',
                'email': 'distributor1@example.com',
                'role': 'distributor',
                'location': '456 Distribution Center'
            },
            {
                'username': 'retailer1',
                'email': 'retailer1@example.com',
                'role': 'retailer',
                'location': '789 Retail Street'
            }
        ]
        
        for user_data in test_users:
            user = User(**user_data)
            user.set_password('password123')
            db.session.add(user)
        
        db.session.commit()
        
        # Get created users
        farmer = User.query.filter_by(role='farmer').first()
        distributor = User.query.filter_by(role='distributor').first()
        retailer = User.query.filter_by(role='retailer').first()
        
        # Create test crops
        test_crops = [
            {
                'name': 'Maize',
                'variety': 'Yellow Dent',
                'quantity': 1000,
                'unit': 'kg',
                'planting_date': datetime.utcnow(),
                'expected_harvest_date': datetime.utcnow() + timedelta(days=90),
                'status': 'growing',
                'description': 'High-yield yellow dent corn variety',
                'farmer_id': farmer.id,
                'planting_season': 'spring',
                'harvest_period': 90,
                'yield_per_acre': 1000,
                'price_per_unit': 150.0
            },
            {
                'name': 'Tomatoes',
                'variety': 'Roma',
                'quantity': 500,
                'unit': 'kg',
                'planting_date': datetime.utcnow() - timedelta(days=70),
                'expected_harvest_date': datetime.utcnow() + timedelta(days=20),
                'status': 'ready_for_harvest',
                'description': 'Disease-resistant Roma tomatoes',
                'farmer_id': farmer.id,
                'planting_season': 'summer',
                'harvest_period': 90,
                'yield_per_acre': 500,
                'price_per_unit': 30.0
            }
        ]
        
        for crop_data in test_crops:
            crop = Crop(**crop_data)
            db.session.add(crop)
        
        # Create test inventory items
        test_inventory = [
            {
                'distributor_id': distributor.id,
                'name': 'Fresh Maize',
                'category': 'Grains',
                'quantity': 1000.0,
                'unit': 'kg',
                'min_quantity': 200.0,
                'price_per_unit': 18.0,
                'description': 'Fresh yellow maize from local farmers'
            },
            {
                'distributor_id': distributor.id,
                'name': 'Roma Tomatoes',
                'category': 'Vegetables',
                'quantity': 500.0,
                'unit': 'kg',
                'min_quantity': 100.0,
                'price_per_unit': 30.0,
                'description': 'Fresh Roma tomatoes'
            },
            {
                'distributor_id': distributor.id,
                'name': 'Potatoes',
                'category': 'Vegetables',
                'quantity': 50.0,
                'unit': 'kg',
                'min_quantity': 100.0,
                'price_per_unit': 12.0,
                'description': 'Fresh potatoes (low stock)'
            }
        ]
        
        for inventory_data in test_inventory:
            item = InventoryItem(**inventory_data)
            db.session.add(item)
        
        # Create test order
        test_order = Order(
            farmer_id=farmer.id,
            retailer_id=retailer.id,
            distributor_id=distributor.id,
            status='processing',
            total_amount=900.0,
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        db.session.add(test_order)
        db.session.commit()
        
        # Add order items
        test_order_items = [
            {
                'order_id': test_order.id,
                'product_id': 1,
                'quantity': 30,
                'price_per_unit': 18.0
            },
            {
                'order_id': test_order.id,
                'product_id': 2,
                'quantity': 15,
                'price_per_unit': 30.0
            }
        ]
        
        for item_data in test_order_items:
            item = OrderItem(**item_data)
            db.session.add(item)
        
        # Create test delivery
        test_delivery = Delivery(
            order_id=test_order.id,
            distributor_id=distributor.id,
            status='scheduled',
            scheduled_date=datetime.utcnow() + timedelta(days=1),
            delivery_address=retailer.location,
            tracking_number='TRK123456789'
        )
        db.session.add(test_delivery)
        
        # Create test cart
        test_cart = Cart(
            retailer_id=retailer.id,
            status='active'
        )
        db.session.add(test_cart)
        db.session.commit()
        
        # Add cart items
        test_cart_items = [
            {
                'cart_id': test_cart.id,
                'product_id': 1,
                'quantity': 10,
                'price_per_unit': 18.0
            }
        ]
        
        for item_data in test_cart_items:
            item = CartItem(**item_data)
            db.session.add(item)
        
        db.session.commit()
        
        print('Database initialized with test data!')

    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to add sample data: {e}")
        raise

if __name__ == '__main__':
    initialize_database()