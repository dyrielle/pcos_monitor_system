"""
Test script for Reports Module
"""

from app import create_app
from app.reports import ReportGenerator

app = create_app()
with app.app_context():
    print("=" * 60)
    print("TESTING REPORTS MODULE")
    print("=" * 60)
    
    generator = ReportGenerator()
    
    # Test 1: Population Summary
    print("\n1. POPULATION SUMMARY:")
    print("-" * 60)
    summary = generator.get_population_summary()
    print(f"  Total Students: {summary['total_students']}")
    print(f"  Average Age: {summary['avg_age']}")
    print(f"  Total Academic Records: {summary['total_academic_records']}")
    print(f"  Total Surveys: {summary['total_surveys']}")
    print(f"  Diagnosis Breakdown: {summary['diagnosis_breakdown']}")
    print(f"  Avg Awareness Score: {summary['avg_awareness_score']}")
    print(f"  Avg Academic Pressure: {summary['avg_academic_pressure']}")
    print(f"  Avg Symptoms Score: {summary['avg_symptoms_score']}")
    print(f"  Date Generated: {summary['date_generated']}")
    
    # Test 2: Correlation Analysis
    print("\n2. CORRELATION ANALYSIS:")
    print("-" * 60)
    correlations = generator.get_correlation_analysis()
    if correlations:
        for key, data in correlations.items():
            print(f"  {key}:")
            print(f"    Coefficient: {data['coefficient']}")
            print(f"    P-value: {data['p_value']}")
            print(f"    Interpretation: {data['interpretation']}")
    else:
        print("  No correlations available (insufficient data)")
    
    # Test 3: Diagnosis Comparison
    print("\n3. DIAGNOSIS COMPARISON:")
    print("-" * 60)
    comparison = generator.get_diagnosis_comparison()
    for diag, data in comparison.items():
        print(f"  {diag}:")
        print(f"    Count: {data['count']}")
        print(f"    Avg Awareness: {data['avg_awareness']}")
        print(f"    Avg Pressure: {data['avg_pressure']}")
        print(f"    Avg Symptoms: {data['avg_symptoms']}")
    
    # Test 4: Time Trends
    print("\n4. TIME TRENDS:")
    print("-" * 60)
    trends = generator.get_time_trends()
    if trends:
        for month, data in trends.items():
            print(f"  {month}:")
            print(f"    Avg Fatigue: {data['avg_fatigue']}")
            print(f"    Avg Mood: {data['avg_mood']}")
            print(f"    Avg Stress: {data['avg_stress']}")
            print(f"    Avg Sleep: {data['avg_sleep']}")
    else:
        print("  No time trends available (no survey data)")
    
    # Test 5: Key Findings
    print("\n5. KEY FINDINGS:")
    print("-" * 60)
    findings = generator.get_key_findings()
    for i, finding in enumerate(findings, 1):
        print(f"  {i}. {finding}")
    
    # Test 6: Full Report Data
    print("\n6. FULL REPORT DATA GENERATION:")
    print("-" * 60)
    full_data = generator.generate_full_report_data()
    print(f"  ✓ Summary: {bool(full_data['summary'])}")
    print(f"  ✓ Correlations: {bool(full_data['correlations'])}")
    print(f"  ✓ Diagnosis Comparison: {bool(full_data['diagnosis_comparison'])}")
    print(f"  ✓ Time Trends: {full_data['time_trends'] is not None}")
    print(f"  ✓ Key Findings: {len(full_data['key_findings'])} findings")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
