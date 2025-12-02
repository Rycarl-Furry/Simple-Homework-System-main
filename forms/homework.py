from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, SelectField
from wtforms.validators import InputRequired
from utils.helpers import HOMEWORKS


class HomeworkForm(FlaskForm):
    homework_number = SelectField(
        "作业选项",
        coerce=int,
        choices=[(i["id"], i["name"]) for i in HOMEWORKS],
    )
    file = FileField("上传文件", validators=[InputRequired()])
    submit = SubmitField("提交")
