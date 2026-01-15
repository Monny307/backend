from flask import Blueprint, request, jsonify
from app import db

bp = Blueprint('contact', __name__, url_prefix='/api/contact')


@bp.route('', methods=['POST'])
def create_contact_message():
    """Submit a contact form message - deprecated (contact_messages table removed)"""
    return jsonify({
        'success': False,
        'message': 'Contact form is currently unavailable. Please email us directly.'
    }), 503
