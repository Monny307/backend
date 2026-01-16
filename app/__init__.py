from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from config import config, ENVIRONMENT, USE_S3
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', ENVIRONMENT)

    app = Flask(__name__)

    # Ensure we have a default config fallback
    chosen_config = config.get(config_name, config['default'])
    app.config.from_object(chosen_config)

    # --- FIX: Ensure SQLALCHEMY_DATABASE_URI is always set ---
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        # Fallback to local SQLite for testing if DATABASE_URL missing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    # Configure CORS
    CORS(app,
         resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000'])}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    # Create upload folder if it doesn't exist
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(os.path.join(upload_folder, 'cvs'), exist_ok=True)
        os.makedirs(os.path.join(upload_folder, 'profiles'), exist_ok=True)
        os.makedirs(os.path.join(upload_folder, 'logos'), exist_ok=True)

    # Register blueprints
    from app.routes import auth, users, jobs, applications, profiles, job_alerts, admin, contact, oauth, saved_jobs, cv_analysis, notifications

    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(applications.bp)
    app.register_blueprint(profiles.bp)
    app.register_blueprint(job_alerts.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(contact.bp)
    app.register_blueprint(oauth.bp)
    app.register_blueprint(saved_jobs.bp)
    app.register_blueprint(cv_analysis.cv_analysis_bp)
    app.register_blueprint(notifications.notifications_bp)

    # Initialize OAuth
    from app.routes.oauth import init_oauth
    init_oauth(app)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'WebCV Backend API is running'}, 200

    # Root endpoint
    @app.route('/')
    def index():
        return {
            'message': 'WebCV Backend API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth/*',
                'users': '/api/users/*',
                'jobs': '/api/jobs/*',
                'applications': '/api/applications/*',
                'profiles': '/api/profiles/*',
                'job_alerts': '/api/job-alerts/*',
                'admin': '/api/admin/*',
                'contact': '/api/contact'
            }
        }, 200

    return app
