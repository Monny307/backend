from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Job, Application
from app.utils import admin_required
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
from flask import current_app

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_stats():
    """Get dashboard statistics"""
    try:
        # Total counts
        total_users = User.query.filter_by(role='user').count()
        total_jobs = Job.query.count()
        
        # Active jobs are those with deadline in the future or no deadline set
        now = datetime.utcnow()
        active_jobs = Job.query.filter(
            db.or_(
                Job.deadline.is_(None),
                Job.deadline > now
            )
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_jobs': total_jobs,
                'active_jobs': active_jobs
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        role = request.args.get('role', '', type=str)
        
        query = User.query
        
        if search:
            query = query.filter(
                (User.fullname.ilike(f'%{search}%')) |
                (User.email.ilike(f'%{search}%'))
            )
        
        if role:
            query = query.filter_by(role=role)
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@jwt_required()
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {"activated" if user.is_active else "deactivated"}',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/applications', methods=['GET'])
@jwt_required()
@admin_required
def get_all_applications():
    """Get all applications"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '', type=str)
        job_id = request.args.get('job_id', '', type=str)
        
        query = Application.query
        
        if status:
            query = query.filter_by(status=status)
        
        if job_id:
            query = query.filter_by(job_id=job_id)
        
        pagination = query.order_by(Application.applied_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'applications': [app.to_dict() for app in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/applications/<application_id>/status', methods=['PUT'])
@jwt_required()
@admin_required
def update_application_status(application_id):
    """Update application status"""
    try:
        application = Application.query.get(application_id)
        
        if not application:
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        application.status = data['status']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application status updated',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/jobs/<job_id>/applications', methods=['GET'])
@jwt_required()
@admin_required
def get_job_applications(job_id):
    """Get all applications for a specific job"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        pagination = Application.query.filter_by(job_id=job_id).order_by(
            Application.applied_date.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'job': job.to_dict(),
            'applications': [app.to_dict() for app in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


# ============ JOB MANAGEMENT ENDPOINTS ============

@bp.route('/jobs', methods=['GET'])
@jwt_required()
@admin_required
def get_jobs():
    """Get all jobs with filters and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        status = request.args.get('status', '', type=str)
        category = request.args.get('category', '', type=str)
        
        query = Job.query
        
        if search:
            query = query.filter(
                (Job.title.ilike(f'%{search}%')) |
                (Job.company.ilike(f'%{search}%')) |
                (Job.location.ilike(f'%{search}%'))
            )
        
        if status:
            query = query.filter_by(status=status)
        
        if category:
            query = query.filter_by(category=category)
        
        pagination = query.order_by(Job.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/jobs', methods=['POST'])
@jwt_required()
@admin_required
def create_job():
    """Create a new job"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'company', 'location', 'job_type', 'category', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Parse deadline if provided
        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except:
                pass
        
        new_job = Job(
            title=data['title'],
            company=data['company'],
            location=data['location'],
            salary=data.get('salary', ''),
            job_type=data['job_type'],
            category=data['category'],
            description=data['description'],
            requirements=data.get('requirements', ''),
            logo=data.get('logo', ''),
            status=data.get('status', 'active'),
            deadline=deadline
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job created successfully',
            'job': new_job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/jobs/<job_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_job(job_id):
    """Get a single job by ID"""
    try:
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/jobs/<job_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_job(job_id):
    """Update a job"""
    try:
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            job.title = data['title']
        if 'company' in data:
            job.company = data['company']
        if 'location' in data:
            job.location = data['location']
        if 'salary' in data:
            job.salary = data['salary']
        if 'job_type' in data:
            job.job_type = data['job_type']
        if 'category' in data:
            job.category = data['category']
        if 'deadline' in data:
            if data['deadline']:
                try:
                    job.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
                except:
                    pass
            else:
                job.deadline = None
        if 'description' in data:
            job.description = data['description']
        if 'requirements' in data:
            job.requirements = data['requirements']
        if 'logo' in data:
            job.logo = data['logo']
        if 'status' in data:
            job.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job updated successfully',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/jobs/<job_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_job(job_id):
    """Delete a job"""
    try:
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/jobs/<job_id>/toggle-status', methods=['POST'])
@jwt_required()
@admin_required
def toggle_job_status(job_id):
    """Toggle job status (active/inactive)"""
    try:
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        job.status = 'inactive' if job.status == 'active' else 'active'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Job status changed to {job.status}',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/upload-logo', methods=['POST'])
@jwt_required()
@admin_required
def upload_logo():
    """Upload company logo"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Check file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: jpg, jpeg, png, gif, svg, webp'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Save file
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logos')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Return relative path for database storage
        relative_path = f"/uploads/logos/{unique_filename}"
        
        return jsonify({
            'success': True,
            'message': 'Logo uploaded successfully',
            'file_path': relative_path
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
