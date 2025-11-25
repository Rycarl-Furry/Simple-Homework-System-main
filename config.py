import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "PleaseChangeThisSecretKey")

    # MySQL 配置
    DB_USER: str = os.getenv("MYSQL_USER", "root")
    DB_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "root")
    DB_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    DB_PORT: str = os.getenv("MYSQL_PORT", "3306")
    DB_NAME: str = os.getenv("MYSQL_DB", "homework_system")

    SQLALCHEMY_DATABASE_URI: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # 上传文件
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 500 * 1024 * 1024  # 500MB
