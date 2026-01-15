from app import create_app, db
from app.models import User, Job, Application, Profile, CV, SavedJob, JobAlert
from flask import send_from_directory, jsonify
from flask_migrate import upgrade
import os

app = create_app()


@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded files"""
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)


@app.route('/api/migrate', methods=['POST'])
def run_migrations():
    """Run database migrations - call once after deployment"""
    try:
        upgrade()
        return jsonify({'message': 'Migrations completed successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.shell_context_processor
def make_shell_context():
    """Register shell context for flask shell"""
    return {
        'db': db,
        'User': User,
        'Job': Job,
        'Application': Application,
        'Profile': Profile,
        'CV': CV,
        'SavedJob': SavedJob,
        'JobAlert': JobAlert
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
