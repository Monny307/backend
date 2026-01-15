from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Job, SavedJob
import uuid

bp = Blueprint('saved_jobs', __name__, url_prefix='/api/saved-jobs')


@bp.route('', methods=['GET'])
@jwt_required()
def list_saved_jobs():
    """List current user's saved jobs."""
    try:
        user_id = get_jwt_identity()
        saved = (
            SavedJob.query
            .filter_by(user_id=user_id)
            .order_by(SavedJob.created_at.desc())
            .all()
        )

        return jsonify({
            'success': True,
            'saved_jobs': [s.to_dict(include_job=True) for s in saved]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/ids', methods=['GET'])
@jwt_required()
def list_saved_job_ids():
    """Return just the job IDs the user has saved (for heart icons)."""
    try:
        user_id = get_jwt_identity()
        ids = (
            db.session.query(SavedJob.job_id)
            .filter(SavedJob.user_id == user_id)
            .all()
        )
        return jsonify({
            'success': True,
            'job_ids': [str(row[0]) for row in ids]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<job_id>', methods=['GET'])
@jwt_required()
def get_saved_status(job_id):
    """Check whether a job is saved by the current user."""
    try:
        user_id = get_jwt_identity()
        try:
            job_uuid = uuid.UUID(str(job_id))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid job id'}), 400

        exists = SavedJob.query.filter_by(user_id=user_id, job_id=job_uuid).first() is not None
        return jsonify({'success': True, 'saved': exists}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<job_id>', methods=['POST'])
@jwt_required()
def save_job(job_id):
    """Save a job for the current user."""
    try:
        user_id = get_jwt_identity()

        try:
            job_uuid = uuid.UUID(str(job_id))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid job id'}), 400

        job = Job.query.get(job_uuid)
        if not job:
            return jsonify({'success': False, 'message': 'Job not found'}), 404

        existing = SavedJob.query.filter_by(user_id=user_id, job_id=job_uuid).first()
        if existing:
            return jsonify({
                'success': True,
                'message': 'Job already saved',
                'saved_job': existing.to_dict(include_job=True)
            }), 200

        saved_job = SavedJob(user_id=user_id, job_id=job_uuid)
        db.session.add(saved_job)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Job saved successfully',
            'saved_job': saved_job.to_dict(include_job=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/<job_id>', methods=['DELETE'])
@jwt_required()
def unsave_job(job_id):
    """Remove a job from the current user's saved list."""
    try:
        user_id = get_jwt_identity()

        try:
            job_uuid = uuid.UUID(str(job_id))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid job id'}), 400

        existing = SavedJob.query.filter_by(user_id=user_id, job_id=job_uuid).first()
        if not existing:
            return jsonify({'success': True, 'message': 'Job was not saved'}), 200

        db.session.delete(existing)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Job unsaved successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
