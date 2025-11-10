from app import create_app
from app.extensions import db

app = create_app()

@app.shell_context_processor
def make_shell_context():
    from app.models import User, StudentProfile, AcademicRecord, SurveyResponse
    return {"db": db, "User": User, "StudentProfile": StudentProfile,
            "AcademicRecord": AcademicRecord, "SurveyResponse": SurveyResponse}

if __name__ == "__main__":
    app.run()