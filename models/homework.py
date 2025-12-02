from __future__ import annotations
from extensions import db


class Homework(db.Model):
    __tablename__ = "homework"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False)
    homework_number: int = db.Column(db.Integer, nullable=False)
    file_path: str = db.Column(db.String(255), nullable=False)
    file_name: str = db.Column(db.String(255), nullable=False)
    submit_time = db.Column(
        db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('homeworks', lazy=True))

    def __init__(
        self,
        user_id: int,
        homework_number: int,
        file_path: str,
        file_name: str,
        name: str | None = None,
    ) -> None:
        self.user_id = user_id
        self.homework_number = homework_number
        self.file_path = file_path
        self.file_name = file_name
        self.name = name
