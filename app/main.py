from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .extensions import db
from .models import StudentProfile, AcademicRecord, SurveyResponse

main_bp = Blueprint("main", __name__, template_folder="templates")


############# FORCE BASELINE COMPLETION CHECK #############
def require_baseline():
    if request.endpoint in ["main.index", "main.profile_setup"]:
        return
    if current_user.is_authenticated and not current_user.is_admin:
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

        # Awareness (only 5 items collected in form)
        profile.awareness_1 = int(request.form.get("awareness_1"))
        profile.awareness_2 = int(request.form.get("awareness_2"))
        profile.awareness_3 = int(request.form.get("awareness_3"))
        profile.awareness_4 = int(request.form.get("awareness_4"))
        profile.awareness_5 = int(request.form.get("awareness_5"))
        # Items 6, 7, 8 are not collected in this form - set to None or skip

        # Academic Pressure (3 items)
        profile.academic_1 = int(request.form.get("academic_1"))
        profile.academic_2 = int(request.form.get("academic_2"))
        profile.academic_3 = int(request.form.get("academic_3"))

        # Symptoms (only 5 items collected in form)
        profile.symptoms_1 = int(request.form.get("symptoms_1"))
        profile.symptoms_2 = int(request.form.get("symptoms_2"))
        profile.symptoms_3 = int(request.form.get("symptoms_3"))
        profile.symptoms_4 = int(request.form.get("symptoms_4"))
        profile.symptoms_5 = int(request.form.get("symptoms_5"))
        # Item 6 and fatigue_sleep_item are not collected in this form

        # Composite computed means (SIMPLIFIED FORMULA based on available data)
        # Awareness: use only items 1-5 that we have
        profile.pcos_awareness_score = (
            profile.awareness_1 + 
            profile.awareness_2 + 
            profile.awareness_3 + 
            profile.awareness_4 + 
            profile.awareness_5
        ) / 5
        
        # Academic Pressure: items 1, 2, 3
        profile.academic_pressure_score = (
            profile.academic_1 + 
            profile.academic_2 + 
            profile.academic_3
        ) / 3
        
        # Symptoms: use only items 1-5 that we have
        profile.pcos_symptoms_score = (
            profile.symptoms_1 + 
            profile.symptoms_2 + 
            profile.symptoms_3 + 
            profile.symptoms_4 + 
            profile.symptoms_5
        ) / 5

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
        profile = StudentProfile(user_id=current_user.id, data_source='manual')
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

        # NEW: Comprehensive PCOS Symptoms
        # 1. Reproductive / Menstrual
        irregular_cycles = request.form.get("irregular_cycles", type=int)
        oligomenorrhea = request.form.get("oligomenorrhea") == "on"
        amenorrhea = request.form.get("amenorrhea") == "on"
        heavy_menstruation = request.form.get("heavy_menstruation") == "on"
        pelvic_pain = request.form.get("pelvic_pain", type=int)
        
        # 2. Hormonal / Hyperandrogenism
        acne_severity = request.form.get("acne_severity", type=int)
        hirsutism = request.form.get("hirsutism", type=int)
        alopecia = request.form.get("alopecia") == "on"
        oily_skin = request.form.get("oily_skin", type=int)
        
        # 3. Metabolic
        weight_gain = request.form.get("weight_gain", type=int)
        insulin_resistance = request.form.get("insulin_resistance") == "on"
        elevated_blood_sugar = request.form.get("elevated_blood_sugar") == "on"
        acanthosis_nigricans = request.form.get("acanthosis_nigricans") == "on"
        
        # 4. Emotional / Psychological
        mood_swings_severity = request.form.get("mood_swings_severity", type=int)
        anxiety = request.form.get("anxiety", type=int)
        depression = request.form.get("depression", type=int)
        sleep_disturbances = request.form.get("sleep_disturbances", type=int)
        
        # 5. Skin-Related
        skin_tags = request.form.get("skin_tags") == "on"
        dark_patches = request.form.get("dark_patches") == "on"
        persistent_acne = request.form.get("persistent_acne") == "on"
        
        # 6. Other General
        fatigue_severity = request.form.get("fatigue_severity", type=int)
        low_energy = request.form.get("low_energy", type=int)
        sugar_cravings = request.form.get("sugar_cravings", type=int)

        sr = SurveyResponse(
            profile_id=profile.id,
            data_source='manual',  # Tag as manual/test account submission
            # Legacy fields
            fatigue=fatigue or 0, 
            irregular_menstruation=irregular,
            mood_swings=mood or 0, 
            acne=acne, 
            sleep_quality=sleepq or 0,
            perceived_academic_stress=stress or 0, 
            notes=notes,
            # New comprehensive symptoms
            irregular_cycles=irregular_cycles,
            oligomenorrhea=oligomenorrhea,
            amenorrhea=amenorrhea,
            heavy_menstruation=heavy_menstruation,
            pelvic_pain=pelvic_pain,
            acne_severity=acne_severity,
            hirsutism=hirsutism,
            alopecia=alopecia,
            oily_skin=oily_skin,
            weight_gain=weight_gain,
            insulin_resistance_symptoms=insulin_resistance,
            elevated_blood_sugar=elevated_blood_sugar,
            acanthosis_nigricans=acanthosis_nigricans,
            mood_swings_severity=mood_swings_severity,
            anxiety=anxiety,
            depression=depression,
            sleep_disturbances=sleep_disturbances,
            skin_tags=skin_tags,
            dark_patches=dark_patches,
            persistent_acne=persistent_acne,
            fatigue_severity=fatigue_severity,
            low_energy=low_energy,
            sugar_cravings=sugar_cravings
        )
        db.session.add(sr)

        db.session.commit()
        flash("Data submitted successfully!", "success")
        return redirect(url_for("main.submit_data"))

    return render_template("submit_data.html", profile=profile)


