from flask import Blueprint, request, jsonify
from app import db
from app.models import Application, Job, User
from app.utils import user_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
import uuid

bp = Blueprint('applications', __name__, url_prefix='/api/applications')


@bp.route('', methods=['GET'])
@jwt_required()
@user_required
def get_applications():
    """Get user's job applications"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', '', type=str)
        
        query = Application.query.filter_by(user_id=current_user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(Application.applied_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'applications': [app.to_dict() for app in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<application_id>', methods=['GET'])
@jwt_required()
@user_required
def get_application(application_id):
    """Get specific application"""
    try:
        current_user_id = get_jwt_identity()
        application = Application.query.get(application_id)
        
        if not application:
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        
        # Check ownership
        if str(application.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('', methods=['POST'])
@jwt_required()
@user_required
def create_application():
    """Apply for a job"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('job_id'):
            return jsonify({'success': False, 'message': 'job_id is required'}), 400
        
        # Check if job exists
        job = Job.query.get(data['job_id'])
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        # Check if already applied
        existing = Application.query.filter_by(
            user_id=current_user_id,
            job_id=data['job_id']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Already applied to this job'}), 400
        
        # Create application
        new_application = Application(
            user_id=current_user_id,
            job_id=data['job_id'],
            status='applied',
            cover_letter=data.get('cover_letter'),
            notes=data.get('notes')
        )
        
        db.session.add(new_application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully',
            'application': new_application.to_dict()
        }), 201
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Already applied to this job'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<application_id>', methods=['PUT', 'PATCH'])
@jwt_required()
@user_required
def update_application(application_id):
    """Update application (e.g., add notes, change status)"""
    try:
        current_user_id = get_jwt_identity()
        application = Application.query.get(application_id)
        
        if not application:
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        
        # Check ownership
        if str(application.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update fields (user can update notes, cover_letter, and status)
        if 'notes' in data:
            application.notes = data['notes']
        if 'cover_letter' in data:
            application.cover_letter = data['cover_letter']
        if 'status' in data:
            # Validate status
            valid_statuses = ['applied', 'reviewed', 'interview', 'offer', 'rejected', 'withdrawn']
            if data['status'].lower() not in valid_statuses:
                return jsonify({'success': False, 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            application.status = data['status'].lower()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application updated successfully',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<application_id>', methods=['DELETE'])
@jwt_required()
@user_required
def delete_application(application_id):
    """Withdraw application"""
    try:
        current_user_id = get_jwt_identity()
        application = Application.query.get(application_id)
        
        if not application:
            return jsonify({'success': False, 'message': 'Application not found'}), 404
        
        # Check ownership
        if str(application.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        db.session.delete(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application withdrawn successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/check/<job_id>', methods=['GET'])
@jwt_required()
@user_required
def check_application(job_id):
    """Check if user has applied to a job"""
    try:
        current_user_id = get_jwt_identity()
        
        application = Application.query.filter_by(
            user_id=current_user_id,
            job_id=job_id
        ).first()
        
        return jsonify({
            'success': True,
            'has_applied': application is not None,
            'application': application.to_dict() if application else None
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/manual', methods=['POST'])
@jwt_required()
@user_required
def create_manual_application():
    """Create a manual application entry (stores job details in application)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields for manual entry
        if not data.get('title') or not data.get('company'):
            return jsonify({'success': False, 'message': 'Title and company are required'}), 400
        
        # Create the application with job details stored directly
        new_application = Application(
            user_id=current_user_id,
            job_id=None,  # Manual entry has no job_id
            job_title=data['title'],
            company=data['company'],
            location=data.get('location', 'Not specified'),
            salary=data.get('salary', 'Not specified'),
            job_type=data.get('job_type', 'Not specified'),
            status=data.get('status', 'applied').lower(),
            notes=data.get('notes')
        )
        
        db.session.add(new_application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Manual application added successfully',
            'application': new_application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500

