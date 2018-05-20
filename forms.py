from wtforms import Form, StringField, PasswordField, DateField, validators

class LoginForm(Form):
    email = StringField('email')
    password = PasswordField('password')

class RegistrationForm(Form):
    email = StringField('email')
    password = PasswordField('password')
    company_name = StringField('compnay_name')
    company_url = StringField('company_url')

class EventForm(Form):
    start_date = DateField('start_date')
    end_date = DateField('end_date')
    event_name = StringField('event_name')
    event_type = StringField('event_type')
    event_description = StringField('event_description')

