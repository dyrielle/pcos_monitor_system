"""
Reports Module for PCOS Monitor System
Handles data aggregation and statistical analysis for research reports.
"""

from .models import StudentProfile, AcademicRecord, SurveyResponse
from .extensions import db
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr
from datetime import datetime


class ReportGenerator:
    """Main class for generating research report data."""
    
    def __init__(self):
        """Initialize report generator."""
        self.profiles = StudentProfile.query.all()
        self.academic_records = AcademicRecord.query.all()
        self.survey_responses = SurveyResponse.query.all()
    
    def get_population_summary(self):
        """
        Get high-level population statistics.
        
        Returns:
            dict: Population summary statistics
        """
        total_students = len(self.profiles)
        
        # Diagnosis breakdown
        diagnosis_counts = {}
        for p in self.profiles:
            diag = p.clinical_diagnosis or "Not Specified"
            diagnosis_counts[diag] = diagnosis_counts.get(diag, 0) + 1
        
        # Age statistics
        ages = [p.age for p in self.profiles if p.age]
        avg_age = np.mean(ages) if ages else None
        
        # Baseline score averages
        awareness_scores = [p.pcos_awareness_score for p in self.profiles if p.pcos_awareness_score]
        pressure_scores = [p.academic_pressure_score for p in self.profiles if p.academic_pressure_score]
        symptoms_scores = [p.pcos_symptoms_score for p in self.profiles if p.pcos_symptoms_score]
        
        return {
            "total_students": total_students,
            "diagnosis_breakdown": diagnosis_counts,
            "avg_age": round(avg_age, 1) if avg_age else None,
            "total_academic_records": len(self.academic_records),
            "total_surveys": len(self.survey_responses),
            "avg_awareness_score": round(np.mean(awareness_scores), 2) if awareness_scores else None,
            "avg_academic_pressure": round(np.mean(pressure_scores), 2) if pressure_scores else None,
            "avg_symptoms_score": round(np.mean(symptoms_scores), 2) if symptoms_scores else None,
            "date_generated": datetime.now().strftime("%B %d, %Y at %I:%M %p")
        }
    
    def get_correlation_analysis(self):
        """
        Perform correlation analysis between key variables.
        
        Returns:
            dict: Correlation coefficients and p-values
        """
        # Build dataframe with all variables
        data_rows = []
        
        for p in self.profiles:
            # Academic averages
            p_academic = [r for r in self.academic_records if r.profile_id == p.id]
            avg_gpa = np.mean([r.gpa for r in p_academic if r.gpa]) if p_academic else None
            avg_attendance = np.mean([r.attendance_percent for r in p_academic if r.attendance_percent]) if p_academic else None
            
            # Survey averages
            p_surveys = [s for s in self.survey_responses if s.profile_id == p.id]
            avg_fatigue = np.mean([s.fatigue for s in p_surveys if s.fatigue]) if p_surveys else None
            avg_stress = np.mean([s.perceived_academic_stress for s in p_surveys if s.perceived_academic_stress]) if p_surveys else None
            
            data_rows.append({
                "awareness": p.pcos_awareness_score,
                "academic_pressure": p.academic_pressure_score,
                "symptoms": p.pcos_symptoms_score,
                "gpa": avg_gpa,
                "attendance": avg_attendance,
                "fatigue": avg_fatigue,
                "stress": avg_stress
            })
        
        df = pd.DataFrame(data_rows)
        
        # Calculate key correlations
        correlations = {}
        
        # Symptoms vs Academic Pressure
        if df["symptoms"].notna().sum() > 2 and df["academic_pressure"].notna().sum() > 2:
            corr, p_val = spearmanr(df["symptoms"].dropna(), df["academic_pressure"].dropna())
            correlations["symptoms_vs_pressure"] = {
                "coefficient": round(corr, 3),
                "p_value": round(p_val, 4),
                "interpretation": self._interpret_correlation(corr)
            }
        
        # Symptoms vs GPA
        df_clean = df[["symptoms", "gpa"]].dropna()
        if len(df_clean) > 2:
            corr, p_val = spearmanr(df_clean["symptoms"], df_clean["gpa"])
            correlations["symptoms_vs_gpa"] = {
                "coefficient": round(corr, 3),
                "p_value": round(p_val, 4),
                "interpretation": self._interpret_correlation(corr)
            }
        
        # Academic Pressure vs GPA
        df_clean = df[["academic_pressure", "gpa"]].dropna()
        if len(df_clean) > 2:
            corr, p_val = spearmanr(df_clean["academic_pressure"], df_clean["gpa"])
            correlations["pressure_vs_gpa"] = {
                "coefficient": round(corr, 3),
                "p_value": round(p_val, 4),
                "interpretation": self._interpret_correlation(corr)
            }
        
        # Fatigue vs Attendance
        df_clean = df[["fatigue", "attendance"]].dropna()
        if len(df_clean) > 2:
            corr, p_val = spearmanr(df_clean["fatigue"], df_clean["attendance"])
            correlations["fatigue_vs_attendance"] = {
                "coefficient": round(corr, 3),
                "p_value": round(p_val, 4),
                "interpretation": self._interpret_correlation(corr)
            }
        
        return correlations
    
    def get_diagnosis_comparison(self):
        """
        Compare metrics across diagnosis groups.
        
        Returns:
            dict: Mean values by diagnosis group
        """
        groups = {}
        
        for p in self.profiles:
            diag = p.clinical_diagnosis or "Not Specified"
            
            if diag not in groups:
                groups[diag] = {
                    "count": 0,
                    "awareness": [],
                    "pressure": [],
                    "symptoms": []
                }
            
            groups[diag]["count"] += 1
            if p.pcos_awareness_score:
                groups[diag]["awareness"].append(p.pcos_awareness_score)
            if p.academic_pressure_score:
                groups[diag]["pressure"].append(p.academic_pressure_score)
            if p.pcos_symptoms_score:
                groups[diag]["symptoms"].append(p.pcos_symptoms_score)
        
        # Calculate means
        comparison = {}
        for diag, data in groups.items():
            comparison[diag] = {
                "count": data["count"],
                "avg_awareness": round(np.mean(data["awareness"]), 2) if data["awareness"] else None,
                "avg_pressure": round(np.mean(data["pressure"]), 2) if data["pressure"] else None,
                "avg_symptoms": round(np.mean(data["symptoms"]), 2) if data["symptoms"] else None
            }
        
        return comparison
    
    def get_time_trends(self):
        """
        Analyze trends over time in survey responses.
        
        Returns:
            dict: Time-series trend data
        """
        if not self.survey_responses:
            return None
        
        # Sort surveys by date
        sorted_surveys = sorted(self.survey_responses, key=lambda s: s.date)
        
        # Group by month
        monthly_data = {}
        
        for survey in sorted_surveys:
            month_key = survey.date.strftime("%Y-%m")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "fatigue": [],
                    "mood": [],
                    "stress": [],
                    "sleep": []
                }
            
            if survey.fatigue:
                monthly_data[month_key]["fatigue"].append(survey.fatigue)
            if survey.mood_swings:
                monthly_data[month_key]["mood"].append(survey.mood_swings)
            if survey.perceived_academic_stress:
                monthly_data[month_key]["stress"].append(survey.perceived_academic_stress)
            if survey.sleep_quality:
                monthly_data[month_key]["sleep"].append(survey.sleep_quality)
        
        # Calculate monthly averages
        trends = {}
        for month, data in monthly_data.items():
            trends[month] = {
                "avg_fatigue": round(np.mean(data["fatigue"]), 2) if data["fatigue"] else None,
                "avg_mood": round(np.mean(data["mood"]), 2) if data["mood"] else None,
                "avg_stress": round(np.mean(data["stress"]), 2) if data["stress"] else None,
                "avg_sleep": round(np.mean(data["sleep"]), 2) if data["sleep"] else None
            }
        
        return trends
    
    def get_key_findings(self):
        """
        Generate key research findings summary.
        
        Returns:
            list: Key findings as text statements
        """
        findings = []
        
        # Population finding
        summary = self.get_population_summary()
        findings.append(f"Study includes {summary['total_students']} female students with {summary['total_surveys']} survey responses collected.")
        
        # Diagnosis finding
        if summary['diagnosis_breakdown']:
            diagnosed = summary['diagnosis_breakdown'].get('Yes', 0)
            if diagnosed > 0:
                pct = round((diagnosed / summary['total_students']) * 100, 1)
                findings.append(f"{pct}% of respondents have a clinical PCOS diagnosis ({diagnosed} students).")
        
        # Correlation findings
        correlations = self.get_correlation_analysis()
        
        if "symptoms_vs_pressure" in correlations:
            corr_data = correlations["symptoms_vs_pressure"]
            findings.append(f"PCOS symptoms show {corr_data['interpretation']} correlation with academic pressure (r={corr_data['coefficient']}, p={corr_data['p_value']}).")
        
        if "symptoms_vs_gpa" in correlations:
            corr_data = correlations["symptoms_vs_gpa"]
            findings.append(f"PCOS symptoms show {corr_data['interpretation']} correlation with GPA (r={corr_data['coefficient']}, p={corr_data['p_value']}).")
        
        # Symptom severity finding
        if summary['avg_symptoms_score']:
            if summary['avg_symptoms_score'] >= 4.0:
                findings.append(f"Population reports high average symptom severity ({summary['avg_symptoms_score']}/5.0).")
            elif summary['avg_symptoms_score'] >= 3.0:
                findings.append(f"Population reports moderate average symptom severity ({summary['avg_symptoms_score']}/5.0).")
        
        return findings
    
    def _interpret_correlation(self, r):
        """
        Interpret correlation coefficient strength.
        
        Args:
            r (float): Correlation coefficient
            
        Returns:
            str: Interpretation
        """
        abs_r = abs(r)
        
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        elif abs_r >= 0.2:
            strength = "weak"
        else:
            strength = "negligible"
        
        direction = "positive" if r >= 0 else "negative"
        
        return f"{strength} {direction}"
    
    def generate_full_report_data(self):
        """
        Generate complete report data package.
        
        Returns:
            dict: All report data combined
        """
        return {
            "summary": self.get_population_summary(),
            "correlations": self.get_correlation_analysis(),
            "diagnosis_comparison": self.get_diagnosis_comparison(),
            "time_trends": self.get_time_trends(),
            "key_findings": self.get_key_findings()
        }


