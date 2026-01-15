from flask import Blueprint, request, jsonify, current_app, send_file
from app import db
from app.models import Profile, User, CV, CVKeyword
from app.utils import user_required, allowed_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
import uuid
import requests
from io import BytesIO

# Optional, heavy dependencies (docx/pdf/ocr + reportlab). These are only
# needed for CV upload/parsing and PDF export. Make them optional so the API
# can still run core features (auth, jobs, saved jobs, etc.).
try:
    from app.utils.cv_text_extractor import extract_cv_text  # type: ignore
except Exception:  # pragma: no cover
    extract_cv_text = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
except Exception:  # pragma: no cover
    letter = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    inch = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None
    colors = None

bp = Blueprint('profiles', __name__, url_prefix='/api')


@bp.route('/profile', methods=['GET'])
@jwt_required()
@user_required
def get_profile():
    """Get user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            # Create profile if it doesn't exist
            profile = Profile(user_id=current_user_id)
            db.session.add(profile)
            db.session.commit()
        
        profile_data = profile.to_dict()
        profile_data['fullname'] = user.fullname
        profile_data['account_email'] = user.email  # Account email for reference
        # profile_data['email'] is already from CV (from to_dict)
        
        return jsonify({
            'success': True,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile', methods=['PUT', 'PATCH'])
@jwt_required()
@user_required
def update_profile():
    """Update user's profile"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            profile = Profile(user_id=current_user_id)
            db.session.add(profile)
        
        data = request.get_json()
        
        # Update basic fields (including email from CV)
        updatable_fields = ['email', 'phone', 'gender', 'location', 'professional_summary']
        for field in updatable_fields:
            if field in data:
                setattr(profile, field, data[field])
        
        # Handle date of birth
        if 'date_of_birth' in data and data['date_of_birth']:
            from datetime import datetime
            try:
                profile.date_of_birth = datetime.fromisoformat(data['date_of_birth'].replace('Z', '+00:00')).date()
            except:
                pass
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': profile.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/photo', methods=['POST'])
@jwt_required()
@user_required
def upload_profile_photo():
    """Upload profile photo"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            profile = Profile(user_id=current_user_id)
            db.session.add(profile)
            db.session.flush()
        
        if 'profile_photo' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['profile_photo']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename, {'jpg', 'jpeg', 'png'}):
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: jpg, jpeg, png'}), 400
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        
        # Save file
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Update profile
        profile.profile_photo = f"/uploads/profiles/{filename}"
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile photo uploaded successfully',
            'profile_photo': profile.profile_photo
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


# CV Management
@bp.route('/profile/cvs', methods=['GET'])
@jwt_required()
@user_required
def get_cvs():
    """Get user's CVs"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': True, 'cvs': []}), 200
        
        cvs = CV.query.filter_by(profile_id=profile.id).order_by(CV.upload_date.desc()).all()
        
        return jsonify({
            'success': True,
            'cvs': [cv.to_dict() for cv in cvs]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/active-keywords', methods=['GET'])
@jwt_required()
@user_required
def get_active_cv_keywords():
    """Get keywords from active CV"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': True, 'keywords': []}), 200
        
        # Get active CV
        active_cv = CV.query.filter_by(profile_id=profile.id, is_active=True).first()
        
        if not active_cv:
            return jsonify({'success': True, 'keywords': []}), 200
        
        # Get keywords for active CV
        cv_keywords = CVKeyword.query.filter_by(cv_id=active_cv.id).first()
        
        if not cv_keywords:
            return jsonify({'success': True, 'keywords': []}), 200
        
        return jsonify({
            'success': True,
            'keywords': cv_keywords.keywords,
            'cv_id': str(active_cv.id),
            'cv_name': active_cv.name,
            'extraction_method': cv_keywords.extraction_method
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/<cv_id>/keywords', methods=['GET'])
@jwt_required()
@user_required
def get_cv_keywords(cv_id):
    """Get keywords from a specific CV"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        # Get the CV and verify ownership
        cv = CV.query.filter_by(id=cv_id, profile_id=profile.id).first()
        
        if not cv:
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        # Get keywords for this CV
        cv_keywords = CVKeyword.query.filter_by(cv_id=cv.id).first()
        
        if not cv_keywords:
            return jsonify({'success': True, 'keywords': []}), 200
        
        return jsonify({
            'success': True,
            'keywords': cv_keywords.keywords,
            'cv_id': str(cv.id),
            'cv_name': cv.name,
            'extraction_method': cv_keywords.extraction_method,
            'created_at': cv_keywords.created_at.isoformat() if cv_keywords.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/<cv_id>/analyze', methods=['POST'])
@jwt_required()
@user_required
def analyze_existing_cv(cv_id):
    """Analyze an existing CV to generate keywords and recommendations"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        # Get the CV and verify ownership
        cv = CV.query.filter_by(id=cv_id, profile_id=profile.id).first()
        
        if not cv:
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        # Check if CV already has extracted text
        extracted_text = ''
        if cv.extracted_data and cv.extracted_data.get('full_text'):
            extracted_text = cv.extracted_data.get('full_text', '')
        
        # If no extracted text, try to get from summary and other fields
        if not extracted_text:
            parts = []
            if cv.extracted_fullname:
                parts.append(f"Name: {cv.extracted_fullname}")
            if cv.extracted_email:
                parts.append(f"Email: {cv.extracted_email}")
            if cv.extracted_phone:
                parts.append(f"Phone: {cv.extracted_phone}")
            if cv.extracted_location:
                parts.append(f"Location: {cv.extracted_location}")
            if cv.extracted_summary:
                parts.append(f"Summary: {cv.extracted_summary}")
            
            # Add education, experience, skills from extracted_data
            if cv.extracted_data:
                if cv.extracted_data.get('education'):
                    parts.append(f"Education: {' '.join(map(str, cv.extracted_data['education']))}")
                if cv.extracted_data.get('experience'):
                    parts.append(f"Experience: {' '.join(map(str, cv.extracted_data['experience']))}")
                if cv.extracted_data.get('skills'):
                    parts.append(f"Skills: {' '.join(map(str, cv.extracted_data['skills']))}")
            
            extracted_text = '\n'.join(parts)
        
        if len(extracted_text) < 50:
            return jsonify({
                'success': False,
                'message': 'Not enough text data in CV to analyze. Please upload a new CV file.'
            }), 400
        
        # Send to ML API for analysis
        ML_API_URL = 'http://138.197.13.244:8000/upload'
        
        try:
            # Create a text file from extracted data
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(extracted_text)
                temp_path = tmp_file.name
            
            # Send to ML API
            with open(temp_path, 'rb') as f:
                files = {'file': (f'{cv.name}.txt', f, 'text/plain')}
                ml_response = requests.post(ML_API_URL, files=files, timeout=180)
            
            os.unlink(temp_path)
            
            if ml_response.status_code == 200:
                ml_data = ml_response.json()
                recommendations = ml_data.get('recommendations', [])
                
                if recommendations:
                    # Save or update keywords
                    keywords = [rec.get('job_title', '') for rec in recommendations]
                    
                    existing_keywords = CVKeyword.query.filter_by(cv_id=cv.id).first()
                    if existing_keywords:
                        existing_keywords.keywords = keywords
                        existing_keywords.extracted_text = extracted_text[:5000]
                        existing_keywords.extraction_method = 'text'
                    else:
                        cv_keyword = CVKeyword(
                            cv_id=cv.id,
                            keywords=keywords,
                            extracted_text=extracted_text[:5000],
                            extraction_method='text'
                        )
                        db.session.add(cv_keyword)
                    
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'keywords': keywords,
                        'cv_id': str(cv.id),
                        'cv_name': cv.name,
                        'extraction_method': 'text',
                        'recommendations': recommendations
                    }), 200
                else:
                    return jsonify({
                        'success': False,
                        'message': 'ML API returned no recommendations'
                    }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': f'ML API error: {ml_response.status_code}'
                }), 400
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'message': 'ML API timeout. Please try again.'
            }), 408
            
        except Exception as ml_error:
            return jsonify({
                'success': False,
                'message': f'ML API error: {str(ml_error)}'
            }), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs', methods=['POST'])
@jwt_required()
@user_required
def upload_cv():
    """Upload CV"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            profile = Profile(user_id=current_user_id)
            db.session.add(profile)
            db.session.flush()
        
        if 'cv' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['cv']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename, {'pdf', 'doc', 'docx'}):
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: pdf, doc, docx'}), 400
        
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        
        # Save file
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cvs')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Extract text from CV
        extraction_result = None
        try:
            extraction_result = extract_cv_text(filepath)
            print(f"CV text extracted successfully using {extraction_result.get('extraction_method')}")
        except Exception as e:
            print(f"Warning: Could not extract CV text: {str(e)}")
            # Continue even if extraction fails
        
        # Create CV record
        cv = CV(
            profile_id=profile.id,
            name=request.form.get('name', file.filename),
            file_path=f"/uploads/cvs/{filename}",
            status='completed',
            is_active=False
        )
        
        db.session.add(cv)
        db.session.flush()
        
        # Auto-populate profile fields if extraction was successful
        if extraction_result and extraction_result.get('parsed_fields'):
            parsed = extraction_result['parsed_fields']
            
            # Store ALL extracted data as JSON in the CV record
            print(f"Storing extracted data for CV: {cv.name} (ID: {cv.id})")
            cv.extracted_data = parsed  # Store complete extraction as JSON
            
            # Also store key fields in dedicated columns for easy access and quick queries
            if parsed.get('name'):
                cv.extracted_fullname = parsed['name'][:200]
            if parsed.get('email'):
                cv.extracted_email = parsed['email'][:120]
            if parsed.get('phone'):
                cv.extracted_phone = parsed['phone'][:50]
            if parsed.get('location'):
                cv.extracted_location = parsed['location']
            if parsed.get('summary'):
                cv.extracted_summary = parsed['summary']
            
            # Update user's fullname if extracted and not set
            user = User.query.get(current_user_id)
            if parsed.get('name') and (not user.fullname or user.fullname == 'User'):
                user.fullname = parsed['name']
            
            # Update profile email (shared across CVs for login)
            if parsed.get('email'):
                profile.email = parsed['email']
            
            print(f"Extracted data stored as JSON. Fields: {list(parsed.keys())}")
            print(f"Personal info: name={parsed.get('name')}, email={parsed.get('email')}, phone={parsed.get('phone')}, skills={len(parsed.get('skills', []))}, education={len(parsed.get('education', []))}")
        
        db.session.commit()
        
        response_data = {
            'success': True,
            'message': 'CV uploaded and processed successfully',
            'cv': cv.to_dict()
        }
        
        # Include extraction data if available
        if extraction_result:
            response_data['extraction'] = {
                'method': extraction_result.get('extraction_method'),
                'fields_extracted': list(extraction_result.get('parsed_fields', {}).keys())
            }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/<cv_id>/set-active', methods=['POST'])
@jwt_required()
@user_required
def set_active_cv(cv_id):
    """Set CV as active"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        cv = CV.query.get(cv_id)
        
        if not cv or str(cv.profile_id) != str(profile.id):
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        # Deactivate all CVs
        CV.query.filter_by(profile_id=profile.id).update({'is_active': False})
        
        # Activate selected CV
        cv.is_active = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'CV set as active',
            'cv': cv.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/<cv_id>', methods=['DELETE'])
@jwt_required()
@user_required
def delete_cv(cv_id):
    """Delete CV"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        cv = CV.query.get(cv_id)
        
        if not cv or str(cv.profile_id) != str(profile.id):
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        # Delete file
        if cv.file_path:
            try:
                file_path = os.path.join(current_app.root_path, '..', cv.file_path.lstrip('/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        db.session.delete(cv)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'CV deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/create', methods=['POST'])
@jwt_required()
@user_required
def create_cv_from_profile():
    """Create CV from profile data"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            profile = Profile(user_id=current_user_id)
            db.session.add(profile)
            db.session.flush()
        
        data = request.get_json()
        cv_name = data.get('name', 'My CV')
        
        # Create CV record without file (user built it)
        cv = CV(
            profile_id=profile.id,
            name=cv_name,
            file_path=None,  # No file, built from profile
            status='completed',
            is_active=data.get('is_active', False)
        )
        
        # If this is set as active, deactivate others
        if cv.is_active:
            CV.query.filter_by(profile_id=profile.id).update({'is_active': False})
        
        db.session.add(cv)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'CV created successfully',
            'cv': cv.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/<cv_id>/data', methods=['GET'])
@jwt_required()
@user_required
def get_cv_data(cv_id):
    """Get CV-specific data including all extracted information"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        user = User.query.get(current_user_id)
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        cv = CV.query.get(cv_id)
        
        if not cv or str(cv.profile_id) != str(profile.id):
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        # Priority: cv_builder_data (manually edited) > extracted_data (from upload) > defaults
        builder_data = cv.cv_builder_data or {}
        extracted = cv.extracted_data or {}
        
        cv_data = {
            'cv': cv.to_dict(),
            'fullname': builder_data.get('fullname') or extracted.get('name') or user.fullname,
            'email': builder_data.get('email') or extracted.get('email') or profile.email,
            'phone': builder_data.get('phone') or extracted.get('phone'),
            'location': builder_data.get('location') or extracted.get('location'),
            'professional_summary': builder_data.get('professional_summary') or extracted.get('summary'),
            'educations': builder_data.get('educations') or extracted.get('education', []),
            'experiences': builder_data.get('experiences') or extracted.get('experience', []),
            'skills': builder_data.get('skills') or [{'name': s, 'level': 'Intermediate'} for s in extracted.get('skills', [])],
            'languages': builder_data.get('languages') or extracted.get('languages', []),
            'certifications': builder_data.get('certifications') or extracted.get('certifications', [])
        }
        
        return jsonify({
            'success': True,
            'data': cv_data
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


# CV Builder Data Management
@bp.route('/profile/cvs/<cv_id>/builder-data', methods=['PUT'])
@jwt_required()
@user_required
def save_cv_builder_data(cv_id):
    """Save CV builder data (educations, experiences, skills, languages, certifications, etc.)"""
    try:
        current_user_id = get_jwt_identity()
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        cv = CV.query.get(cv_id)
        
        if not cv or str(cv.profile_id) != str(profile.id):
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        data = request.get_json()
        
        # Store complete CV builder data as JSON
        cv.cv_builder_data = {
            'fullname': data.get('fullname'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'location': data.get('location'),
            'professional_summary': data.get('professional_summary'),
            'educations': data.get('educations', []),
            'experiences': data.get('experiences', []),
            'skills': data.get('skills', []),
            'languages': data.get('languages', []),
            'certifications': data.get('certifications', [])
        }
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'CV data saved successfully',
            'cv': cv.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500


@bp.route('/profile/cvs/<cv_id>/download', methods=['GET'])
@jwt_required()
@user_required
def download_cv(cv_id):
    """Download CV as PDF"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        profile = Profile.query.filter_by(user_id=current_user_id).first()
        
        if not profile:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        
        cv = CV.query.get(cv_id)
        
        if not cv or str(cv.profile_id) != str(profile.id):
            return jsonify({'success': False, 'message': 'CV not found'}), 404
        
        # If CV has a file, send it
        if cv.file_path:
            filepath = os.path.join(current_app.config['BASE_DIR'], cv.file_path.lstrip('/'))
            if os.path.exists(filepath):
                return send_file(filepath, as_attachment=True, download_name=f"{cv.name}.pdf")
        
        # Generate PDF from CV data (builder_data or extracted_data)
        builder_data = cv.cv_builder_data or {}
        extracted = cv.extracted_data or {}
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF8C42'),
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#FF8C42'),
            spaceAfter=12,
            spaceBefore=12,
        )
        
        # Add name and contact info
        fullname = builder_data.get('fullname') or extracted.get('name') or user.fullname
        elements.append(Paragraph(fullname or 'Professional CV', title_style))
        
        email_val = builder_data.get('email') or extracted.get('email') or profile.email
        phone_val = builder_data.get('phone') or extracted.get('phone') or profile.phone
        location_val = builder_data.get('location') or extracted.get('location') or profile.location
        
        if email_val or phone_val or location_val:
            contact_info = []
            if email_val:
                contact_info.append(f"Email: {email_val}")
            if phone_val:
                contact_info.append(f"Phone: {phone_val}")
            if location_val:
                contact_info.append(f"Location: {location_val}")
            elements.append(Paragraph(" | ".join(contact_info), styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Professional Summary
        summary = builder_data.get('professional_summary') or extracted.get('summary') or profile.professional_summary
        if summary:
            elements.append(Paragraph("Professional Summary", heading_style))
            elements.append(Paragraph(summary, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Education
        educations = builder_data.get('educations') or extracted.get('education', [])
        if educations:
            elements.append(Paragraph("Education", heading_style))
            for edu in educations:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                year = edu.get('year', '')
                description = edu.get('description', '')
                elements.append(Paragraph(f"<b>{degree}</b> - {institution} ({year})", styles['Normal']))
                if description:
                    elements.append(Paragraph(description, styles['Normal']))
                elements.append(Spacer(1, 6))
        
        # Experience
        experiences = builder_data.get('experiences') or extracted.get('experience', [])
        if experiences:
            elements.append(Paragraph("Work Experience", heading_style))
            for exp in experiences:
                title = exp.get('title', '')
                company = exp.get('company', '')
                duration = exp.get('duration', '')
                description = exp.get('description', '')
                elements.append(Paragraph(f"<b>{title}</b> - {company} ({duration})", styles['Normal']))
                if description:
                    elements.append(Paragraph(description, styles['Normal']))
                elements.append(Spacer(1, 6))
        
        # Skills
        skills = builder_data.get('skills', [])
        if not skills and extracted.get('skills'):
            skills = [{'name': s, 'level': 'Intermediate'} for s in extracted.get('skills', [])]
        if skills:
            elements.append(Paragraph("Skills", heading_style))
            skills_text = ", ".join([f"{skill.get('name', '')} ({skill.get('level', '')})" for skill in skills])
            elements.append(Paragraph(skills_text, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Languages
        languages = builder_data.get('languages') or extracted.get('languages', [])
        if languages:
            elements.append(Paragraph("Languages", heading_style))
            lang_text = ", ".join([f"{lang.get('language', '')} ({lang.get('proficiency', '')})" for lang in languages])
            elements.append(Paragraph(lang_text, styles['Normal']))
            elements.append(Spacer(1, 12))
        
        # Certifications
        certifications = builder_data.get('certifications') or extracted.get('certifications', [])
        if certifications:
            elements.append(Paragraph("Certifications", heading_style))
            for cert in certifications:
                name = cert.get('name', '')
                organization = cert.get('organization', '')
                year = cert.get('year', '')
                description = cert.get('description', '')
                elements.append(Paragraph(f"<b>{name}</b> - {organization} ({year})", styles['Normal']))
                if description:
                    elements.append(Paragraph(description, styles['Normal']))
                elements.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{cv.name}.pdf"
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
