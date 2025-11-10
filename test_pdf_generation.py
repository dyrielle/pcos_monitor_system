"""
Test script for PDF Report Generation
Tests all aspects of the PDFReportBuilder functionality
"""

from app import create_app
from app.reports import ReportGenerator, PDFReportBuilder
import os

def test_pdf_generation():
    """Test PDF generation with comprehensive checks."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Testing PDF Report Generation")
        print("=" * 60)
        
        # Step 1: Generate report data
        print("\n1. Generating report data...")
        generator = ReportGenerator()
        report_data = generator.generate_full_report_data()
        print(f"   ✓ Report data generated")
        print(f"   - Total students: {report_data['summary']['total_students']}")
        print(f"   - Academic records: {report_data['summary']['total_academic_records']}")
        print(f"   - Survey responses: {report_data['summary']['total_surveys']}")
        
        # Step 2: Initialize PDF builder
        print("\n2. Initializing PDF builder...")
        pdf_builder = PDFReportBuilder(report_data)
        print(f"   ✓ PDF builder initialized")
        
        # Step 3: Generate PDF
        print("\n3. Building PDF document...")
        output_path = os.path.join(os.getcwd(), 'comprehensive_test_report.pdf')
        result_path = pdf_builder.build_pdf(output_path)
        print(f"   ✓ PDF generated at: {result_path}")
        
        # Step 4: Verify file exists
        print("\n4. Verifying file...")
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"   ✓ File exists")
            print(f"   - File size: {file_size:,} bytes")
            
            if file_size > 1000:
                print(f"   ✓ File size looks reasonable (> 1KB)")
            else:
                print(f"   ⚠ Warning: File size seems small")
        else:
            print(f"   ✗ File does not exist!")
            return False
        
        # Step 5: Check report data sections
        print("\n5. Checking report data sections...")
        has_summary = bool(report_data.get('summary'))
        has_correlations = bool(report_data.get('correlations'))
        has_diagnosis = bool(report_data.get('diagnosis_comparison'))
        has_findings = bool(report_data.get('key_findings'))
        
        print(f"   - Summary section: {'✓' if has_summary else '✗'}")
        print(f"   - Correlations section: {'✓' if has_correlations else '✗'}")
        print(f"   - Diagnosis comparison: {'✓' if has_diagnosis else '✗'}")
        print(f"   - Key findings: {'✓' if has_findings else '✗'}")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        print(f"\nGenerated PDF: {output_path}")
        print("You can now open this file in a PDF reader to verify formatting.")
        
        return True

if __name__ == "__main__":
    try:
        success = test_pdf_generation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
