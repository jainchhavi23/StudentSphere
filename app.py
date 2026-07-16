from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Student, Admin
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)
from config import Config
import re
from werkzeug.security import generate_password_hash
from openpyxl import Workbook
from flask import send_file
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message
import random
from openpyxl import load_workbook
import pandas as pd
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail = Mail(app)
app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        photo = request.files.get("photo")
        filename = ""
        if photo and photo.filename != "":
            filename = secure_filename(photo.filename)
            photo.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )
        admin = Admin.query.filter_by(
             username=session["admin"]
         ).first()
        student = Student(
            name=request.form.get("name"),
            roll_no=request.form.get("roll_no"),
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            course=request.form.get("course"),
            semester=request.form.get("semester"),
            gender=request.form.get("gender"),
            address=request.form.get("address"),

            dob=datetime.strptime(
                request.form.get("dob"),
                "%Y-%m-%d"
            ).date(),

            admission_date=datetime.strptime(
                request.form.get("admission_date"),
                "%Y-%m-%d"
            ).date(),

            photo=filename,
            admin_id=admin.id
        )

        db.session.add(student)
        db.session.commit()

        flash("Student Added Successfully!", "success")
        return redirect(url_for("students"))

    return render_template("add_student.html")
      
@app.route("/profile")
def profile():

    if "admin" not in session:
        return redirect(url_for("login"))

    admin = Admin.query.filter_by(username=session["admin"]).first()

    return render_template("profile.html", admin=admin)

with app.app_context():
    db.create_all()

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if len(password) < 8:
          flash("Password must be at least 8 characters long.")
          return redirect(url_for("signup"))

        if not re.search(r"[A-Z]", password):
          flash("Password must contain at least one uppercase letter.")
          return redirect(url_for("signup"))

        if not re.search(r"[a-z]", password):
          flash("Password must contain at least one lowercase letter.")
          return redirect(url_for("signup"))

        if not re.search(r"\d", password):
          flash("Password must contain at least one number.")
          return redirect(url_for("signup"))

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
          flash("Password must contain at least one special character.")
          return redirect(url_for("signup"))
        existing_admin = Admin.query.filter(
            (Admin.username == username) | (Admin.email == email)
        ).first()

        if existing_admin:
            flash("Username or Email already exists!")
            return redirect(url_for("signup"))

        admin = Admin(
            username=username,
            email=email
        )

        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        flash("Account Created Successfully! Please Login.")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username).first()

        print("Entered Username:", username)
        print("Admin Object:", admin)

        if admin:
          print("Stored Password Hash:", admin.password)
          print("Password Match:", admin.check_password(password))

        if admin and admin.check_password(password):
            session["admin"] = admin.username
            return redirect(url_for("dashboard"))

        flash("Invalid Username or Password")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def dashboard():

    if "admin" not in session:
        return redirect(url_for("login"))

    admin = Admin.query.filter_by(
        username=session["admin"]
    ).first()

    if admin is None:
        session.clear()
        flash("Please login again.")
        return redirect(url_for("login"))

    total_students = Student.query.filter_by(
        admin_id=admin.id
    ).count()

    male_students = Student.query.filter_by(
        admin_id=admin.id,
        gender="Male"
    ).count()

    female_students = Student.query.filter_by(
        admin_id=admin.id,
        gender="Female"
    ).count()

    new_students = Student.query.filter_by(
        admin_id=admin.id
    ).order_by(Student.id.desc()).limit(5).count()

    recent_students = Student.query.filter_by(
        admin_id=admin.id
    ).order_by(Student.id.desc()).limit(5).all()

    course_data = db.session.query(
        Student.course,
        db.func.count(Student.id)
    ).filter(
        Student.admin_id == admin.id
    ).group_by(Student.course).all()

    course_labels = [c[0] for c in course_data]
    course_counts = [c[1] for c in course_data]

    semester_data = db.session.query(
        Student.semester,
        db.func.count(Student.id)
    ).filter(
        Student.admin_id == admin.id
    ).group_by(Student.semester).all()

    semester_labels = [str(s[0]) for s in semester_data]
    semester_counts = [s[1] for s in semester_data]

    return render_template(
        "dashboard.html",
        total_students=total_students,
        male_students=male_students,
        female_students=female_students,
        new_students=new_students,
        recent_students=recent_students,
        course_labels=course_labels,
        course_counts=course_counts,
        semester_labels=semester_labels,
        semester_counts=semester_counts
    )

