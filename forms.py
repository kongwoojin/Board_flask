from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import InputRequired, EqualTo, Email, Length
from wtforms.widgets import TextArea


class SignUpForm(FlaskForm):
    userid = StringField('User ID', [InputRequired()])
    username = StringField('Username', [InputRequired()])
    email = EmailField('Email', [InputRequired()])
    password = PasswordField('Password', [InputRequired(),
                                          Length(min=8, message="Password too short!"),
                                          EqualTo('confirm', message="Password not match!")])
    confirm = PasswordField('Password confirm')
    submit = SubmitField('Sign Up')


class SignInForm(FlaskForm):
    userid = StringField('User ID', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])
    submit = SubmitField('Sign In')


class WriteForm(FlaskForm):
    title = StringField('Title', [InputRequired()])
    text = StringField('Text', widget=TextArea())
    submit = SubmitField('Write')


class CommentForm(FlaskForm):
    comment = StringField('Comment', [InputRequired()], widget=TextArea())
    submit = SubmitField('Write')
