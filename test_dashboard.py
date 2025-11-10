"""Test script for student dashboard backend"""
from app import create_app
from app.models import User, StudentProfile, AcademicRecord, SurveyResponse
import numpy as np

app = create_app()

with app.app_context():
    print("=" * 60)
    print("TEST 1: User and Profile Data")
    print("=" * 60)
    
    user = User.query.first()
    if user:
        profile = user.profile
        print(f"✓ User: {user.email}")
        print(f"✓ Profile: {profile.name if profile else 'No profile'}")
        print(f"✓ Academic records: {len(profile.academic_records) if profile else 0}")
        print(f"✓ Survey responses: {len(profile.survey_responses) if profile else 0}")
    else:
        print("✗ No users in database - create one first")
    
    print("\n" + "=" * 60)
    print("TEST 2: Academic Statistics Calculation")
    print("=" * 60)
    
    profile = StudentProfile.query.first()
    if profile:
        records = AcademicRecord.query.filter_by(profile_id=profile.id).all()
        if records:
            avg_gpa = np.mean([r.gpa for r in records if r.gpa])
            avg_attendance = np.mean([r.attendance_percent for r in records if r.attendance_percent])
            avg_study = np.mean([r.study_hours_per_week for r in records if r.study_hours_per_week])
            
            print(f"✓ Total records: {len(records)}")
            print(f"✓ Average GPA: {round(avg_gpa, 2) if not np.isnan(avg_gpa) else 'N/A'}")
            print(f"✓ Average Attendance: {round(avg_attendance, 2) if not np.isnan(avg_attendance) else 'N/A'}%")
            print(f"✓ Average Study Hours: {round(avg_study, 2) if not np.isnan(avg_study) else 'N/A'}")
        else:
            print("✗ No academic records found")
    else:
        print("✗ No profiles found")
    
    print("\n" + "=" * 60)
    print("TEST 3: Survey Statistics Calculation")
    print("=" * 60)
    
    if profile:
        surveys = SurveyResponse.query.filter_by(profile_id=profile.id).all()
        if surveys:
            avg_fatigue = np.mean([s.fatigue for s in surveys if s.fatigue])
            avg_mood = np.mean([s.mood_swings for s in surveys if s.mood_swings])
            avg_sleep = np.mean([s.sleep_quality for s in surveys if s.sleep_quality])
            avg_stress = np.mean([s.perceived_academic_stress for s in surveys if s.perceived_academic_stress])
            
            print(f"✓ Total surveys: {len(surveys)}")
            print(f"✓ Average Fatigue: {round(avg_fatigue, 2) if not np.isnan(avg_fatigue) else 'N/A'}")
            print(f"✓ Average Mood: {round(avg_mood, 2) if not np.isnan(avg_mood) else 'N/A'}")
            print(f"✓ Average Sleep: {round(avg_sleep, 2) if not np.isnan(avg_sleep) else 'N/A'}")
            print(f"✓ Average Stress: {round(avg_stress, 2) if not np.isnan(avg_stress) else 'N/A'}")
        else:
            print("✗ No survey responses found")
    
    print("\n" + "=" * 60)
    print("TEST 4: Cohort Statistics (Anonymized)")
    print("=" * 60)
    
    all_profiles = StudentProfile.query.all()
    if len(all_profiles) > 1:
        cohort = all_profiles[1:]  # Exclude first profile (simulating current user)
        
        awareness_scores = [p.pcos_awareness_score for p in cohort if p.pcos_awareness_score]
        academic_scores = [p.academic_pressure_score for p in cohort if p.academic_pressure_score]
        symptom_scores = [p.pcos_symptoms_score for p in cohort if p.pcos_symptoms_score]
        
        print(f"✓ Cohort size: {len(cohort)}")
        if awareness_scores:
            print(f"✓ Cohort avg awareness: {round(np.mean(awareness_scores), 2)}")
        if academic_scores:
            print(f"✓ Cohort avg academic pressure: {round(np.mean(academic_scores), 2)}")
        if symptom_scores:
            print(f"✓ Cohort avg symptoms: {round(np.mean(symptom_scores), 2)}")
    else:
        print(f"✗ Only {len(all_profiles)} profile(s) found - need at least 2 for cohort comparison")
    
    print("\n" + "=" * 60)
    print("TEST 5: Route Registration")
    print("=" * 60)
    
    dashboard_routes = [str(rule) for rule in app.url_map.iter_rules() if 'my-dashboard' in str(rule)]
    if dashboard_routes:
        print(f"✓ Dashboard route found: {dashboard_routes[0]}")
    else:
        print("✗ Dashboard route not found")
    
    print("\n" + "=" * 60)
    print("All Tests Complete!")
    print("=" * 60)
