from __future__ import annotations
from extensions import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(100), nullable=False)
    student_id: str = db.Column(db.String(20), unique=True, nullable=False)
    email: str = db.Column(db.String(100), unique=True, nullable=False)
    password: str = db.Column(db.String(100), nullable=False)
    is_admin: bool = db.Column(db.Boolean, default=False)

    def __init__(
        self,
        username: str,
        student_id: str,
        email: str,
        password: str,
        is_admin: bool = False,
    ) -> None:
        self.username = username
        self.student_id = student_id
        self.email = email
        self.password = password
        self.is_admin = is_admin
