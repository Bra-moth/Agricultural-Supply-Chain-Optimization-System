from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    SubmitField,
    DateField,
    FloatField,
    IntegerField,
    TextAreaField,
    BooleanField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    EqualTo,
    ValidationError
)
from models import User, Product
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=25)
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

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
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('farmer', 'Farmer'),
        ('distributor', 'Distributor'),
        ('retailer', 'Retailer')
    ], validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    farm_size = StringField('Farm Size (acres)', validators=[Optional()])
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[
        DataRequired(message='You must agree to the terms and conditions')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class CropForm(FlaskForm):
    name = StringField('Crop Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    variety = StringField('Variety', validators=[
        Optional(),
        Length(max=100, message='Variety name must not exceed 100 characters')
    ])
    
    quantity = FloatField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message='Quantity must be greater than 0')
    ])
    
    unit = SelectField('Unit', choices=[
        ('kg', 'Kilograms (kg)'),
        ('g', 'Grams (g)'),
        ('ton', 'Tons'),
        ('piece', 'Pieces')
    ], validators=[DataRequired()])
    
    planting_date = DateField('Planting Date', validators=[DataRequired()])
    expected_harvest_date = DateField('Expected Harvest Date', validators=[DataRequired()])
    
    planting_season = SelectField('Planting Season', choices=[
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
        ('winter', 'Winter')
    ], validators=[DataRequired()])
    
    harvest_period = IntegerField('Harvest Period (days)', validators=[
        Optional(),
        NumberRange(min=1, message='Harvest period must be at least 1 day')
    ])
    
    yield_per_acre = FloatField('Yield per Acre', validators=[
        Optional(),
        NumberRange(min=0, message='Yield must be greater than 0')
    ])
    
    price_per_unit = FloatField('Price per Unit (R)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Price must be greater than 0')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=500, message='Description must not exceed 500 characters')
    ])
    
    image = FileField('Crop Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only images (jpg, jpeg, png, gif) are allowed!')
    ])
    
    submit = SubmitField('Save Crop')

class CreateOrderForm(FlaskForm):
    farmer_id = SelectField('Farmer', coerce=int, validators=[DataRequired()])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Quantity must be greater than 0')
    ])
    submit = SubmitField('Create Order')

    def __init__(self, *args, **kwargs):
        super(CreateOrderForm, self).__init__(*args, **kwargs)
        # Dynamically populate the farmer_id field with farmers
        self.farmer_id.choices = [
            (farmer.id, f"{farmer.username} ({farmer.location})")
            for farmer in User.query.filter_by(role='farmer').all()
        ]
        # Dynamically populate the product_id field with products
        self.product_id.choices = [
            (product.id, f"{product.name} (${product.price_per_unit:.2f}/{product.unit})")
            for product in Product.query.all()
        ]

class PlaceOrderForm(FlaskForm):
    quantity = FloatField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Quantity must be greater than 0')
    ])
    delivery_address = StringField('Delivery Address', validators=[
        DataRequired(),
        Length(min=10, max=200, message='Address must be between 10 and 200 characters')
    ])
    notes = TextAreaField('Order Notes', validators=[
        Optional(),
        Length(max=500, message='Notes must be less than 500 characters')
    ])
    submit = SubmitField('Place Order')
