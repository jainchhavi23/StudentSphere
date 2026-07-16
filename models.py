from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    address = db.Column(db.Text)

    photo = db.Column(db.String(200), nullable=True)

    status = db.Column(db.String(20), default="Active")

    admission_date = db.Column(db.Date)

    dob = db.Column(db.Date)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("admins.id"),
        nullable=False
    )


class Admin(db.Model):

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    students = db.relationship(
        "Student",
        backref="admin",
        lazy=True
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<Admin {self.username}>"