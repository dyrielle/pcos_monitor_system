"""
Machine Learning Service for PCOS Prediction
Provides functions to load the trained model and make predictions
"""
import pickle
import os
import numpy as np
from pathlib import Path

# Model directory path
MODEL_DIR = Path(__file__).parent.parent / 'ml_models'

# Model file names - using CLINICAL SYMPTOM MODEL (23 comprehensive symptoms)
MODEL_FILE = 'pcos_clinical_model.pkl'
FEATURES_FILE = 'clinical_feature_columns.pkl'

# Global variables to store loaded model and features
_model = None
_feature_columns = None

def load_model():
    """Load the trained Random Forest model and feature columns"""
    global _model, _feature_columns
    
    if _model is None:
        model_path = MODEL_DIR / MODEL_FILE
        
        # Try loading clinical model first
        if not model_path.exists():
            raise FileNotFoundError(
                f"Clinical model not found. Please train the model first by running: "
                f"train_clinical_symptom_model.py (requires at least 5 student responses with Submit Data completed)"
            )
        
        with open(model_path, 'rb') as f:
            _model = pickle.load(f)
        print(f"Clinical model loaded from {model_path}")
    
    if _feature_columns is None:
        features_path = MODEL_DIR / FEATURES_FILE
        
        # Try loading clinical features first
        if not features_path.exists():
            raise FileNotFoundError(
                f"Clinical feature columns not found. Please train the model first by running: "
                f"train_clinical_symptom_model.py"
            )
        
        with open(features_path, 'rb') as f:
            _feature_columns = pickle.load(f)
        print(f"Clinical feature columns loaded from {features_path}")
    
    return _model, _feature_columns

def prepare_features_from_profile(profile):
    """
    Extract CLINICAL SYMPTOM features from student's survey responses
    
    Uses the 23 comprehensive PCOS symptoms from the Submit Data form.
    
    Args:
        profile: StudentProfile database model instance
        
    Returns:
        numpy array of 23 clinical symptom features
    """
    from app.models import SurveyResponse
    
    _, feature_columns = load_model()
    
    # Get the most recent survey response for this student
    latest_survey = SurveyResponse.query.filter_by(profile_id=profile.id)\
        .order_by(SurveyResponse.date.desc())\
        .first()
    
    if not latest_survey:
        raise ValueError(
            "No symptom data found. Student must complete the 'Submit Data' form first "
            "to provide comprehensive PCOS symptom information for prediction."
        )
    
    # Extract all 23 comprehensive symptoms
    clinical_symptoms = {
        # Reproductive/Menstrual (5 features)
        'irregular_cycles': latest_survey.irregular_cycles or 3,
        'oligomenorrhea': 1 if latest_survey.oligomenorrhea else 0,
        'amenorrhea': 1 if latest_survey.amenorrhea else 0,
        'heavy_menstruation': 1 if latest_survey.heavy_menstruation else 0,
        'pelvic_pain': latest_survey.pelvic_pain or 3,
        
        # Hormonal/Skin (4 features)
        'hirsutism': latest_survey.hirsutism or 3,
        'acne_severity': latest_survey.acne_severity or 3,
        'alopecia': 1 if latest_survey.alopecia else 0,
        'oily_skin': latest_survey.oily_skin or 3,
        
        # Metabolic (4 features)
        'weight_gain': latest_survey.weight_gain or 3,
        'insulin_resistance_symptoms': 1 if latest_survey.insulin_resistance_symptoms else 0,
        'elevated_blood_sugar': 1 if latest_survey.elevated_blood_sugar else 0,
        'acanthosis_nigricans': 1 if latest_survey.acanthosis_nigricans else 0,
        
        # Emotional/Psychological (4 features)
        'mood_swings_severity': latest_survey.mood_swings_severity or 3,
        'anxiety': latest_survey.anxiety or 3,
        'depression': latest_survey.depression or 3,
        'sleep_disturbances': latest_survey.sleep_disturbances or 3,
        
        # Skin-Related (3 features)
        'skin_tags': 1 if latest_survey.skin_tags else 0,
        'dark_patches': 1 if latest_survey.dark_patches else 0,
        'persistent_acne': 1 if latest_survey.persistent_acne else 0,
        
        # Other General (3 features)
        'fatigue_severity': latest_survey.fatigue_severity or 3,
        'low_energy': latest_survey.low_energy or 3,
        'sugar_cravings': latest_survey.sugar_cravings or 3,
    }
    
    # Create feature array in the same order as training
    features = [clinical_symptoms[col] for col in feature_columns]
    
    return np.array(features).reshape(1, -1)