class PDFReportBuilder:
    """Builds formatted PDF reports using ReportLab."""
    
    def __init__(self, report_data):
        """
        Initialize PDF report builder.
        
        Args:
            report_data (dict): Report data from ReportGenerator
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        # Store imports as class attributes
        self.letter = letter
        self.inch = inch
        self.colors = colors
        self.Table = Table
        self.TableStyle = TableStyle
        self.Paragraph = Paragraph
        self.Spacer = Spacer
        self.PageBreak = PageBreak
        self.SimpleDocTemplate = SimpleDocTemplate
        
        self.report_data = report_data
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
    
    def build_pdf(self, filename):
        """
        Build complete PDF report.
        
        Args:
            filename (str): Output PDF filename path
            
        Returns:
            str: Path to generated PDF
        """
        doc = self.SimpleDocTemplate(
            filename,
            pagesize=self.letter,
            rightMargin=0.75 * self.inch,
            leftMargin=0.75 * self.inch,
            topMargin=0.75 * self.inch,
            bottomMargin=0.75 * self.inch
        )
        
        # Build story (content)
        story = []
        
        # Title page
        story.extend(self._build_title_page())
        story.append(self.PageBreak())
        
        # Executive summary
        story.extend(self._build_summary_section())
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Key findings
        story.extend(self._build_findings_section())
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Correlation analysis
        story.extend(self._build_correlation_section())
        story.append(self.Spacer(1, 0.2 * self.inch))
        
        # Diagnosis comparison
        story.extend(self._build_diagnosis_section())
        
        # Build PDF
        doc.build(story)
        
        return filename
    
    def _build_title_page(self):
        """Build title page elements."""
        elements = []
        
        # Title
        title = self.Paragraph(
            "PCOS Academic & Health Monitoring System<br/>Research Report",
            self.title_style
        )
        elements.append(title)
        elements.append(self.Spacer(1, 0.3 * self.inch))
        
        # Subtitle
        subtitle = self.Paragraph(
            "Analysis of Health and Academic Performance Data",
            self.styles['Heading3']
        )
        elements.append(subtitle)
        elements.append(self.Spacer(1, 0.5 * self.inch))
        
        # Date
        date_text = f"Generated: {self.report_data['summary']['date_generated']}"
        date_para = self.Paragraph(date_text, self.styles['Normal'])
        elements.append(date_para)
        elements.append(self.Spacer(1, 0.3 * self.inch))
        
        # Summary stats box
        summary = self.report_data['summary']
        summary_text = f"""
        <b>Study Overview:</b><br/>
        Total Participants: {summary['total_students']}<br/>
        Academic Records: {summary['total_academic_records']}<br/>
        Survey Responses: {summary['total_surveys']}<br/>
        Average Age: {summary['avg_age'] or 'N/A'}
        """
        summary_para = self.Paragraph(summary_text, self.body_style)
        elements.append(summary_para)
        
        return elements
    
    def _build_summary_section(self):
        """Build executive summary section."""
        elements = []
        
        elements.append(self.Paragraph("Executive Summary", self.heading_style))
        
        summary = self.report_data['summary']
        
        # Population overview
        pop_text = f"""
        This report presents findings from a study of {summary['total_students']} female students 
        monitoring the relationship between PCOS symptoms and academic performance. 
        The study collected {summary['total_surveys']} survey responses and 
        {summary['total_academic_records']} academic records.
        """
        elements.append(self.Paragraph(pop_text, self.body_style))
        
        # Diagnosis breakdown
        if summary['diagnosis_breakdown']:
            diag_text = "<b>Diagnosis Distribution:</b><br/>"
            for diagnosis, count in summary['diagnosis_breakdown'].items():
                pct = round((count / summary['total_students']) * 100, 1)
                diag_text += f"• {diagnosis}: {count} students ({pct}%)<br/>"
            elements.append(self.Paragraph(diag_text, self.body_style))
        
        # Baseline scores
        if summary['avg_awareness_score']:
            scores_text = f"""
            <b>Population Baseline Scores:</b><br/>
            • PCOS Awareness: {summary['avg_awareness_score']}/5.0<br/>
            • Academic Pressure: {summary['avg_academic_pressure']}/5.0<br/>
            • Symptom Severity: {summary['avg_symptoms_score']}/5.0
            """
            elements.append(self.Paragraph(scores_text, self.body_style))
        
        return elements
    
    def _build_findings_section(self):
        """Build key findings section."""
        elements = []
        
        elements.append(self.Paragraph("Key Research Findings", self.heading_style))
        
        findings = self.report_data['key_findings']
        
        if findings:
            findings_text = ""
            for i, finding in enumerate(findings, 1):
                findings_text += f"{i}. {finding}<br/><br/>"
            elements.append(self.Paragraph(findings_text, self.body_style))
        else:
            elements.append(self.Paragraph("Insufficient data for key findings.", self.body_style))
        
        return elements
    
    def _build_correlation_section(self):
        """Build correlation analysis section."""
        elements = []
        
        elements.append(self.Paragraph("Correlation Analysis", self.heading_style))
        
        correlations = self.report_data['correlations']
        
        if correlations:
            # Create table data
            table_data = [['Variable Pair', 'Coefficient (r)', 'P-Value', 'Interpretation']]
            
            correlation_labels = {
                'symptoms_vs_pressure': 'Symptoms ↔ Academic Pressure',
                'symptoms_vs_gpa': 'Symptoms ↔ GPA',
                'pressure_vs_gpa': 'Academic Pressure ↔ GPA',
                'fatigue_vs_attendance': 'Fatigue ↔ Attendance'
            }
            
            for key, data in correlations.items():
                label = correlation_labels.get(key, key)
                table_data.append([
                    label,
                    str(data['coefficient']),
                    str(data['p_value']),
                    data['interpretation']
                ])
            
            # Create table
            table = self.Table(table_data, colWidths=[2.5 * self.inch, 1 * self.inch, 1 * self.inch, 2 * self.inch])
            table.setStyle(self.TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, self.colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.colors.whitesmoke, self.colors.lightgrey])
            ]))
            
            elements.append(table)
            elements.append(self.Spacer(1, 0.2 * self.inch))
            
            # Interpretation note
            note = self.Paragraph(
                "<i>Note: Spearman correlation coefficients range from -1 to +1. "
                "P-values < 0.05 indicate statistical significance.</i>",
                self.styles['Italic']
            )
            elements.append(note)
        else:
            elements.append(self.Paragraph("Insufficient data for correlation analysis.", self.body_style))
        
        return elements
    
    def _build_diagnosis_section(self):
        """Build diagnosis group comparison section."""
        elements = []
        
        elements.append(self.Paragraph("Diagnosis Group Comparison", self.heading_style))
        
        comparison = self.report_data['diagnosis_comparison']
        
        if comparison:
            # Create table
            table_data = [['Diagnosis', 'Count', 'Avg Awareness', 'Avg Pressure', 'Avg Symptoms']]
            
            for diagnosis, data in comparison.items():
                table_data.append([
                    diagnosis,
                    str(data['count']),
                    str(data['avg_awareness']) if data['avg_awareness'] else 'N/A',
                    str(data['avg_pressure']) if data['avg_pressure'] else 'N/A',
                    str(data['avg_symptoms']) if data['avg_symptoms'] else 'N/A'
                ])
            
            table = self.Table(table_data, colWidths=[1.5 * self.inch, 1 * self.inch, 1.3 * self.inch, 1.3 * self.inch, 1.3 * self.inch])
            table.setStyle(self.TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors.HexColor('#2ECC71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), self.colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, self.colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.colors.whitesmoke, self.colors.lightgrey])
            ]))
            
            elements.append(table)
        else:
            elements.append(self.Paragraph("No diagnosis group data available.", self.body_style))
        
        return elements
