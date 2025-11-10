from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .extensions import db
import pandas as pd
import io
from werkzeug.utils import secure_filename

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

    # Get page number from query parameter, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 5

    # Paginate profiles
    profiles_pagination = StudentProfile.query.paginate(page=page, per_page=per_page, error_out=False)
    profiles = profiles_pagination.items

    academic = AcademicRecord.query.all()
    surveys = SurveyResponse.query.all()

    return render_template("admin_data.html", profiles=profiles, academic=academic, surveys=surveys, pagination=profiles_pagination)


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


@admin_bp.route("/download_sample_csv")
@login_required
def download_sample_csv():
    if not current_user.is_admin:
        return "Access denied", 403

    from flask import Response
    
    # Create sample CSV with correct column structure
    sample_data = {
        "Consent": ["Yes"],
        "Age": [19],
        "Year Level": [2],
        "Clinical Diagnosis": ["No"],
        "Interview Willing": ["No"],
        "Suspect PCOS": ["Not sure"],
        "Familiar PCOS": [4],
        "Know Symptoms Irregular": [5],
        "Know Symptoms Acne": [4],
        "Know Symptoms Weight": [4],
        "Know Symptoms Hair": [4],
        "Understand Health Impact": [5],
        "Aware Treatments": [3],
        "Believe Academic Impact": [4],
        "Academic Pressure": [4],
        "Stress Affects Health": [4],
        "Fatigue Affects Concentration": [4],
        "Performance Influenced Health": [4],
        "School Understanding": [3],
        "Symptoms Affect Work": [3],
        "Anxious Health Studies": [4],
        "Miss Deadlines Health": [2],
        "Unsupported Balance": [2],
        "What Know PCOS": ["PCOS is a hormonal disorder affecting women"],
        "How Cope Pressure": ["Taking breaks and prioritizing self-care"],
        "Support Needed": ["Understanding from professors and flexible deadlines"],
        "Uncertainty Effect": ["Causes stress and difficulty focusing"]
    }
    
    df_sample = pd.DataFrame(sample_data)
    csv_sample = df_sample.to_csv(index=False)
    
    return Response(
        csv_sample,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=pcos_sample_format.csv"}
    )


