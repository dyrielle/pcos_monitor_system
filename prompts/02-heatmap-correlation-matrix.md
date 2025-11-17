# Implementation Prompt 02: Correlation Heatmap Visualization

## 🎯 Objective
Add an interactive correlation heatmap to the admin charts page that shows relationships between all numeric health and academic variables in the PCOS dataset.

## 📋 Prerequisites
- Task 01 completed (dependencies installed)
- Project root: `c:\Users\samfn\Downloads\SYSTEM\pcos_monitor`
- Familiarity with Plotly for interactive visualizations

## 🔧 Task Overview
Enhance the existing `/admin/charts` route to include a correlation heatmap showing relationships between:
- PCOS awareness score
- Academic pressure score
- Symptoms score
- Average GPA
- Average attendance
- Average study hours
- Average fatigue, mood swings, and stress from surveys

## 📝 Implementation Steps

### Step 1: Update Backend Route (`app/admin.py`)

**File:** `c:\Users\samfn\Downloads\SYSTEM\pcos_monitor\app\admin.py`

**Location:** Find the `charts_page()` function (around line 391)

**Current function structure:**
```python
@admin_bp.route("/charts")
@login_required
def charts_page():
    if not current_user.is_admin:
        return "Access denied", 403

    from .models import StudentProfile
    import pandas as pd

    profiles = StudentProfile.query.all()
    df = pd.DataFrame([...])
    rows = df.to_dict(orient="records") if not df.empty else []
    return render_template("admin_charts.html", rows=rows)
```

**Action:** Replace the `charts_page()` function with the enhanced version below:

```python
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
            # Use Spearman's rho for non-normally distributed data
            correlation_matrix = df_correlation.corr(method='spearman').round(3)
            correlation_labels = correlation_matrix.columns.tolist()
            correlation_values = correlation_matrix.values.tolist()

    return render_template("admin_charts.html", 
                          rows=rows,
                          correlation_labels=correlation_labels,
                          correlation_values=correlation_values)
```

