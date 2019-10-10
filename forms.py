from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, TextAreaField, RadioField
from wtforms import validators, ValidationError
from wtforms.validators import InputRequired, EqualTo, Email, Length, DataRequired, Regexp

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20, message='Your username needs to be 4-20 characters long'), Regexp(r'^[\w]+$', message='Only alphanumeric characters are allowed')])
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email address')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=255, message="Use a password at least 8 characters long")])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password', message='Passwords must match')])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign Up')
    
class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[InputRequired()]) # can be username or email
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SearchForm(FlaskForm):
    search = StringField('Search', render_kw={"placeholder": "Find Movies by Title, IMDB ID, Year of Release..."})

class ReviewForm(FlaskForm):
    rating = RadioField('Rating', choices=[
        (10, ''), (9, ''), (8, ''), (7, ''), (6, ''), (5, ''), (4, ''), (3, ''), (2, ''), (1, '')
    ], render_kw={'required': True}, coerce=int)
    # wtforms bug#477 - DataRequired() and InputRequired() not working for RadioField; workaround - render_kw
    review = TextAreaField('Your Review', validators=[InputRequired(), Length(max=65535, message='Your review is too long. Please shorten it.')], render_kw={'rows': 8})
    submit = SubmitField('Submit')

    class Meta:
        def render_field(self, field, render_kw):
            render_kw.setdefault('required', True)
            return super().render_field(field, render_kw)