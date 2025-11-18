# CSV Import Guide

## Overview

The PCOS Monitor system now supports **TWO types of CSV imports**:

1. **Baseline Data Import** - Imports student profiles, awareness scores, and academic pressure data
2. **Symptom Data Import** - Imports detailed PCOS symptom assessments for existing students

---

## 1. Baseline Data Import (Profile Setup)

### What it imports:
- Student profiles (age, year level, degree program)
- PCOS awareness scores (5-point Likert scale responses)
- Academic pressure scores
- Basic symptom-related scores
- Clinical diagnosis status

### Data Storage:
- Creates **User** records (with auto-generated emails)
- Creates **StudentProfile** records
- Calculates composite scores for awareness, academic pressure, and symptoms

### Sample CSV Structure:
Download the sample CSV from the admin panel using the **"Download Sample CSV Format"** button in the Baseline Import modal.

**Key Columns:**
- Age
- Year Level
- Clinical Diagnosis
- Awareness items (Familiar PCOS, Know Symptoms, etc.)
- Academic pressure items
- Basic symptom items

### Use Case:
- Initial data import from research surveys
- Bulk student registration
- Historical data migration

---

## 2. Symptom Data Import (Submit Data)

### What it imports:
- Detailed PCOS symptoms (23 comprehensive clinical symptoms)
- Time-series symptom tracking
- Individual symptom assessments per student

### Data Storage:
- Creates **SurveyResponse** records linked to student profiles
- Records 23 comprehensive PCOS symptoms across 6 categories:
  1. Reproductive/Menstrual symptoms (5 fields)
  2. Hormonal/Hyperandrogenism symptoms (4 fields)
  3. Metabolic symptoms (4 fields)
  4. Emotional/Psychological symptoms (4 fields)
  5. Skin-related symptoms (3 fields)
  6. Other general symptoms (3 fields)

### Import Modes:

**Mode 1: With Email Column (Linked Import)**
- CSV must include an `Email` column
- Links symptom data to existing students
- Students must already exist in the system
- Use when you have identifiable respondents

**Mode 2: Without Email Column (Anonymous Import)**
- CSV does **NOT** need an `Email` column
- Auto-creates anonymous student profiles for each row
- Each row becomes a separate anonymous respondent
- Perfect for research data where respondents are not tracked individually
- **Use this mode when baseline and symptom datasets have different respondents**

### Sample CSV Structure:

**With Email (Mode 1):**
Download the sample CSV from the admin panel using the **"Download Sample Symptom CSV Format"** button.

**Without Email (Mode 2) - For your use case:**
Your CSV file should have columns like:
- `id` (optional, ignored)
- `heavy_menstruation` (TRUE/FALSE)
- `elevated_blood_sugar` (TRUE/FALSE)
- `persistent_acne` (TRUE/FALSE)
- `pelvic_pain` (1-5 scale)
- `acanthosis_nigricans` (TRUE/FALSE)
- `fatigue_severity` (1-5 scale)
- ... and all other symptom columns

### Important Notes:
✅ **Email column is OPTIONAL** - System auto-detects import mode
- Mode 1 (Email present): Links to existing students
- Mode 2 (No email): Creates anonymous profiles automatically
- Supports both `Title Case` and `snake_case` column names
- Multiple symptom records can be imported (time-series tracking)

### Use Case:
- **Mode 1:** Importing follow-up data for registered students
- **Mode 2:** Importing anonymous research data (different respondents from baseline)
- Bulk symptom data from external surveys
- Time-series symptom tracking over academic terms
- Clinical trial data import

---

## How to Use

### Admin Panel Access:
1. Login as admin
2. Navigate to **Admin Control Panel**
3. You'll see two import buttons:
   - **⬆ Import CSV (Baseline)** - For profile/awareness data
   - **⬆ Import CSV (Symptoms)** - For detailed symptom data

