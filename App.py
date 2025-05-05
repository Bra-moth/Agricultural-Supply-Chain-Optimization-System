from flask import Flask, render_template, request, redirect, url_for
from .models import db, Product  # Use relative import if models.py is in the same directory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ascos.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

@app.route('/')
def home():
    return redirect(url_for('farmer_dashboard'))

@app.route('/dashboard/farmer')
def farmer_dashboard():
    products = Product.query.all()
    return render_template('farmer_dashboard.html', products=products)

@app.route('/add-product', methods=['POST'])
def add_product():
    name = request.form['name']
    category = request.form['category']
    price = request.form['price']
    quantity = request.form['quantity']
    location = request.form['location']

    product = Product(name=name, category=category, price=price, quantity=quantity, location=location)
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('farmer_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
