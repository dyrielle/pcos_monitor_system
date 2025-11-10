from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db, login_manager

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("StudentProfile", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    degree_program = db.Column(db.String(120))
    consent = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="profile")
    academic_records = db.relationship("AcademicRecord", back_populates="profile", cascade="all, delete-orphan")
    survey_responses = db.relationship("SurveyResponse", back_populates="profile", cascade="all, delete-orphan")

    clinical_diagnosis = db.Column(db.String(50))
    pcos_awareness_score = db.Column(db.Float)
    pcos_symptoms_score = db.Column(db.Float)
    academic_pressure_score = db.Column(db.Float)

    # Awareness (5)
    awareness_1 = db.Column(db.Integer)
    awareness_2 = db.Column(db.Integer)
    awareness_3 = db.Column(db.Integer)
    awareness_4 = db.Column(db.Integer)
    awareness_5 = db.Column(db.Integer)

    # Academic Pressure (3)
    academic_1 = db.Column(db.Integer)
    academic_2 = db.Column(db.Integer)
    academic_3 = db.Column(db.Integer)

    # Symptoms (5)
    symptoms_1 = db.Column(db.Integer)
    symptoms_2 = db.Column(db.Integer)
    symptoms_3 = db.Column(db.Integer)
    symptoms_4 = db.Column(db.Integer)
    symptoms_5 = db.Column(db.Integer)

class AcademicRecord(db.Model):
    __tablename__ = "academic_records"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    term = db.Column(db.String(50))
    gpa = db.Column(db.Float)
    attendance_percent = db.Column(db.Float)
    study_hours_per_week = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("StudentProfile", back_populates="academic_records")


class SurveyResponse(db.Model):
    __tablename__ = "survey_responses"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    fatigue = db.Column(db.Integer)
    irregular_menstruation = db.Column(db.Boolean)
    mood_swings = db.Column(db.Integer)
    acne = db.Column(db.Boolean)
    sleep_quality = db.Column(db.Integer)
    perceived_academic_stress = db.Column(db.Integer)
    notes = db.Column(db.Text)

    profile = db.relationship("StudentProfile", back_populates="survey_responses")