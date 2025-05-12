from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    PasswordField, 
    SelectField, 
    SubmitField,
    DateField,  # New import added here
    FloatField,
    IntegerField,
    TextAreaField,
    FileField
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional
from models import User, Product

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
        Length(min=6)
    ])
    role = SelectField('Role', choices=[
        ('farmer', 'Farmer'), 
        ('distributor', 'Distributor'),
        ('retailer', 'Retailer')
    ], validators=[DataRequired()])
    farm_size = StringField('Farm Size (acres)')
    location = StringField('Location', validators=[DataRequired()])

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=25)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])

class CropForm(FlaskForm):
    name = StringField('Crop Name', validators=[DataRequired()])  # This was missing
    variety = StringField('Variety')
    planting_season = SelectField('Planting Season', choices=[
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'), 
        ('winter', 'Winter')
    ])
    harvest_period = StringField('Harvest Period (days)')
    yield_per_acre = FloatField('Yield per Acre')
    price_per_unit = FloatField('Price per Unit')
    description = TextAreaField('Description')
    image = FileField('Crop Image')


class CreateOrderForm(FlaskForm):
    farmer_id = SelectField('Farmer', coerce=int, validators=[DataRequired()])
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Create Order')

    def __init__(self, *args, **kwargs):
        super(CreateOrderForm, self).__init__(*args, **kwargs)
        # Dynamically populate the 'farmer_id' field with farmers from the database
        self.farmer_id.choices = [(farmer.id, farmer.username) for farmer in User.query.filter_by(role='farmer').all()]
        # Dynamically populate the 'product_id' field with products from the database
        self.product_id.choices = [(product.id, product.name) for product in Product.query.all()]
