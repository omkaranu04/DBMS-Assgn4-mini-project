from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    user_type = SelectField('User Type', choices=[
        ('System Administrator', 'System Administrator'),
        ('Government Official', 'Government Official'),
        ('Panchayat Employee', 'Panchayat Employee'),
        ('Citizen', 'Citizen')
    ], validators=[DataRequired()])
    submit = SubmitField('Login')

class PanchayatEmployeeForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    designation = SelectField('Designation', choices=[
        ('Sarpanch', 'Sarpanch'),
        ('Naib Sarpanch', 'Naib Sarpanch'),
        ('Panchayat Secretary', 'Panchayat Secretary'),
        ('Gram Sevak', 'Gram Sevak'),
        ('Ward Member', 'Ward Member'),
        ('Community Mobilizer', 'Community Mobilizer')
    ], validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class GovernmentOfficialForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')