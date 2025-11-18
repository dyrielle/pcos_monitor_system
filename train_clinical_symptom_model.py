"""
PCOS Clinical Symptom Model Training Script
Trains a Random Forest model using the 23 comprehensive PCOS symptoms from Submit Data
Collects data from actual student survey responses in the database
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import os
from pathlib import Path

# Import Flask app and database
import sys
sys.path.insert(0, 'app')
from app import create_app
from app.models import User, StudentProfile, SurveyResponse
from app.extensions import db

def collect_training_data_from_database():
    """
    Collect training data from the database
    Uses the 23 comprehensive symptoms from SurveyResponse
    """
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("COLLECTING TRAINING DATA FROM DATABASE")
        print("=" * 80)
        
        # Get all survey responses
        surveys = SurveyResponse.query.all()
        
        if len(surveys) == 0:
            print("\n⚠️  WARNING: No survey responses found in database!")
            print("Students need to fill out the 'Submit Data' form first.")
            print("\nTo proceed, you can:")
            print("1. Have students complete the Submit Data form")
            print("2. Import sample data if available")
            return None
        
        print(f"\n✓ Found {len(surveys)} survey responses in database")
        
        # Prepare data structure
        data = []
        
        for survey in surveys:
            # Get the associated profile (SurveyResponse uses profile_id)
            profile = StudentProfile.query.get(survey.profile_id)
            if not profile:
                continue
            
            # Get the user
            user = User.query.get(profile.user_id)
            if not user or user.is_admin:
                continue
            
            # Extract the 23 comprehensive PCOS symptoms (matching actual database columns)
            row = {
                # Reproductive/Menstrual (5 features)
                'irregular_cycles': survey.irregular_cycles or 3,
                'oligomenorrhea': 1 if survey.oligomenorrhea else 0,
                'amenorrhea': 1 if survey.amenorrhea else 0,
                'heavy_menstruation': 1 if survey.heavy_menstruation else 0,
                'pelvic_pain': survey.pelvic_pain or 3,
                
                # Hormonal/Skin (4 features)
                'hirsutism': survey.hirsutism or 3,
                'acne_severity': survey.acne_severity or 3,
                'alopecia': 1 if survey.alopecia else 0,
                'oily_skin': survey.oily_skin or 3,
                
                # Metabolic (4 features)
                'weight_gain': survey.weight_gain or 3,
                'insulin_resistance_symptoms': 1 if survey.insulin_resistance_symptoms else 0,
                'elevated_blood_sugar': 1 if survey.elevated_blood_sugar else 0,
                'acanthosis_nigricans': 1 if survey.acanthosis_nigricans else 0,
                
                # Emotional/Psychological (4 features)
                'mood_swings_severity': survey.mood_swings_severity or 3,
                'anxiety': survey.anxiety or 3,
                'depression': survey.depression or 3,
                'sleep_disturbances': survey.sleep_disturbances or 3,
                
                # Skin-Related (3 features)
                'skin_tags': 1 if survey.skin_tags else 0,
                'dark_patches': 1 if survey.dark_patches else 0,
                'persistent_acne': 1 if survey.persistent_acne else 0,
                
                # Other General (3 features)
                'fatigue_severity': survey.fatigue_severity or 3,
                'low_energy': survey.low_energy or 3,
                'sugar_cravings': survey.sugar_cravings or 3,
                
                # Target variable (PCOS diagnosis)
                'has_pcos': 1 if profile.has_pcos_diagnosis else 0
            }
            
            data.append(row)
        
        if len(data) == 0:
            print("\n⚠️  WARNING: No valid training data collected!")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        print(f"\n✓ Collected {len(df)} valid training samples")
        print(f"✓ PCOS cases: {df['has_pcos'].sum()} ({df['has_pcos'].sum()/len(df)*100:.1f}%)")
        print(f"✓ Non-PCOS cases: {(df['has_pcos'] == 0).sum()} ({(df['has_pcos'] == 0).sum()/len(df)*100:.1f}%)")
        
        return df

def train_clinical_model(df):
    """Train Random Forest model on clinical symptoms"""
    print("\n" + "=" * 80)
    print("TRAINING CLINICAL SYMPTOM MODEL")
    print("=" * 80)
    
    # Separate features and target
    feature_cols = [col for col in df.columns if col != 'has_pcos']
    X = df[feature_cols]
    y = df['has_pcos']
    
    print(f"\nFeature count: {len(feature_cols)}")
    print("Features by category:")
    print("  • Reproductive/Menstrual: 5 features")
    print("  • Hormonal/Skin: 4 features")
    print("  • Metabolic: 4 features")
    print("  • Emotional/Psychological: 4 features")
    print("  • Skin-Related: 3 features")
    print("  • General Symptoms: 3 features")
    
    # Check if we have enough data
    if len(df) < 30:
        print(f"\n⚠️  WARNING: Only {len(df)} samples available.")
        print("For better accuracy, collect at least 50-100 student responses.")
        print("Proceeding with available data for demonstration...")
    
    # Split data
    if len(df) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if y.sum() > 1 else None
        )
    else:
        print("\n⚠️  Not enough data for train/test split. Using all data for training.")
        X_train, X_test, y_train, y_test = X, X, y, y
    
    print(f"\nTraining samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    
    # Train Random Forest
    print("\nTraining Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    print("✓ Model training complete!")
    
    # Evaluate
    print("\n" + "=" * 80)
    print("MODEL EVALUATION")
    print("=" * 80)
    
    # Training accuracy
    train_score = model.score(X_train, y_train)
    print(f"\nTraining Accuracy: {train_score * 100:.2f}%")
    
    # Test accuracy (if different from train)
    if len(X_test) > 0 and len(X_test) != len(X_train):
        test_score = model.score(X_test, y_test)
        print(f"Testing Accuracy: {test_score * 100:.2f}%")
        
        # Predictions
        y_pred = model.predict(X_test)
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['No PCOS', 'PCOS'], zero_division=0))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
    
    # Cross-validation (if enough data)
    if len(df) >= 10:
        try:
            cv_scores = cross_val_score(model, X, y, cv=min(5, len(df)), scoring='accuracy')
            print(f"\nCross-Validation Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
        except:
            print("\n⚠️  Cross-validation skipped (insufficient data)")
    
    # Feature importance
    print("\n" + "=" * 80)
    print("TOP 10 MOST IMPORTANT FEATURES")
    print("=" * 80)
    
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n" + feature_importance.head(10).to_string(index=False))
    
    return model, feature_cols

def save_model(model, feature_columns):
    """Save the trained model and feature columns"""
    print("\n" + "=" * 80)
    print("SAVING MODEL")
    print("=" * 80)
    
    # Create models directory
    model_dir = Path('ml_models')
    model_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = model_dir / 'pcos_clinical_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n✓ Model saved to: {model_path}")
    
    # Save feature columns
    features_path = model_dir / 'clinical_feature_columns.pkl'
    with open(features_path, 'wb') as f:
        pickle.dump(feature_columns, f)
    print(f"✓ Feature columns saved to: {features_path}")
    
    print("\n" + "=" * 80)
    print("✓ MODEL TRAINING COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Restart Flask server to load the new model")
    print("2. Test prediction with students who have submitted symptom data")
    print("3. Collect more student responses to improve accuracy")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PCOS CLINICAL SYMPTOM MODEL TRAINER")
    print("=" * 80)
    print("\nThis script trains a model using the 23 comprehensive symptoms")
    print("from student 'Submit Data' responses stored in the database.")
    
    # Collect data from database
    df = collect_training_data_from_database()
    
    if df is None or len(df) < 5:
        print("\n" + "=" * 80)
        print("❌ INSUFFICIENT DATA")
        print("=" * 80)
        print("\nCannot train model with fewer than 5 samples.")
        print("\nPlease:")
        print("1. Have at least 5-10 students complete the 'Submit Data' form")
        print("2. Ensure students indicate if they have a PCOS diagnosis in their profile")
        print("3. Run this script again")
        sys.exit(1)
    
    # Train model
    model, feature_cols = train_clinical_model(df)
    
    # Save model
    save_model(model, feature_cols)
    
    print("\n✓ Ready to make predictions based on comprehensive symptom data!")
