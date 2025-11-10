from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .extensions import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")


@admin_bp.route("/")
@login_required
def admin_home():
    if not current_user.is_admin:
        return "Access denied", 403
    return render_template("admin_home.html")


@admin_bp.route("/data")
@login_required
def view_data():
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile, AcademicRecord, SurveyResponse

    profiles = StudentProfile.query.all()
    academic = AcademicRecord.query.all()
    surveys = SurveyResponse.query.all()

    return render_template("admin_data.html", profiles=profiles, academic=academic, surveys=surveys)


@admin_bp.route("/export_csv")
@login_required
def export_csv():
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile, AcademicRecord, SurveyResponse
    import pandas as pd
    from flask import Response

    surveys = SurveyResponse.query.all()
    df_surveys = pd.DataFrame([s.__dict__ for s in surveys])
    df_surveys.drop(columns=["_sa_instance_state"], inplace=True, errors="ignore")

    csv = df_surveys.to_csv(index=False)

    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=pcos_dataset.csv"}
    )


@admin_bp.route("/profile/<int:profile_id>/edit", methods=["GET"])
@login_required
def edit_profile(profile_id):
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile
    profile = StudentProfile.query.get_or_404(profile_id)
    return render_template("admin_edit_profile.html", profile=profile)


@admin_bp.route("/profile/<int:profile_id>/update", methods=["POST"])
@login_required
def update_profile(profile_id):
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile
    from .extensions import db
    profile = StudentProfile.query.get_or_404(profile_id)

    profile.clinical_diagnosis = request.form.get("clinical_diagnosis") or None

    def to_float(value):
        try:
            return float(value) if value not in (None, "",) else None
        except:
            return None

    profile.pcos_awareness_score = to_float(request.form.get("pcos_awareness_score"))
    profile.pcos_symptoms_score = to_float(request.form.get("pcos_symptoms_score"))
    profile.academic_pressure_score = to_float(request.form.get("academic_pressure_score"))

    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("admin.edit_profile", profile_id=profile.id))


@admin_bp.route("/analytics")
@login_required
def analytics_page():
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile, AcademicRecord
    import pandas as pd
    from scipy.stats import spearmanr

    profiles = StudentProfile.query.all()

    df = pd.DataFrame([{
        "diagnosis": p.clinical_diagnosis,
        "awareness": p.pcos_awareness_score,
        "academic_pressure": p.academic_pressure_score,
        "symptoms": p.pcos_symptoms_score,
        "profile_id": p.id
    } for p in profiles])

    gpa_data = AcademicRecord.query.all()
    df_gpa = pd.DataFrame([{
        "profile_id": r.profile_id,
        "gpa": r.gpa
    } for r in gpa_data])

    if not df_gpa.empty:
        df_gpa = df_gpa.groupby("profile_id")["gpa"].mean().reset_index()
        df = df.merge(df_gpa, on="profile_id", how="left")

    corr_sym_acad = None
    corr_sym_gpa = None

    if df["symptoms"].notnull().sum() > 1 and df["academic_pressure"].notnull().sum() > 1:
        corr_sym_acad, _ = spearmanr(df["symptoms"], df["academic_pressure"], nan_policy="omit")

    if df["symptoms"].notnull().sum() > 1 and df["gpa"].notnull().sum() > 1:
        corr_sym_gpa, _ = spearmanr(df["symptoms"], df["gpa"], nan_policy="omit")

    group_means = df.groupby("diagnosis")[["awareness", "academic_pressure", "symptoms"]].mean().reset_index()

    return render_template("admin_analytics.html",
                           group_means=group_means,
                           corr_sym_acad=corr_sym_acad,
                           corr_sym_gpa=corr_sym_gpa)


### FIXED CHARTS ROUTE BELOW ###
@admin_bp.route("/charts")
@login_required
def charts_page():
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile
    import pandas as pd

    profiles = StudentProfile.query.all()

    df = pd.DataFrame([{
        "profile_id": p.id,
        "diagnosis": p.clinical_diagnosis or "Not Diagnosed",
        "awareness": p.pcos_awareness_score,
        "academic_pressure": p.academic_pressure_score,
        "symptoms": p.pcos_symptoms_score
    } for p in profiles])

    rows = df.to_dict(orient="records") if not df.empty else []

    return render_template("admin_charts.html", rows=rows)