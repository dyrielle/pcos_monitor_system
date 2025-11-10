from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .extensions import db
from .models import StudentProfile, AcademicRecord, SurveyResponse

main_bp = Blueprint("main", __name__, template_folder="templates")


############# FORCE BASELINE COMPLETION CHECK #############
def require_baseline():
    if request.endpoint in ["main.index", "main.profile_setup"]:
        return
    if current_user.is_authenticated:
        profile = current_user.profile
        if profile and profile.awareness_1 is None:
            return redirect(url_for("main.profile_setup"))


@main_bp.before_app_request
def before_request_func():
    return require_baseline()
############################################################


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/profile_setup", methods=["GET", "POST"])
@login_required
def profile_setup():
    profile = current_user.profile

    if request.method == "POST":
        profile.clinical_diagnosis = request.form.get("clinical_diagnosis")

        # Awareness
        profile.awareness_1 = int(request.form.get("awareness_1"))
        profile.awareness_2 = int(request.form.get("awareness_2"))
        profile.awareness_3 = int(request.form.get("awareness_3"))
        profile.awareness_4 = int(request.form.get("awareness_4"))
        profile.awareness_5 = int(request.form.get("awareness_5"))

        # Academic Pressure
        profile.academic_1 = int(request.form.get("academic_1"))
        profile.academic_2 = int(request.form.get("academic_2"))
        profile.academic_3 = int(request.form.get("academic_3"))

        # Symptoms
        profile.symptoms_1 = int(request.form.get("symptoms_1"))
        profile.symptoms_2 = int(request.form.get("symptoms_2"))
        profile.symptoms_3 = int(request.form.get("symptoms_3"))
        profile.symptoms_4 = int(request.form.get("symptoms_4"))
        profile.symptoms_5 = int(request.form.get("symptoms_5"))

        # composite computed means
        profile.pcos_awareness_score = (profile.awareness_1 + profile.awareness_2 + profile.awareness_3 + profile.awareness_4 + profile.awareness_5) / 5
        profile.academic_pressure_score = (profile.academic_1 + profile.academic_2 + profile.academic_3) / 3
        profile.pcos_symptoms_score = (profile.symptoms_1 + profile.symptoms_2 + profile.symptoms_3 + profile.symptoms_4 + profile.symptoms_5) / 5

        db.session.commit()
        flash("Baseline PCOS profile survey completed successfully.", "success")
        return redirect(url_for("main.index"))

    return render_template("profile_setup.html", profile=profile)


@main_bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit_data():

    # SAFETY AUTO-FIX: regenerate missing profile if data was deleted
    profile = current_user.profile
    if profile is None:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    if request.method == "POST":

        academic_year = request.form.get("academic_year")
        semester = request.form.get("semester")
        grading_period = request.form.get("grading_period")

        gpa = request.form.get("gpa", type=float)
        attendance = request.form.get("attendance", type=float)
        study_hours = request.form.get("study_hours", type=float)

        if academic_year and semester and grading_period:
            term = f"{academic_year} - {semester} - {grading_period}"
            ar = AcademicRecord(profile_id=profile.id, term=term, gpa=gpa or 0.0,
                                attendance_percent=attendance or 0.0, study_hours_per_week=study_hours or 0.0)
            db.session.add(ar)

        fatigue = request.form.get("fatigue", type=int)
        irregular = request.form.get("irregular") == "on"
        mood = request.form.get("mood", type=int)
        acne = request.form.get("acne") == "on"
        sleepq = request.form.get("sleepq", type=int)
        stress = request.form.get("stress", type=int)
        notes = request.form.get("notes")

        sr = SurveyResponse(profile_id=profile.id,
                            fatigue=fatigue or 0, irregular_menstruation=irregular,
                            mood_swings=mood or 0, acne=acne, sleep_quality=sleepq or 0,
                            perceived_academic_stress=stress or 0, notes=notes)
        db.session.add(sr)

        db.session.commit()
        flash("Data submitted successfully!", "success")
        return redirect(url_for("main.submit_data"))

    return render_template("submit_data.html", profile=profile)


@main_bp.route("/api/profile/<int:profile_id>/data")
@login_required
def profile_data(profile_id):
    profile = StudentProfile.query.get_or_404(profile_id)
    academics = [{"term": a.term, "gpa": a.gpa, "attendance": a.attendance_percent, "study_hours": a.study_hours_per_week}
                 for a in profile.academic_records]
    surveys = [{"date": s.date.isoformat(), "fatigue": s.fatigue, "mood": s.mood_swings, "stress": s.perceived_academic_stress}
               for s in profile.survey_responses]
    return jsonify({"academics": academics, "surveys": surveys})