@main_bp.route("/my-dashboard")
@login_required
def student_dashboard():
    """Individual student dashboard showing personal health and academic trends."""
    
    from datetime import datetime
    import pandas as pd
    import numpy as np
    
    # Get current student's profile
    profile = current_user.profile
    
    if not profile:
        flash("Please complete your profile setup first.", "warning")
        return redirect(url_for("main.profile_setup"))
    
    # --- Personal Profile Data ---
    personal_data = {
        "name": profile.name or "Student",
        "age": profile.age,
        "degree_program": profile.degree_program,
        "clinical_diagnosis": profile.clinical_diagnosis or "Not specified",
        "awareness_score": profile.pcos_awareness_score,
        "academic_pressure_score": profile.academic_pressure_score,
        "symptoms_score": profile.pcos_symptoms_score
    }
    
    # --- Academic Records Timeline ---
    academic_records = AcademicRecord.query.filter_by(profile_id=profile.id).order_by(AcademicRecord.created_at).all()
    
    academic_timeline = []
    for record in academic_records:
        academic_timeline.append({
            "date": record.created_at.strftime("%Y-%m-%d"),
            "term": record.term or "N/A",
            "gpa": record.gpa,
            "attendance": record.attendance_percent,
            "study_hours": record.study_hours_per_week
        })
    
    # Academic averages
    academic_stats = {
        "avg_gpa": np.mean([r.gpa for r in academic_records if r.gpa]) if academic_records else None,
        "avg_attendance": np.mean([r.attendance_percent for r in academic_records if r.attendance_percent]) if academic_records else None,
        "avg_study_hours": np.mean([r.study_hours_per_week for r in academic_records if r.study_hours_per_week]) if academic_records else None,
        "total_records": len(academic_records)
    }
    
    # --- Survey Responses Timeline ---
    survey_responses = SurveyResponse.query.filter_by(profile_id=profile.id).order_by(SurveyResponse.date).all()
    
    survey_timeline = []
    for survey in survey_responses:
        survey_timeline.append({
            "date": survey.date.strftime("%Y-%m-%d"),
            "fatigue": survey.fatigue,
            "mood_swings": survey.mood_swings,
            "sleep_quality": survey.sleep_quality,
            "academic_stress": survey.perceived_academic_stress,
            "irregular_menstruation": survey.irregular_menstruation,
            "acne": survey.acne
        })
    
    # Survey averages
    survey_stats = {
        "avg_fatigue": np.mean([s.fatigue for s in survey_responses if s.fatigue]) if survey_responses else None,
        "avg_mood": np.mean([s.mood_swings for s in survey_responses if s.mood_swings]) if survey_responses else None,
        "avg_sleep": np.mean([s.sleep_quality for s in survey_responses if s.sleep_quality]) if survey_responses else None,
        "avg_stress": np.mean([s.perceived_academic_stress for s in survey_responses if s.perceived_academic_stress]) if survey_responses else None,
        "total_surveys": len(survey_responses)
    }
    
    # --- Cohort Comparison (Anonymized Averages) ---
    # Get all profiles except current user
    all_profiles = StudentProfile.query.filter(StudentProfile.id != profile.id).all()
    
    cohort_stats = {
        "cohort_size": len(all_profiles),
        "avg_awareness": None,
        "avg_academic_pressure": None,
        "avg_symptoms": None
    }
    
    if all_profiles:
        cohort_stats["avg_awareness"] = np.mean([p.pcos_awareness_score for p in all_profiles if p.pcos_awareness_score])
        cohort_stats["avg_academic_pressure"] = np.mean([p.academic_pressure_score for p in all_profiles if p.academic_pressure_score])
        cohort_stats["avg_symptoms"] = np.mean([p.pcos_symptoms_score for p in all_profiles if p.pcos_symptoms_score])
    
    # Format cohort stats to 2 decimal places
    for key in ["avg_awareness", "avg_academic_pressure", "avg_symptoms"]:
        if cohort_stats[key] is not None:
            cohort_stats[key] = round(cohort_stats[key], 2)
    
    # Format personal stats to 2 decimal places
    for key in ["avg_gpa", "avg_attendance", "avg_study_hours"]:
        if academic_stats[key] is not None:
            academic_stats[key] = round(academic_stats[key], 2)
    
    for key in ["avg_fatigue", "avg_mood", "avg_sleep", "avg_stress"]:
        if survey_stats[key] is not None:
            survey_stats[key] = round(survey_stats[key], 2)
    
    # --- Last Submission Date ---
    last_submission = None
    if survey_responses:
        last_submission = survey_responses[-1].date.strftime("%B %d, %Y")
    
    # --- Latest Symptoms for Radar Chart ---
    latest_symptoms = None
    if survey_responses:
        latest = survey_responses[-1]
        latest_symptoms = {
            "fatigue": latest.fatigue or 0,
            "mood": latest.mood_swings or 0,
            "sleep": latest.sleep_quality or 0,
            "stress": latest.perceived_academic_stress or 0,
            "irregular": 3 if latest.irregular_menstruation else 0,
            "acne": 3 if latest.acne else 0
        }
    
    # --- Health Score Calculation ---
    health_score = None
    if survey_responses:
        # Calculate health score (0-100, higher is better)
        # Invert scores since lower fatigue/stress/mood swings is better
        avg_fatigue = survey_stats["avg_fatigue"] or 3
        avg_mood = survey_stats["avg_mood"] or 3
        avg_sleep = survey_stats["avg_sleep"] or 3  # Higher sleep quality is better
        avg_stress = survey_stats["avg_stress"] or 3
        
        # Calculate score: sleep quality counts positive, others count negative
        health_score = round(
            ((5 - avg_fatigue) * 20 +  # 0-20 points
             (5 - avg_mood) * 20 +      # 0-20 points
             avg_sleep * 20 +            # 0-20 points (higher is better)
             (5 - avg_stress) * 20),     # 0-20 points
            1
        )
    
    return render_template("student_dashboard.html",
                          personal_data=personal_data,
                          academic_timeline=academic_timeline,
                          academic_stats=academic_stats,
                          survey_timeline=survey_timeline,
                          survey_stats=survey_stats,
                          cohort_stats=cohort_stats,
                          last_submission=last_submission,
                          latest_symptoms=latest_symptoms,
                          health_score=health_score)


