from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, mail       # <-- added mail here
from .auth import auth_bp
from .main import main_bp
from .dash_app import init_dashboard
from .admin import admin_bp

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)     # <-- add this line

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    init_dashboard(app)

    return app