**Key Changes:**
1. Import `numpy` and additional models (`AcademicRecord`, `SurveyResponse`)
2. Calculate averages for each student's academic and survey data
3. Create correlation matrix using pandas `.corr(method='spearman')` (Spearman's rho for non-normally distributed data)
4. Pass correlation data to template

### Step 2: Update Frontend Template (`app/templates/admin_charts.html`)

**File:** `c:\Users\samfn\Downloads\SYSTEM\pcos_monitor\app\templates\admin_charts.html`

**Location:** After the existing scatter plots section, before the "Back to Admin Panel" button (around line 48)

**Action:** Add the following heatmap section:

```html
    </div>

    <!-- NEW: Correlation Heatmap Section -->
    <hr class="my-5">

    <h3>Correlation Heatmap</h3>
    <p class="text-muted">
        Spearman's rho correlation between all numeric variables. Values range from -1 (negative correlation) to +1 (positive correlation). 
        Spearman's rho is used because the dataset is not normally distributed.
    </p>

    <div class="row">
        <div class="col-12 mb-4">
            <div class="card shadow-sm">
                <div class="card-header bg-light">
                    <strong>Variable Correlation Matrix</strong>
                </div>
                <div class="card-body">
                    <div id="correlation_heatmap" style="width:100%;height:600px;"></div>
                </div>
            </div>
        </div>
    </div>

    <a href="{{ url_for('admin.admin_home') }}" class="btn btn-secondary">Back to Admin Panel</a>
```

### Step 3: Add Heatmap JavaScript

**File:** `c:\Users\samfn\Downloads\SYSTEM\pcos_monitor\app\templates\admin_charts.html`

**Location:** In the existing `<script>` section, after the scatter plot code (before the closing `</script>` tag, around line 140)

**Action:** Add this JavaScript code:

```javascript
    // ----- CORRELATION HEATMAP -----
    const correlationLabels = {{ correlation_labels | tojson }};
    const correlationValues = {{ correlation_values | tojson }};

    if (correlationLabels && correlationLabels.length > 0 && correlationValues && correlationValues.length > 0) {
        const heatmapData = [{
            z: correlationValues,
            x: correlationLabels,
            y: correlationLabels,
            type: 'heatmap',
            colorscale: [
                [0, '#3D5A80'],      // Dark blue (negative correlation)
                [0.5, '#EE6C4D'],    // White (no correlation)
                [1, '#98C1D9']       // Light blue (positive correlation)
            ],
            zmin: -1,
            zmax: 1,
            colorbar: {
                title: 'Correlation',
                titleside: 'right'
            },
            hovertemplate: '%{y} ↔ %{x}<br>Correlation: %{z:.3f}<extra></extra>',
            showscale: true
        }];

        const heatmapLayout = {
            title: '',
            xaxis: {
                title: '',
                tickangle: -45,
                side: 'bottom'
            },
            yaxis: {
                title: '',
                autorange: 'reversed'
            },
            margin: {
                l: 150,
                r: 50,
                t: 50,
                b: 150
            },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff'
        };

        const heatmapConfig = {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        };

        Plotly.newPlot('correlation_heatmap', heatmapData, heatmapLayout, heatmapConfig);
    } else {
        document.getElementById('correlation_heatmap').innerHTML = 
            '<div class="text-center text-muted p-5">Not enough data to generate correlation heatmap. Need at least 2 variables with 2+ data points.</div>';
    }
```

## ✅ Validation Checklist

- [ ] `app/admin.py` updated with enhanced `charts_page()` function
- [ ] `app/templates/admin_charts.html` updated with heatmap HTML section
- [ ] JavaScript heatmap code added to template
- [ ] No syntax errors in Python or JavaScript code
- [ ] Application runs without errors
- [ ] Can access `/admin/charts` route as admin
- [ ] Correlation heatmap displays correctly
- [ ] Heatmap shows appropriate color gradient
- [ ] Hover tooltips work on heatmap cells

## 🧪 Testing Instructions

### Test 1: Access Charts Page
1. Start the Flask application
2. Login as admin user
3. Navigate to `/admin/charts`
4. Verify page loads without errors

### Test 2: Verify Heatmap Display
1. On charts page, scroll down to "Correlation Heatmap" section
2. Verify heatmap renders with color gradient
3. Hover over cells - should show correlation values
4. Check that diagonal shows 1.0 (variable correlated with itself)

### Test 3: Check Data Accuracy
1. Note a correlation value from the heatmap
2. Verify it makes logical sense (e.g., symptoms vs academic pressure should show some correlation)
3. Check that values are between -1 and 1

### Test 4: Edge Case - No Data
1. If you have a fresh database with no data:
   - Should show message: "Not enough data to generate correlation heatmap"

## 🐛 Troubleshooting

### Issue: "No module named numpy"
**Solution:** Run `pip install numpy` or re-run task 01

### Issue: Heatmap shows all white/single color
**Solution:** Check that correlation values are being calculated. May need more diverse data.

### Issue: JavaScript error in console
**Solution:** 
- Check that `correlation_labels` and `correlation_values` are properly passed from backend
- Verify JSON serialization with `| tojson` filter

### Issue: Heatmap not displaying
**Solution:**
- Ensure Plotly CDN is loaded (should be in template already)
- Check browser console for errors
- Verify div ID matches: `correlation_heatmap`

## 📊 Expected File Changes

### Files Modified:
1. `app/admin.py` - Enhanced `charts_page()` function
2. `app/templates/admin_charts.html` - Added heatmap HTML and JavaScript

### Files Created:
None

## 🎓 Understanding the Implementation

**What is a correlation heatmap?**
- Visual representation of correlation coefficients between variables
- Color intensity shows strength of relationship
- Helps identify which health/academic factors are related

**Color scheme:**
- Dark blue: Negative correlation (as one increases, other decreases)
- White/Light: No correlation (variables independent)
- Light blue: Positive correlation (both increase/decrease together)

## 🚀 Next Steps

After successful completion:
1. Update tracker: `prompts/00-TRACKER.md` - Mark task 02 as ✅ Completed
2. Proceed to: `03-heatmap-diagnosis-groups.md`

---

**Estimated Time:** 20 minutes  
**Difficulty:** Medium  
**Dependencies:** Task 01 (ReportLab & dependencies)
