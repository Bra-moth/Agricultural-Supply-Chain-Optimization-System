from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[
        ('farmer', 'Farmer'), 
        ('distributor', 'Distributor'),
        ('retailer', 'Retailer')
    ], validators=[DataRequired()])
    farm_size = StringField('Farm Size (acres)')
    location = StringField('Location', validators=[DataRequired()])
