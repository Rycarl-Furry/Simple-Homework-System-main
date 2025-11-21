from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField
from wtforms.validators import InputRequired, Email, Length
import os
from dotenv import load_dotenv
import pymysql
import email_validator
import hashlib

# 加载环境变量
load_dotenv()

# 密码加密函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 设置MySQL连接
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')

# 数据库配置
DB_USER = os.getenv('MYSQL_USER', 'root')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
DB_HOST = os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = os.getenv('MYSQL_PORT', '3306')
DB_NAME = os.getenv('MYSQL_DB', 'homework_system')

# 尝试连接数据库，如果数据库不存在则创建
conn = None
try:
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=int(DB_PORT)
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"数据库连接或创建失败: {e}")

# 配置SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 文件上传安全配置
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'zip', 'pdf', 'md'}
# 最大文件大小 (500MB)
MAX_CONTENT_LENGTH = 500 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 安全处理文件名，过滤不安全字符
def secure_filename(filename):
    # 过滤掉路径分隔符和上级目录引用
    return filename.replace('/', '').replace('\\', '').replace('..', '')

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Homework(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    homework_number = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    submit_time = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    user = db.relationship('User', backref=db.backref('homeworks', lazy=True))

# 创建数据库表
with app.app_context():
    db.create_all()
    # 检查是否有管理员用户，如果没有则创建
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        admin = User(username='admin', student_id='00000000', email='redrock@admin.com', password=hash_password('admin@rycarl'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

# 表单类
class RegisterForm(FlaskForm):
    username = StringField('姓名', validators=[InputRequired(), Length(min=2, max=100)])
    student_id = StringField('学号', validators=[InputRequired(), Length(min=8, max=20)])
    email = StringField('邮箱', validators=[InputRequired(), Email(), Length(max=100)])
    password = PasswordField('密码', validators=[InputRequired(), Length(min=4, max=100)])
    submit = SubmitField('注册')

class LoginForm(FlaskForm):
    student_id = StringField('学号', validators=[InputRequired(), Length(min=8, max=20)])
    password = PasswordField('密码', validators=[InputRequired(), Length(min=4, max=100)])
    submit = SubmitField('登录')

# 作业数字到名称的映射
def get_homework_name(number):
    homework_names = {
        1: 'Linux基础',
        2: 'Python基础',
        3: 'Git',
        4: 'Liunx进阶',
        5: '虚拟化和容器技术',
        6:'计算机网络',
    }
    return homework_names.get(number, f'第{number}次作业')

class HomeworkForm(FlaskForm):
    homework_number = SelectField('作业选项', choices=[(1, 'Linux基础'), (2, 'Python基础'), (3, 'Git'), (4, 'Liunx进阶'), (5, '虚拟化和容器技术'), (6, '计算机网络')], coerce=int)
    file = FileField('上传文件', validators=[InputRequired()])
    submit = SubmitField('提交')

# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # 检查学号和邮箱是否已存在
        existing_student = User.query.filter_by(student_id=form.student_id.data).first()
        existing_email = User.query.filter_by(email=form.email.data).first()
        
        if existing_student:
            flash('学号已被注册', 'danger')
            return redirect(url_for('register'))
        if existing_email:
            flash('邮箱已被注册', 'danger')
            return redirect(url_for('register'))
        
        # 创建新用户
        new_user = User(
            username=form.username.data,
            student_id=form.student_id.data,
            email=form.email.data,
            password=hash_password(form.password.data)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(student_id=form.student_id.data).first()
        if user and user.password == hash_password(form.password.data):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('学号或密码错误', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    form = HomeworkForm()
    # 获取当前用户的作业提交记录
    user_homeworks = Homework.query.filter_by(user_id=current_user.id).all()
    # 为每个作业添加名称字段
    for homework in user_homeworks:
        homework.name = get_homework_name(homework.homework_number)
    return render_template('student_dashboard.html', form=form, homeworks=user_homeworks, get_homework_name=get_homework_name)

@app.route('/submit_homework', methods=['POST'])
@login_required
def submit_homework():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    form = HomeworkForm()
    if form.validate_on_submit():
        file = form.file.data
        homework_number = form.homework_number.data
        
        # 检查文件扩展名
        if not allowed_file(file.filename):
            flash('不支持的文件类型，仅允许上传 .zip、.pdf 或 .md 文件', 'danger')
            return redirect(url_for('student_dashboard'))
        
        # 检查文件大小（Flask已经通过MAX_CONTENT_LENGTH配置限制了请求大小）
        
        # 为用户创建以学号命名的文件夹
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], current_user.student_id)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # 安全处理文件名
        safe_filename = secure_filename(file.filename)
        
        # 检查用户是否已经提交过该次数的作业
        existing_homework = Homework.query.filter_by(user_id=current_user.id, homework_number=homework_number).first()
        if existing_homework:
            # 删除旧文件
            old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], existing_homework.file_path)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            # 更新数据库记录
            existing_homework.file_name = file.filename  # 保留原始文件名用于显示
            existing_homework.file_path = f"{current_user.student_id}/{homework_number}_{safe_filename}"
            file.save(os.path.join(user_folder, f"{homework_number}_{safe_filename}"))
            flash('作业更新成功', 'success')
        else:
            # 保存新文件
            file_path = f"{current_user.student_id}/{homework_number}_{safe_filename}"
            file.save(os.path.join(user_folder, f"{homework_number}_{safe_filename}"))
            
            # 添加到数据库
            new_homework = Homework(
                user_id=current_user.id,
                homework_number=homework_number,
                file_path=file_path,
                file_name=file.filename  # 保留原始文件名用于显示
            )
            db.session.add(new_homework)
            flash('作业提交成功', 'success')
        
        db.session.commit()
        return redirect(url_for('student_dashboard'))
    
    flash('提交失败，请检查表单', 'danger')
    return redirect(url_for('student_dashboard'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    # 获取所有用户
    users = User.query.all()
    
    # 统计每个用户的作业提交情况
    user_stats = {}
    for user in users:
        if not user.is_admin:
            user_homeworks = Homework.query.filter_by(user_id=user.id).all()
            # 为每个作业添加名称字段
            for homework in user_homeworks:
                homework.name = get_homework_name(homework.homework_number)
            user_stats[user.id] = {
                'username': user.username,
                'student_id': user.student_id,
                'email': user.email,
                'homeworks': user_homeworks
            }
    
    return render_template('admin_dashboard.html', user_stats=user_stats, get_homework_name=get_homework_name)

@app.route('/download/<int:homework_id>')
@login_required
def download_homework(homework_id):
    homework = Homework.query.get_or_404(homework_id)
    # 只有管理员或作业所有者可以下载
    if not current_user.is_admin and homework.user_id != current_user.id:
        flash('无权访问该文件', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # 安全检查文件路径，防止路径遍历攻击
    import os.path
    safe_path = os.path.normpath(homework.file_path)
    if '..' in safe_path or not safe_path.startswith(str(homework.user.student_id)):
        flash('无效的文件路径', 'danger')
        return redirect(url_for('student_dashboard'))
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_path, as_attachment=True, download_name=homework.file_name)

@app.route('/delete_homework/<int:homework_id>')
@login_required
def delete_homework(homework_id):
    homework = Homework.query.get_or_404(homework_id)
    # 只有管理员可以删除
    if not current_user.is_admin:
        flash('无权执行此操作', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # 安全检查文件路径
    import os.path
    safe_path = os.path.normpath(homework.file_path)
    if '..' in safe_path or not safe_path.startswith(str(homework.user.student_id)):
        flash('无效的文件路径', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # 删除文件
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # 删除数据库记录
    db.session.delete(homework)
    db.session.commit()
    flash('作业已删除', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0',port=5000)