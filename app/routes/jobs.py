from flask import Blueprint, request, jsonify
from app import db
from app.models import Job
from app.utils import admin_required
# from app.utils.translator import translate_job_title, detect_language
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')


@bp.route('', methods=['GET'])
def get_jobs():
    """Get all jobs with filters and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        category = request.args.get('category', '', type=str)
        job_type = request.args.get('jobType', '', type=str)
        location = request.args.get('location', '', type=str)
        status = request.args.get('status', 'active', type=str)
        
        query = Job.query
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        
        if search:
            query = query.filter(
                (Job.title.ilike(f'%{search}%')) |
                (Job.company.ilike(f'%{search}%')) |
                (Job.description.ilike(f'%{search}%'))
            )
        
        if category:
            query = query.filter_by(category=category)
        
        if job_type:
            query = query.filter_by(job_type=job_type)
        
        if location:
            query = query.filter(Job.location.ilike(f'%{location}%'))
        
        # Paginate
        pagination = query.order_by(Job.posted_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Add translations for Khmer job titles (temporarily disabled - Python 3.13 compatibility)
        jobs_with_translations = []
        for job in pagination.items:
            job_dict = job.to_dict()
            # TODO: Re-enable translation when Python 3.13 compatible version available
            job_dict['title_en'] = job_dict['title']  # Use original title for now
            job_dict['title_original'] = job_dict['title']
            job_dict['is_khmer'] = False
            jobs_with_translations.append(job_dict)
        
        return jsonify({
            'success': True,
            'jobs': jobs_with_translations,
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get job by ID"""
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


@bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_job():
    """Create a new job (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'company', 'location', 'job_type', 'category', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        new_job = Job(
            title=data['title'],
            company=data['company'],
            location=data['location'],
            salary=data.get('salary'),
            job_type=data['job_type'],
            category=data['category'],
            description=data['description'],
            requirements=data.get('requirements'),
            logo=data.get('logo'),
            status=data.get('status', 'active'),
            posted_date=datetime.utcnow()
        )
        
        db.session.add(new_job)
        db.session.commit()
        
        # Create notifications for matching CVs
        from app.routes.notifications import check_and_create_notifications
        check_and_create_notifications(str(new_job.id))
        
        return jsonify({
            'success': True,
            'message': 'Job created successfully',
            'job': new_job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<job_id>', methods=['PUT', 'PATCH'])
@jwt_required()
@admin_required
def update_job(job_id):
    """Update job (admin only)"""
    try:
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        updatable_fields = ['title', 'company', 'location', 'salary', 'job_type', 
                           'category', 'description', 'requirements', 'logo', 'status']
        
        for field in updatable_fields:
            if field in data:
                setattr(job, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job updated successfully',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<job_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_job(job_id):
    """Delete job (admin only)"""
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


@bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all job categories"""
    try:
        categories = db.session.query(Job.category).distinct().all()
        category_list = [cat[0] for cat in categories]
        
        return jsonify({
            'success': True,
            'categories': category_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/types', methods=['GET'])
def get_job_types():
    """Get all job types"""
    try:
        job_types = db.session.query(Job.job_type).distinct().all()
        type_list = [jt[0] for jt in job_types]
        
        return jsonify({
            'success': True,
            'job_types': type_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
