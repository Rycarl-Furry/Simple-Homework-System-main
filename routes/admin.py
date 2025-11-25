from flask import Blueprint, render_template, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
import os
from models.user import User
from models.homework import Homework
from utils.helpers import get_homework_name
from extensions import db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard")
@login_required
def dashboard():
    users = User.query.all()
    stats = {}

    for u in users:
        if not u.is_admin:
            hw_list: list[Homework] = Homework.query.filter_by(
                user_id=u.id).all()
            for h in hw_list:
                h.name = get_homework_name(h.homework_number)
            stats[u.id] = {
                "username": u.username,
                "student_id": u.student_id,
                "email": u.email,
                "homeworks": hw_list,
            }

    return render_template("admin_dashboard.html", user_stats=stats)


@admin_bp.route("/admin/download/<int:homework_id>")
@login_required
def download(homework_id):
    hw = Homework.query.get_or_404(homework_id)
    if not current_user.is_admin:
        flash("无权限", "danger")
        return redirect(url_for("student.dashboard"))

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        hw.file_path,
        as_attachment=True,
        download_name=hw.file_name,
    )


@admin_bp.route("/admin/delete_homework/<int:homework_id>")
@login_required
def delete(homework_id):
    if not current_user.is_admin:
        flash("无权限", "danger")
        return redirect(url_for("student.dashboard"))

    hw = Homework.query.get_or_404(homework_id)

    path = os.path.join(current_app.config["UPLOAD_FOLDER"], hw.file_path)
    if os.path.exists(path):
        os.remove(path)

    db.session.delete(hw)
    db.session.commit()

    flash("已删除", "success")
    return redirect(url_for("admin.dashboard"))
