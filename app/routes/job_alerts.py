from flask import Blueprint, request, jsonify
from app import db
from app.models import JobAlert
from app.utils import user_required
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('job_alerts', __name__, url_prefix='/api/job-alerts')


@bp.route('', methods=['GET'])
@jwt_required()
@user_required
def get_job_alerts():
    """Get user's job alerts"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = JobAlert.query.filter_by(user_id=current_user_id).order_by(
            JobAlert.created_date.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'job_alerts': [alert.to_dict() for alert in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<alert_id>', methods=['GET'])
@jwt_required()
@user_required
def get_job_alert(alert_id):
    """Get specific job alert"""
    try:
        current_user_id = get_jwt_identity()
        alert = JobAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({'success': False, 'message': 'Job alert not found'}), 404
        
        if str(alert.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'job_alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('', methods=['POST'])
@jwt_required()
@user_required
def create_job_alert():
    """Create a new job alert"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'}), 400
        
        new_alert = JobAlert(
            user_id=current_user_id,
            title=data['title'],
            keywords=data.get('keywords'),
            location=data.get('location'),
            category=data.get('category'),
            job_type=data.get('job_type'),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            frequency=data.get('frequency', 'daily'),
            is_active=True
        )
        
        db.session.add(new_alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job alert created successfully',
            'job_alert': new_alert.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<alert_id>', methods=['PUT', 'PATCH'])
@jwt_required()
@user_required
def update_job_alert(alert_id):
    """Update job alert"""
    try:
        current_user_id = get_jwt_identity()
        alert = JobAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({'success': False, 'message': 'Job alert not found'}), 404
        
        if str(alert.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        updatable_fields = ['title', 'keywords', 'location', 'category', 'job_type',
                           'salary_min', 'salary_max', 'frequency', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(alert, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job alert updated successfully',
            'job_alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<alert_id>', methods=['DELETE'])
@jwt_required()
@user_required
def delete_job_alert(alert_id):
    """Delete job alert"""
    try:
        current_user_id = get_jwt_identity()
        alert = JobAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({'success': False, 'message': 'Job alert not found'}), 404
        
        if str(alert.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Job alert deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<alert_id>/toggle', methods=['POST'])
@jwt_required()
@user_required
def toggle_job_alert(alert_id):
    """Toggle job alert active status"""
    try:
        current_user_id = get_jwt_identity()
        alert = JobAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({'success': False, 'message': 'Job alert not found'}), 404
        
        if str(alert.user_id) != current_user_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        alert.is_active = not alert.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Job alert {"activated" if alert.is_active else "deactivated"}',
            'job_alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
