from __init_app__ import app
from models import User

from flask_login import LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, SubmitField, TextAreaField, validators
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)

class SignupForm(FlaskForm):
    username = StringField(validators=[InputRequired(message='Username is required'), Length(min=4, max=20), validators.regexp('^[a-zA-Z0-9]*$', message='Should not contain special characters')])
    password = PasswordField(validators=[InputRequired(message='Password is required'), Length(min=4,max=20), EqualTo(fieldname='confirm_password', message='Passwords do not match')])
    confirm_password = PasswordField(validators=[InputRequired(message='Required field'), Length(min=4, max=20)])
    name = StringField(validators=[InputRequired(message='Name is required'), Length(min=2, max=50), validators.regexp('^[a-zA-Z]*\s?[a-zA-Z]*$', message='Invalid name')])
    bio = TextAreaField(Length(max=100))
    image  = FileField([validators.regexp('.\(jpg|png|jpeg\)$', message='Invalid image format')])
    submit = SubmitField('Signup')

    def validate_username(self, username):
        existing_username = User.query.filter_by(username=self.username.data).first()
        if existing_username:
            raise ValidationError('Username already exists')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(min=4,max=20)])
    submit = SubmitField('Login')

    def validate_username(self, username):
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user is None:
            raise ValidationError('User not found')

    def validate_password(self, password):
        user = User.query.filter_by(username=self.username.data).first()
        if user is not None:
            if bcrypt.check_password_hash(user.password, password.data):
                pass
            else:
                raise ValidationError('Incorrect password')

class EditProfileForm(FlaskForm):
    name = StringField(validators=[InputRequired(message='Name is required'), Length(min=2), validators.regexp('^[a-zA-Z]*\s?[a-zA-Z]*$', message='Invalid name')])
    bio = TextAreaField(Length(max=100))
    image  = FileField([validators.regexp('.\(jpg|png|jpeg\)$', message='Invalid image format')])
    submit = SubmitField('Save Changes')