def predict_pcos(profile):
    """
    Predict PCOS likelihood for a student profile
    
    Args:
        profile: StudentProfile database model instance
        
    Returns:
        dict: {
            'has_pcos': bool - prediction (True/False),
            'probability': float - probability of having PCOS (0-1),
            'confidence': str - confidence level description,
            'risk_level': str - risk category
        }
    """
    model, _ = load_model()
    
    # Prepare features
    X = prepare_features_from_profile(profile)
    
    # Make prediction
    prediction = model.predict(X)[0]
    probabilities = model.predict_proba(X)[0]
    
    # Extract probability for PCOS class (class 1)
    pcos_probability = probabilities[1]
    
    # Determine confidence level
    if pcos_probability >= 0.7 or pcos_probability <= 0.3:
        confidence = "High"
    elif pcos_probability >= 0.55 or pcos_probability <= 0.45:
        confidence = "Moderate"
    else:
        confidence = "Low"
    
    # Determine risk level
    if pcos_probability >= 0.7:
        risk_level = "High Risk"
    elif pcos_probability >= 0.5:
        risk_level = "Moderate Risk"
    elif pcos_probability >= 0.3:
        risk_level = "Low Risk"
    else:
        risk_level = "Very Low Risk"
    
    return {
        'has_pcos': bool(prediction),
        'probability': float(pcos_probability),
        'probability_percentage': float(pcos_probability * 100),
        'confidence': confidence,
        'risk_level': risk_level
    }

def get_feature_importance():
    """
    Get feature importance from the trained model
    
    Returns:
        list of dicts: [{'feature': name, 'importance': value}, ...]
    """
    model, feature_columns = load_model()
    
    importance_data = []
    for feature, importance in zip(feature_columns, model.feature_importances_):
        importance_data.append({
            'feature': feature,
            'importance': float(importance)
        })
    
    # Sort by importance
    importance_data.sort(key=lambda x: x['importance'], reverse=True)
    
    return importance_data

def get_recommendations(prediction_result, profile):
    """
    Generate recommendations based on prediction results
    
    Args:
        prediction_result: dict from predict_pcos()
        profile: StudentProfile instance
        
    Returns:
        list of recommendation strings
    """
    recommendations = []
    
    if prediction_result['has_pcos']:
        recommendations.append(
            "⚕️ We recommend consulting with a healthcare professional for proper diagnosis and treatment."
        )
        recommendations.append(
            "📋 Consider getting a clinical examination including ultrasound and hormone level tests."
        )
    
    if prediction_result['probability'] >= 0.5:
        recommendations.append(
            "🏃‍♀️ Maintain a healthy lifestyle with regular exercise (at least 30 minutes daily)."
        )
        recommendations.append(
            "🥗 Follow a balanced diet rich in whole grains, fruits, vegetables, and lean proteins."
        )
        recommendations.append(
            "😴 Ensure adequate sleep (7-9 hours) to help regulate hormones."
        )
    
    # Check symptom severity
    high_symptom_scores = 0
    for i in range(1, 6):  # symptoms_1 through symptoms_5
        symptom_val = getattr(profile, f'symptoms_{i}', None)
        if symptom_val and symptom_val >= 4:
            high_symptom_scores += 1
    
    if high_symptom_scores >= 3:
        recommendations.append(
            "📚 Consider requesting academic accommodations if symptoms affect your studies."
        )
        recommendations.append(
            "🧘‍♀️ Practice stress management techniques like meditation or yoga."
        )
    
    if not prediction_result['has_pcos']:
        recommendations.append(
            "✅ Continue monitoring your symptoms and maintaining healthy habits."
        )
        recommendations.append(
            "📊 Keep track of your menstrual cycle and any unusual symptoms."
        )
    
    return recommendations

def model_exists():
    """Check if the clinical symptom model files exist"""
    model_path = MODEL_DIR / MODEL_FILE
    features_path = MODEL_DIR / FEATURES_FILE
    
    return model_path.exists() and features_path.exists()

