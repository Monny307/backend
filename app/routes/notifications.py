from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Profile, CV, CVKeyword, Job, JobNotification
from functools import wraps
import jwt
from config import Config
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except Exception as e:
            return jsonify({'error': 'Token is invalid', 'details': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


@notifications_bp.route('/api/notifications/active-cv', methods=['GET'])
@token_required
def get_active_cv_notifications(current_user):
    """Get notifications for jobs matching active CV keywords"""
    try:
        # Get user's profile
        profile = Profile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            return jsonify({'notifications': []})
        
        # Get notifications for active CV
        notifications = JobNotification.query.filter_by(
            user_id=current_user.id,
            notification_type='active_cv'
        ).order_by(JobNotification.created_at.desc()).limit(50).all()
        
        # Include job details
        result = []
        for notif in notifications:
            job = Job.query.get(notif.job_id)
            if job:
                notif_dict = notif.to_dict()
                notif_dict['job'] = job.to_dict()
                result.append(notif_dict)
        
        return jsonify({'notifications': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/notifications/all-cvs', methods=['GET'])
@token_required
def get_all_cvs_notifications(current_user):
    """Get notifications for jobs matching past/inactive CV keywords"""
    try:
        # Get user's profile
        profile = Profile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            return jsonify({'notifications': []})
        
        # Get notifications for past CVs
        notifications = JobNotification.query.filter_by(
            user_id=current_user.id,
            notification_type='past_cv'
        ).order_by(JobNotification.created_at.desc()).limit(50).all()
        
        # Include job and CV details
        result = []
        for notif in notifications:
            job = Job.query.get(notif.job_id)
            cv = CV.query.get(notif.cv_id) if notif.cv_id else None
            if job:
                notif_dict = notif.to_dict()
                notif_dict['job'] = job.to_dict()
                if cv:
                    notif_dict['cv_name'] = cv.name
                result.append(notif_dict)
        
        return jsonify({'notifications': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/notifications/<notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(current_user, notification_id):
    """Mark a notification as read"""
    try:
        notification = JobNotification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Verify ownership
        if str(notification.user_id) != str(current_user.id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/api/notifications/unread-count', methods=['GET'])
@token_required
def get_unread_count(current_user):
    """Get count of unread notifications"""
    try:
        active_cv_count = JobNotification.query.filter_by(
            user_id=current_user.id,
            notification_type='active_cv',
            is_read=False
        ).count()
        
        past_cvs_count = JobNotification.query.filter_by(
            user_id=current_user.id,
            notification_type='past_cv',
            is_read=False
        ).count()
        
        return jsonify({
            'active_cv': active_cv_count,
            'past_cvs': past_cvs_count,
            'total': active_cv_count + past_cvs_count
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def check_and_create_notifications(job_id):
    """
    Check if a new job matches any user's CV keywords and create notifications.
    This function should be called after a job is added or scraped.
    """
    try:
        job = Job.query.get(job_id)
        if not job:
            return
        
        job_title_lower = job.title.lower()
        job_desc_lower = job.description.lower() if job.description else ''
        
        # Get all users with CVs
        profiles = Profile.query.all()
        
        for profile in profiles:
            # Check active CV keywords
            active_cv = CV.query.filter_by(profile_id=profile.id, is_active=True).first()
            if active_cv:
                cv_keywords = CVKeyword.query.filter_by(cv_id=active_cv.id).first()
                if cv_keywords and cv_keywords.keywords:
                    matched_keywords = []
                    for keyword in cv_keywords.keywords:
                        keyword_lower = keyword.lower()
                        if keyword_lower in job_title_lower or keyword_lower in job_desc_lower:
                            matched_keywords.append(keyword)
                    
                    # Create notification if there are matches
                    if matched_keywords:
                        # Check if notification already exists
                        existing = JobNotification.query.filter_by(
                            user_id=profile.user_id,
                            job_id=job_id,
                            notification_type='active_cv'
                        ).first()
                        
                        if not existing:
                            notification = JobNotification(
                                user_id=profile.user_id,
                                job_id=job_id,
                                cv_id=active_cv.id,
                                notification_type='active_cv',
                                matched_keywords=matched_keywords,
                                is_read=False
                            )
                            db.session.add(notification)
            
            # Check past/inactive CV keywords
            inactive_cvs = CV.query.filter_by(profile_id=profile.id, is_active=False).all()
            for cv in inactive_cvs:
                cv_keywords = CVKeyword.query.filter_by(cv_id=cv.id).first()
                if cv_keywords and cv_keywords.keywords:
                    matched_keywords = []
                    for keyword in cv_keywords.keywords:
                        keyword_lower = keyword.lower()
                        if keyword_lower in job_title_lower or keyword_lower in job_desc_lower:
                            matched_keywords.append(keyword)
                    
                    # Create notification if there are matches
                    if matched_keywords:
                        # Check if notification already exists
                        existing = JobNotification.query.filter_by(
                            user_id=profile.user_id,
                            job_id=job_id,
                            cv_id=cv.id,
                            notification_type='past_cv'
                        ).first()
                        
                        if not existing:
                            notification = JobNotification(
                                user_id=profile.user_id,
                                job_id=job_id,
                                cv_id=cv.id,
                                notification_type='past_cv',
                                matched_keywords=matched_keywords,
                                is_read=False
                            )
                            db.session.add(notification)
        
        db.session.commit()
        print(f"✅ Notifications created for job: {job.title}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating notifications: {str(e)}")
