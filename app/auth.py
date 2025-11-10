from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from .extensions import db, mail
from .models import User, StudentProfile
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder="templates")

# --- Helpers ---------------------------------------------------------------

def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=current_app.config["SECRET_KEY"],
        salt="pcos-reset-salt"
    )

def _send_reset_email(to_email: str, token: str) -> None:
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    subject = "Password Reset — University Research Portal — PCOS Monitor"
    body = (
        "You requested a password reset for your PCOS Monitor account.\n\n"
        f"Click the link below to set a new password (valid for 1 hour):\n{reset_url}\n\n"
        "If you did not request this, please ignore this email."
    )
    msg = Message(subject=subject, recipients=[to_email], body=body)
    mail.send(msg)

# --- Registration ----------------------------------------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")

        if User.query.filter_by(email=email).first():
            flash("That email is already registered.", "warning")
            return redirect(url_for("auth.register"))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        profile = StudentProfile(user_id=user.id, name=name)
        db.session.add(profile)
        db.session.commit()

        flash("Account created — please login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

# --- Login / Logout --------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in.", "success")
            return redirect(url_for("main.index"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.index"))

# --- Forgot / Reset Password ----------------------------------------------

@auth_bp.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("If that email exists, a reset link has been sent.", "info")
            return redirect(url_for("auth.login"))

        token = _serializer().dumps(email)
        try:
            _send_reset_email(email, token)
            flash("Check your email for a password reset link (valid for 1 hour).", "success")
        except Exception as e:
            # Keep error generic to users
            flash("Could not send email. Please contact the admin.", "danger")
            current_app.logger.exception(e)
        return redirect(url_for("auth.login"))
    return render_template("forgot_password.html")

@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = _serializer().loads(token, max_age=3600)  # 1 hour
    except SignatureExpired:
        flash("Reset link expired. Please request a new one.", "warning")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first_or_404()

    if request.method == "POST":
        pw1 = request.form.get("password", "")
        pw2 = request.form.get("confirm_password", "")
        if not pw1 or pw1 != pw2:
            flash("Passwords must match.", "warning")
            return redirect(request.url)
        user.set_password(pw1)
        db.session.commit()
        flash("Password updated. You can now login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", email=email)