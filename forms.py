from flask_wtf import Form
from wtforms import Form, StringField, PasswordField, validators


class LoginForm(Form):
    email = StringField('email')
    password = PasswordField('password')

class RegistrationForm(Form):
    email = StringField('email')
    password = PasswordField('password')
    company_name = StringField('compnay_name')
    company_url = StringField('company_url')