@app.route("/students")
def students():

    if "admin" not in session:
        return redirect(url_for("login"))

    admin = Admin.query.filter_by(
        username=session["admin"]
    ).first()

    page = request.args.get("page", 1, type=int)

    students = Student.query.filter_by(
        admin_id=admin.id
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    return render_template(
        "students.html",
        students=students
    )
with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username="admin").first():

        admin = Admin(
            username="admin",
            email="admin@gmail.com"
        )

        admin.set_password("admin123")

        db.session.add(admin)
        db.session.commit()

@app.route("/check-admin")
def check_admin():
    admins = Admin.query.all()

    for admin in admins:
        print(admin.username, admin.email, admin.password)

    return f"Total Admins: {len(admins)}"

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    admin = Admin.query.filter_by(
    username=session["admin"]
).first()

    student = Student.query.filter_by(
    id=id,
    admin_id=admin.id
).first_or_404()

    if request.method == "POST":

        student.name = request.form["name"]
        student.roll_no = request.form["roll_no"]
        student.email = request.form["email"]
        student.phone = request.form["phone"]
        student.course = request.form["course"]
        student.semester = request.form["semester"]
        student.gender = request.form["gender"]
        student.address = request.form["address"]

        # DOB
        student.dob = datetime.strptime(
            request.form["dob"],
            "%Y-%m-%d"
        ).date()

        # Admission Date
        student.admission_date = datetime.strptime(
            request.form["admission_date"],
            "%Y-%m-%d"
        ).date()

        # Photo Update
        photo = request.files.get("photo")

        if photo and photo.filename != "":
            filename = secure_filename(photo.filename)
            photo.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )
            student.photo = filename

        db.session.commit()

        flash("Student Updated Successfully")

        return redirect(url_for("students"))

    return render_template(
        "edit_student.html",
        student=student
    )
@app.route("/delete/<int:id>")
def delete_student(id):

    admin = Admin.query.filter_by(
    username=session["admin"]
).first()

    student = Student.query.filter_by(
    id=id,
    admin_id=admin.id
).first_or_404()

    db.session.delete(student)

    db.session.commit()

    flash("Student Deleted Successfully")

    return redirect(url_for("students"))

