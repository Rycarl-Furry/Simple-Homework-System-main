from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length


class RegisterForm(FlaskForm):
    username = StringField("姓名", validators=[InputRequired(), Length(2, 100)])
    student_id = StringField("学号", validators=[InputRequired(), Length(8, 20)])
    email = StringField("邮箱", validators=[InputRequired(), Email()])
    password = PasswordField(
        "密码", validators=[InputRequired(), Length(4, 100)])
    submit = SubmitField("注册")


class LoginForm(FlaskForm):
    student_id = StringField("学号", validators=[InputRequired(), Length(8, 20)])
    password = PasswordField(
        "密码", validators=[InputRequired(), Length(4, 100)])
    submit = SubmitField("登录")
