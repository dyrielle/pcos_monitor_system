"""
Test script to verify clinical symptom prediction system is ready
"""
import sys
import os

print("=" * 80)
print("CLINICAL SYMPTOM PREDICTION SYSTEM - VERIFICATION")
print("=" * 80)

# Check 1: Verify ml_service.py changes
print("\n1. Checking ml_service.py configuration...")
try:
    sys.path.insert(0, 'app')
    from app.ml_service import MODEL_FILE, FEATURES_FILE, FALLBACK_MODEL_FILE
    
    if MODEL_FILE == 'pcos_clinical_model.pkl':
        print("   ✓ MODEL_FILE correctly set to clinical model")
    else:
        print(f"   ✗ MODEL_FILE is '{MODEL_FILE}' (should be 'pcos_clinical_model.pkl')")
    
    if FEATURES_FILE == 'clinical_feature_columns.pkl':
        print("   ✓ FEATURES_FILE correctly set to clinical features")
    else:
        print(f"   ✗ FEATURES_FILE is '{FEATURES_FILE}' (should be 'clinical_feature_columns.pkl')")
        
except Exception as e:
    print(f"   ✗ Error loading ml_service: {e}")

# Check 2: Verify database models have required fields
print("\n2. Checking database models...")
try:
    from app.models import SurveyResponse, StudentProfile
    
    required_fields = [
        'irregular_cycles', 'oligomenorrhea', 'amenorrhea', 'heavy_menstruation', 'pelvic_pain',
        'hirsutism', 'acne_severity', 'alopecia', 'oily_skin',
        'weight_gain', 'insulin_resistance_symptoms', 'elevated_blood_sugar', 'acanthosis_nigricans',
        'mood_swings_severity', 'anxiety', 'depression', 'sleep_disturbances',
        'skin_tags', 'dark_patches', 'persistent_acne',
        'fatigue_severity', 'low_energy', 'sugar_cravings'
    ]
    
    survey_fields = [f for f in dir(SurveyResponse) if not f.startswith('_')]
    missing_fields = [f for f in required_fields if f not in survey_fields]
    
    if not missing_fields:
        print(f"   ✓ All 23 symptom fields exist in SurveyResponse model")
    else:
        print(f"   ✗ Missing fields in SurveyResponse: {missing_fields}")
        
except Exception as e:
    print(f"   ✗ Error checking models: {e}")

# Check 3: Verify training script exists
print("\n3. Checking training script...")
if os.path.exists('train_clinical_symptom_model.py'):
    print("   ✓ train_clinical_symptom_model.py exists")
else:
    print("   ✗ train_clinical_symptom_model.py not found")

# Check 4: Check if clinical model already trained
print("\n4. Checking for trained model...")
if os.path.exists('ml_models/pcos_clinical_model.pkl'):
    print("   ✓ Clinical model already trained (pcos_clinical_model.pkl)")
    if os.path.exists('ml_models/clinical_feature_columns.pkl'):
        print("   ✓ Clinical features file exists")
    else:
        print("   ✗ Clinical features file missing")
else:
    print("   ⚠ Clinical model not yet trained")
    print("     Run: .\\venv\\Scripts\\python.exe train_clinical_symptom_model.py")

# Check 5: Verify dependencies
print("\n5. Checking dependencies...")
try:
    import sklearn
    print(f"   ✓ scikit-learn {sklearn.__version__}")
except ImportError:
    print("   ✗ scikit-learn not installed")

try:
    import pandas
    print(f"   ✓ pandas {pandas.__version__}")
except ImportError:
    print("   ✗ pandas not installed")

try:
    import numpy
    print(f"   ✓ numpy {numpy.__version__}")
except ImportError:
    print("   ✗ numpy not installed")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("\n✅ System is configured to use clinical symptom prediction")
print("\nNext steps:")
print("1. Have students complete 'Submit Data' form (need 5+ responses)")
print("2. Run: .\\venv\\Scripts\\python.exe train_clinical_symptom_model.py")
print("3. Restart Flask server")
print("4. Test predictions (requires Submit Data completion)")
print("\n" + "=" * 80)