### Import Process:
1. Click the appropriate import button
2. Download the sample CSV format
3. Prepare your CSV file following the sample structure
4. Upload the CSV file
5. Review the import results (created/skipped counts)

### Data Validation:
- Missing required columns will trigger an error
- Invalid data types are skipped with error messages
- Duplicate emails in baseline import are skipped
- Missing student emails in symptom import are skipped

---

## Field Mappings

### Symptom Data - Detailed Field Reference

#### 1-5 Scale Fields:
- **1** = None/Never
- **2** = Mild/Rarely
- **3** = Moderate/Sometimes
- **4** = Severe/Often
- **5** = Very Severe/Always

**Fields using 1-5 scale:**
- Irregular Cycles
- Pelvic Pain
- Acne Severity
- Hirsutism
- Oily Skin
- Weight Gain
- Mood Swings Severity
- Anxiety
- Depression
- Sleep Disturbances
- Fatigue Severity
- Low Energy
- Sugar Cravings

#### Yes/No Boolean Fields:
- Oligomenorrhea
- Amenorrhea
- Heavy Menstruation
- Alopecia
- Insulin Resistance
- Elevated Blood Sugar
- Acanthosis Nigricans
- Skin Tags
- Dark Patches
- Persistent Acne

---

## Integration with ML Models

The symptom data imported through this feature is used by:
- **Clinical Symptom Prediction Model** (`train_clinical_symptom_model.py`)
- **Dashboard Analytics** (symptom distributions, trends)
- **Student Health Reports** (individual symptom tracking)

After importing symptom data, you can train the ML model with:
```powershell
.\venv\Scripts\python.exe train_clinical_symptom_model.py
```

---

## Best Practices

1. **Import Order:**
   - Always import **Baseline Data** first
   - Then import **Symptom Data** for those students

2. **Data Quality:**
   - Ensure emails are consistent between baseline and symptom imports
   - Use proper date formats (YYYY-MM-DD)
   - Validate numeric ranges (1-5 for scales)
   - Use "Yes"/"No" for boolean fields

3. **Batch Processing:**
   - Large CSV files are processed row-by-row
   - Errors in individual rows won't stop the entire import
   - Review error messages to fix problematic rows

4. **Time-Series Data:**
   - Include dates in symptom imports for proper tracking
   - Multiple symptom records per student are allowed
   - Useful for longitudinal studies

---

## Troubleshooting

### Common Errors:

**"Missing required column: Email"**
- Symptom CSV must include an "Email" column
- Check spelling and capitalization

**"User with email X not found"**
- Student must exist in system before importing symptoms
- Run baseline import first or register the student manually

**"Missing required columns: Age, Year Level"**
- Baseline CSV must include these columns
- Download the sample CSV for reference

**"Failed to process CSV"**
- Check file encoding (should be UTF-8)
- Ensure proper CSV format
- Check for special characters in data

---

## Summary

| Feature | Baseline Import | Symptom Import (Mode 1) | Symptom Import (Mode 2) |
|---------|----------------|------------------------|------------------------|
| **Creates** | Users + Profiles | Survey Responses | Users + Profiles + Responses |
| **Required Fields** | Age, Year Level | Email + Symptoms | Symptom columns only |
| **Pre-requisite** | None | Students must exist | None |
| **Email Column** | Not used | Required | Optional (omit it) |
| **Use Case** | Initial setup | Linked tracking | Anonymous research data |
| **Data Type** | Profile + Awareness | Detailed symptoms | Detailed symptoms |
| **Records Per Student** | One profile | Multiple responses | One anonymous profile per row |
| **Respondent Matching** | N/A | Same as baseline | **Different from baseline** |

**Perfect for your scenario:** Use **Mode 2** (no Email column) to import symptom data from respondents who are different from your baseline dataset!

---

## Need Help?

- Download sample CSV files from the import modals
- Check existing data structure in the Dataset Tables page
- Review error messages carefully - they indicate which rows failed
- Verify CSV encoding is UTF-8
