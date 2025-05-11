from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, DateField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('farmer', 'Farmer'), ('distributor', 'Distributor')])
    location = StringField('Location', validators=[DataRequired()])
    farm_size = FloatField('Farm Size (acres)', validators=[NumberRange(min=0)])

class CropForm(FlaskForm):
    crop_type = StringField('Crop Type', validators=[DataRequired()])
    quantity = FloatField('Quantity (kg)', validators=[NumberRange(min=0)])
    planting_date = DateField('Planting Date', format='%Y-%m-%d')