@app.route("/edit-account", methods=["GET", "POST"])
def edit_account():

    if "admin" not in session:
        return redirect(url_for("login"))

    admin = Admin.query.filter_by(username=session["admin"]).first()

    if request.method == "POST":

        username = request.form.get("username").strip()
        email = request.form.get("email").strip()

        existing = Admin.query.filter(
            ((Admin.username == username) | (Admin.email == email)) &
            (Admin.id != admin.id)
        ).first()

        if existing:
            flash("Username or Email already exists!", "danger")
            return redirect(url_for("edit_account"))

        admin.username = username
        admin.email = email

        db.session.commit()

        session["admin"] = username

        flash("Account updated successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("edit_account.html", admin=admin)

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "admin" not in session:
        return redirect(url_for("login"))

    return render_template("change_password.html")

@app.route("/about")
def about():

    if "admin" not in session:
        return redirect(url_for("login"))

    return render_template("about.html")

@app.route("/download-report", methods=["POST"])
def download_report():

    if "admin" not in session:
        return redirect(url_for("login"))

    admin = Admin.query.filter_by(
        username=session["admin"]
    ).first()

    course = request.form.get("course")
    semester = request.form.get("semester")
    gender = request.form.get("gender")
    file_type = request.form.get("file_type")

    query = Student.query.filter_by(admin_id=admin.id)

    if course != "All":
        query = query.filter_by(course=course)

    if semester != "All":
        query = query.filter_by(semester=semester)

    if gender != "All":
        query = query.filter_by(gender=gender)

    students = query.all()

    # ==========================
    # EXCEL REPORT
    # ==========================

    if file_type == "excel":

        wb = Workbook()
        ws = wb.active
        ws.title = "Students Report"

        ws.append([
            "ID",
            "Name",
            "Roll No",
            "Email",
            "Phone",
            "Course",
            "Semester",
            "Gender",
            "Address",
            "DOB",
            "Admission Date",
            "Status"
        ])

        for s in students:

            ws.append([
                s.id,
                s.name,
                s.roll_no,
                s.email,
                s.phone,
                s.course,
                s.semester,
                s.gender,
                s.address,
                s.dob.strftime("%d-%m-%Y") if s.dob else "",
                s.admission_date.strftime("%d-%m-%Y") if s.admission_date else "",
                s.status
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(
            output,
            download_name="Student_Report.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # ==========================
    # PDF REPORT
    # ==========================

    elif file_type == "pdf":

        output = io.BytesIO()

        pdf = SimpleDocTemplate(
            output,
            pagesize=A4
        )

        data = [[
            "ID",
            "Name",
            "Roll No",
            "Course",
            "Semester",
            "Status"
        ]]

        for s in students:

            data.append([
                s.id,
                s.name,
                s.roll_no,
                s.course,
                s.semester,
                s.status
            ])

        table = Table(data)

        table.setStyle(TableStyle([

            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),

            ("GRID", (0,0), (-1,-1), 1, colors.black),

            ("BACKGROUND", (0,1), (-1,-1), colors.beige),

            ("ALIGN", (0,0), (-1,-1), "CENTER"),

            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

            ("BOTTOMPADDING", (0,0), (-1,0), 10),

        ]))

        pdf.build([table])

        output.seek(0)

        return send_file(
            output,
            download_name="Student_Report.pdf",
            as_attachment=True,
            mimetype="application/pdf"
        )

    flash("Invalid file type selected.", "danger")
    return redirect(url_for("reports"))
    
@app.route("/reports")
def reports():     
    if "admin" not in session:
        return redirect(url_for("login"))
    courses = [
        "BCA",
        "BBA",
        "B.Tech",
        "MCA",
        "MBA",
        "B.Com",
        "B.Sc"
    ]
    semesters = [
        "1", "2", "3", "4", "5", "6", "7", "8"
    ]
    return render_template(
        "reports.html",
        courses=courses,
        semesters=semesters
    )
@app.route("/student/<int:id>")
def student_profile(id):

    if "admin" not in session:
        return redirect(url_for("login"))
    admin = Admin.query.filter_by(
    username=session["admin"]
).first()
    student = Student.query.filter_by(
    id=id,
    admin_id=admin.id
).first_or_404()

    return render_template(
        "student_profile.html",
        student=student
    )
@app.route("/student-pdf/<int:id>")
def student_pdf(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    admin = Admin.query.filter_by(
        username=session["admin"]
    ).first()

    student = Student.query.filter_by(
        id=id,
        admin_id=admin.id
    ).first_or_404()

    return f"PDF for {student.name}"
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        admin = Admin.query.filter_by(email=email).first()

        if not admin:
            flash("Email not found!", "danger")
            return redirect(url_for("forgot_password"))

        # Generate 6 digit OTP
        otp = random.randint(100000, 999999)

        # Store in session
        session["reset_email"] = email
        session["otp"] = str(otp)

        # Send Email
        msg = Message(
            "Password Reset OTP",
            recipients=[email]
        )

        msg.body = f"""
Hello,

Your OTP is: {otp}

It is valid for one use only.

StudentSphere
"""

        mail.send(msg)

        flash("OTP sent successfully!", "success")

        return redirect(url_for("verify_otp"))
    return render_template("forgot_password.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():

    if request.method == "POST":

        entered_otp = request.form.get("otp")

        if entered_otp == session.get("otp"):
            return redirect(url_for("reset_password"))

        flash("Invalid OTP!", "danger")
        return redirect(url_for("verify_otp"))

    return render_template("verify_otp.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():

    if "reset_email" not in session:
        flash("Session expired!", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("reset_password"))

        admin = Admin.query.filter_by(
            email=session["reset_email"]
        ).first()

        admin.set_password(password)

        db.session.commit()

        session.pop("otp", None)
        session.pop("reset_email", None)

        flash("Password Updated Successfully!", "success")

        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/test-mail")
def test_mail():

    msg = Message(
        "Test Email",
        recipients=["yourgmail@gmail.com"]
    )

    msg.body = "Congratulations! Flask Mail is working."

    mail.send(msg)

    return "Email Sent Successfully!"

@app.route("/import-students", methods=["GET", "POST"])
def import_students():

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Please select a file", "danger")
            return redirect(url_for("import_students"))

        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)

        elif file.filename.endswith(".csv"):
            df = pd.read_csv(file)

        else:
            flash("Only Excel or CSV files are allowed", "danger")
            return redirect(url_for("import_students"))

        admin = Admin.query.filter_by(
            username=session["admin"]
        ).first()

        for _, row in df.iterrows():

            student = Student(
                name=row["Name"],
                roll_no=row["Roll No"],
                email=row["Email"],
                phone=row["Phone"],
                course=row["Course"],
                semester=str(row["Semester"]),
                gender=row["Gender"],
                address=row["Address"],
                admin_id=admin.id
            )

            db.session.add(student)

        db.session.commit()

        flash("Students Imported Successfully!", "success")
        return redirect(url_for("students"))

    return render_template("import_students.html")

if __name__ == "__main__":
    app.run(debug=True)