@main_bp.route("/api/profile/<int:profile_id>/data")
@login_required
def profile_data(profile_id):
    profile = StudentProfile.query.get_or_404(profile_id)
    academics = [{"term": a.term, "gpa": a.gpa, "attendance": a.attendance_percent, "study_hours": a.study_hours_per_week}
                 for a in profile.academic_records]
    surveys = [{"date": s.date.isoformat(), "fatigue": s.fatigue, "mood": s.mood_swings, "stress": s.perceived_academic_stress}
               for s in profile.survey_responses]
    return jsonify({"academics": academics, "surveys": surveys})


@main_bp.route("/predict-pcos")
@login_required
def predict_pcos():
    """PCOS prediction page using Random Forest ML model based on comprehensive symptoms"""
    from .ml_service import model_exists, predict_pcos, get_recommendations
    from .models import SurveyResponse
    
    # Check if user is admin
    if current_user.is_admin:
        flash("PCOS prediction is only available for students.", "warning")
        return redirect(url_for("main.index"))
    
    # Get current student's profile
    profile = current_user.profile
    
    if not profile:
        flash("Please complete your profile setup first.", "warning")
        return redirect(url_for("main.profile_setup"))
    
    # Check if student has submitted symptom data (REQUIRED for prediction)
    latest_survey = SurveyResponse.query.filter_by(profile_id=profile.id)\
        .order_by(SurveyResponse.date.desc())\
        .first()
    
    if not latest_survey:
        flash("Please complete the 'Submit Data' form first. The prediction requires your comprehensive PCOS symptom information.", "warning")
        return redirect(url_for("main.submit_data"))
    
    # Check if model exists
    if not model_exists():
        flash("Prediction model is not available yet. The system is collecting training data from student responses.", "warning")
        return redirect(url_for("main.index"))
    
    try:
        # Make prediction based on comprehensive symptoms
        prediction_result = predict_pcos(profile)
        
        # Get recommendations
        recommendations = get_recommendations(prediction_result, profile)
        
        # Prepare context data
        context = {
            "profile": profile,
            "prediction": prediction_result,
            "recommendations": recommendations,
            "survey_response": latest_survey,  # Add survey data for detailed symptom display
            "personal_data": {
                "name": profile.name or "Student",
                "age": profile.age,
                "clinical_diagnosis": profile.clinical_diagnosis or "Not specified"
            }
        }
        
        return render_template("prediction_result.html", **context)
        
    except ValueError as e:
        # Specific error for missing survey data
        flash(f"{str(e)}", "warning")
        return redirect(url_for("main.submit_data"))
    except Exception as e:
        flash(f"Error making prediction: {str(e)}", "error")
        import traceback
        traceback.print_exc()
        return redirect(url_for("main.index"))