@admin_bp.route("/import_csv", methods=["POST"])
@login_required
def import_csv():
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403

    from .models import User, StudentProfile
    from flask import Response
    import pandas as pd
    import io
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a CSV"}), 400
    
    try:
        # Read CSV file
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_data = stream.read()
        df = pd.read_csv(io.StringIO(csv_data))
        
        # Validate CSV structure - check for minimum required columns
        required_columns = ["Age", "Year Level"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            return jsonify({
                "error": f"Missing required columns: {', '.join(missing_cols)}. Please download the sample CSV for reference."
            }), 400
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        # Column mapping for the survey data
        column_mapping = {
            "Consent To Participate I Have Read And Understood The Information Provided Above About This Research Study. I Voluntarily Agree To Participate, And I Understand That My Participation Is Voluntary, And I May Withdraw At Any Time Without Penalty. My Responses Will Remain Confidential And Will Only Be Used For Academic Purposes. No Personal Identifiers (Such As My Name) Will Appear In The Final Report. The Data I Provide Will Be Protected Under The Data Privacy Act Of 2012 (Ra 10173).": "Consent",
            "Do You Have A Clinical Diagnosis Of Pcos": "Clinical Diagnosis",
            "For Clinically Diagnosed, Are You Willing To Undergo A Thorough Interview (If Yes, Leave Your Fb_Email_Contact Number In \"Other\" Section).": "Interview Willing",
            "If No, Do You Think You May Have Pcos (Based On Symptoms You Experience)": "Suspect PCOS",
            "I Am Familiar With The Term Polycystic Ovary Syndrome (Pcos).": "Familiar PCOS",
            "I Know The Common Symptoms Of Pcos. Irregular Periods": "Know Symptoms Irregular",
            "I Know The Common Symptoms Of Pcos. Acne": "Know Symptoms Acne",
            "I Know The Common Symptoms Of Pcos. Weight Fluctuations": "Know Symptoms Weight",
            "I Know The Common Symptoms Of Pcos. Excessive Hair Growth": "Know Symptoms Hair",
            "I Understand That Pcos Can Affect Both Physical And Mental Health.": "Understand Health Impact",
            "I Am Aware Of The Possible Treatments_Management Strategies For Pcos.": "Aware Treatments",
            "I Believe Pcos Can Affect Academic Performance.": "Believe Academic Impact",
            "I Often Feel Academic Pressure Due To Heavy Workloads.": "Academic Pressure",
            "Stress From My Academic Environment Affects My Health And Well-Being.": "Stress Affects Health",
            "Fatigue Or Irregular Sleep Patterns Affect My Ability To Concentrate On Schoolwork.": "Fatigue Affects Concentration",
            "My Academic Performance Is Sometimes Influenced By My Physical Or Emotional Health.": "Performance Influenced Health",
            "Professors And School Administrators Are Understanding When Health Issues Affect My Performance.": "School Understanding",
            "I Sometimes Experience Symptoms (E.G., Fatigue, Irregular Menstruation, Mood Swings) That Affect My Academic Work.": "Symptoms Affect Work",
            "I Feel Anxious About How Health-Related Issues May Affect My Studies.": "Anxious Health Studies",
            "I Sometimes Miss Deadlines Or Classes Due To Health Struggles.": "Miss Deadlines Health",
            "I Feel Unsupported In Balancing My Health And Academic Responsibilities.": "Unsupported Balance",
        }
        
        # Rename columns if they exist
        df.rename(columns=column_mapping, inplace=True)
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Skip rows with no age data
                if pd.isna(row.get('Age')):
                    skipped_count += 1
                    continue
                
                # Generate unique email for this import entry
                email = f"import_{index}_{pd.Timestamp.now().timestamp()}@pcos.research"
                
                # Check if similar profile exists (by age and year level)
                age = int(row['Age']) if not pd.isna(row.get('Age')) else None
                year_level = str(row.get('Year Level', '')).strip() if not pd.isna(row.get('Year Level')) else None
                
                # Create or get user
                user = User.query.filter_by(email=email).first()
                if user:
                    skipped_count += 1
                    continue
                
                user = User(email=email, is_admin=False)
                user.set_password("imported123")  # Default password for imported records
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Helper function to safely convert to int
                def safe_int(value):
                    if pd.isna(value) or value == '' or value == 'No response':
                        return None
                    try:
                        return int(float(value))
                    except:
                        return None
                
                # Helper function to convert Yes/No to boolean
                def to_bool(value):
                    if pd.isna(value) or value == '':
                        return None
                    val_str = str(value).strip().lower()
                    if val_str in ['yes', 'y', '1', 'true']:
                        return True
                    elif val_str in ['no', 'n', '0', 'false']:
                        return False
                    return None
                
                # Create student profile
                profile = StudentProfile(
                    user_id=user.id,
                    name=f"Imported Student {index + 1}",
                    age=age,
                    degree_program=f"Year {year_level}" if year_level else None,
                    consent=True,
                    clinical_diagnosis=str(row.get('Clinical Diagnosis', '')).strip() if not pd.isna(row.get('Clinical Diagnosis')) else None,
                    
                    # Awareness scores (items 1-5)
                    awareness_1=safe_int(row.get('Familiar PCOS')),
                    awareness_2=safe_int(row.get('Know Symptoms Irregular')),
                    awareness_3=safe_int(row.get('Know Symptoms Acne')),
                    awareness_4=safe_int(row.get('Understand Health Impact')),
                    awareness_5=safe_int(row.get('Aware Treatments')),
                    
                    # Academic pressure scores (items 1-3)
                    academic_1=safe_int(row.get('Academic Pressure')),
                    academic_2=safe_int(row.get('Stress Affects Health')),
                    academic_3=safe_int(row.get('Fatigue Affects Concentration')),
                    
                    # Symptoms scores (items 1-5)
                    symptoms_1=safe_int(row.get('Performance Influenced Health')),
                    symptoms_2=safe_int(row.get('Symptoms Affect Work')),
                    symptoms_3=safe_int(row.get('Anxious Health Studies')),
                    symptoms_4=safe_int(row.get('Miss Deadlines Health')),
                    symptoms_5=safe_int(row.get('Unsupported Balance'))
                )
                
                # Calculate composite scores
                awareness_scores = [profile.awareness_1, profile.awareness_2, profile.awareness_3, 
                                   profile.awareness_4, profile.awareness_5]
                awareness_valid = [s for s in awareness_scores if s is not None]
                if awareness_valid:
                    profile.pcos_awareness_score = sum(awareness_valid) / len(awareness_valid)
                
                academic_scores = [profile.academic_1, profile.academic_2, profile.academic_3]
                academic_valid = [s for s in academic_scores if s is not None]
                if academic_valid:
                    profile.academic_pressure_score = sum(academic_valid) / len(academic_valid)
                
                symptoms_scores = [profile.symptoms_1, profile.symptoms_2, profile.symptoms_3,
                                  profile.symptoms_4, profile.symptoms_5]
                symptoms_valid = [s for s in symptoms_scores if s is not None]
                if symptoms_valid:
                    profile.pcos_symptoms_score = sum(symptoms_valid) / len(symptoms_valid)
                
                db.session.add(profile)
                created_count += 1
                
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
                skipped_count += 1
                continue
        
        # Commit all changes
        db.session.commit()
        
        message = f"Successfully imported CSV file."
        if errors:
            message += f" Some rows had errors and were skipped."
        
        return jsonify({
            "message": message,
            "created": created_count,
            "skipped": skipped_count,
            "errors": errors[:10]  # Return first 10 errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 500



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


@admin_bp.route("/profile/<int:profile_id>/delete", methods=["POST"])
@login_required
def delete_profile(profile_id):
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile, AcademicRecord, SurveyResponse, User
    from .extensions import db
    
    profile = StudentProfile.query.get_or_404(profile_id)
    
    # Delete associated academic records
    AcademicRecord.query.filter_by(profile_id=profile_id).delete()
    
    # Delete associated survey responses
    SurveyResponse.query.filter_by(profile_id=profile_id).delete()
    
    # Get the user_id before deleting the profile
    user_id = profile.user_id
    
    # Delete the student profile
    db.session.delete(profile)
    
    # Optionally delete the user account as well
    user = User.query.get(user_id)
    if user and not user.is_admin:  # Don't delete admin users
        db.session.delete(user)
    
    db.session.commit()
    flash("Student profile and associated data deleted successfully.", "success")
    return redirect(url_for("admin.view_data"))


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

    from .models import StudentProfile, AcademicRecord, SurveyResponse
    import pandas as pd
    import numpy as np

    profiles = StudentProfile.query.all()

    # Original data for scatter plots
    df_profiles = pd.DataFrame([{
        "profile_id": p.id,
        "diagnosis": p.clinical_diagnosis or "Not Diagnosed",
        "awareness": p.pcos_awareness_score,
        "academic_pressure": p.academic_pressure_score,
        "symptoms": p.pcos_symptoms_score
    } for p in profiles])

    rows = df_profiles.to_dict(orient="records") if not df_profiles.empty else []

    # NEW: Prepare data for correlation heatmap
    correlation_data = []
    for p in profiles:
        # Get academic averages
        academic_records = AcademicRecord.query.filter_by(profile_id=p.id).all()
        avg_gpa = np.mean([r.gpa for r in academic_records if r.gpa]) if academic_records else None
        avg_attendance = np.mean([r.attendance_percent for r in academic_records if r.attendance_percent]) if academic_records else None
        avg_study_hours = np.mean([r.study_hours_per_week for r in academic_records if r.study_hours_per_week]) if academic_records else None

        # Get survey averages
        surveys = SurveyResponse.query.filter_by(profile_id=p.id).all()
        avg_fatigue = np.mean([s.fatigue for s in surveys if s.fatigue]) if surveys else None
        avg_mood = np.mean([s.mood_swings for s in surveys if s.mood_swings]) if surveys else None
        avg_stress = np.mean([s.perceived_academic_stress for s in surveys if s.perceived_academic_stress]) if surveys else None

        correlation_data.append({
            "PCOS Awareness": p.pcos_awareness_score,
            "Academic Pressure": p.academic_pressure_score,
            "Symptoms": p.pcos_symptoms_score,
            "GPA": avg_gpa,
            "Attendance %": avg_attendance,
            "Study Hours/Week": avg_study_hours,
            "Fatigue": avg_fatigue,
            "Mood Swings": avg_mood,
            "Academic Stress": avg_stress
        })

    df_correlation = pd.DataFrame(correlation_data)
    
    # Compute correlation matrix
    correlation_matrix = None
    correlation_labels = []
    correlation_values = []
    
    if not df_correlation.empty:
        # Drop columns that are all NaN
        df_correlation = df_correlation.dropna(axis=1, how='all')
        
        # Compute correlation only if we have at least 2 variables and 2 samples
        if len(df_correlation.columns) >= 2 and len(df_correlation) >= 2:
            correlation_matrix = df_correlation.corr().round(3)
            correlation_labels = correlation_matrix.columns.tolist()
            correlation_values = correlation_matrix.values.tolist()

    # NEW: Diagnosis group heatmap data
    diagnosis_labels = []
    metric_labels = []
    diagnosis_values = []
    
    if not df_correlation.empty:
        # Add diagnosis column
        diagnosis_col = [p.clinical_diagnosis or "Not Specified" for p in profiles]
        df_with_diagnosis = df_correlation.copy()
        df_with_diagnosis['Diagnosis'] = diagnosis_col
        
        # Group by diagnosis and calculate means
        grouped = df_with_diagnosis.groupby('Diagnosis').mean()
        
        if not grouped.empty:
            diagnosis_labels = grouped.index.tolist()
            metric_labels = grouped.columns.tolist()
            diagnosis_values = grouped.values.tolist()

    return render_template("admin_charts.html", 
                          rows=rows,
                          correlation_labels=correlation_labels,
                          correlation_values=correlation_values,
                          diagnosis_labels=diagnosis_labels,
                          metric_labels=metric_labels,
                          diagnosis_values=diagnosis_values)


@admin_bp.route("/reports")
@login_required
def reports_page():
    """Display reports interface."""
    if not current_user.is_admin:
        return "Access denied", 403
    
    from .reports import ReportGenerator
    
    # Generate preview data
    generator = ReportGenerator()
    report_data = generator.generate_full_report_data()
    
    return render_template("admin_reports.html", report_data=report_data)


@admin_bp.route("/reports/generate-pdf")
@login_required
def generate_pdf_report():
    """Generate and download PDF report."""
    if not current_user.is_admin:
        return "Access denied", 403
    
    from .reports import ReportGenerator, PDFReportBuilder
    from flask import send_file
    import os
    import tempfile
    from datetime import datetime
    
    # Generate report data
    generator = ReportGenerator()
    report_data = generator.generate_full_report_data()
    
    # Create PDF in temporary directory
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PCOS_Research_Report_{timestamp}.pdf"
    filepath = os.path.join(temp_dir, filename)
    
    # Build PDF
    pdf_builder = PDFReportBuilder(report_data)
    pdf_builder.build_pdf(filepath)
    
    # Send file for download
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


@admin_bp.route("/reports/preview-data")
@login_required
def preview_report_data():
    """Preview report data as JSON (for debugging)."""
    if not current_user.is_admin:
        return "Access denied", 403
    
    from .reports import ReportGenerator
    
    generator = ReportGenerator()
    report_data = generator.generate_full_report_data()
    
    return jsonify(report_data)