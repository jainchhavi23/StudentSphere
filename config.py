import os
UPLOAD_FOLDER = os.path.join("static", "uploads")
class Config:
    SECRET_KEY = "student_management_system_secret_key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///students.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join("static", "uploads")
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "jchhavi2317@gmail.com"
    MAIL_PASSWORD = "lyjp uclq nuzo wtme"
    MAIL_DEFAULT_SENDER = "jchhavi2317@gmail.com"

