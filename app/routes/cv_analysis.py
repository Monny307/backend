"""
CV Analysis API Route
Extracts text from CV (with OCR for scanned PDFs) and gets ML recommendations
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import tempfile
import requests
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from app import db
from app.models import CV, CVKeyword, Profile
from app.utils.cv_text_extractor import CVTextExtractor

cv_analysis_bp = Blueprint('cv_analysis', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
ML_API_URL = 'http://138.197.13.244:8000/upload'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@cv_analysis_bp.route('/api/analyze-cv', methods=['POST'])
@jwt_required()
def analyze_cv():
    """
    Analyze CV with OCR support and ML recommendations
    1. Extract text from CV (with OCR if needed)
    2. Forward to ML API for job recommendations
    3. Save CV to database with extracted info
    4. Save keywords to cv_keywords table
    5. Return combined results
    """
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF, DOC, DOCX allowed'}), 400
    
    try:
        # Get user's profile
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        print(f"📄 Processing CV: {filename}")
        
        # Extract text using our OCR-enabled extractor
        extractor = CVTextExtractor()
        result = extractor.extract_from_file(temp_path)
        
        extracted_text = result.get('full_text', '')
        extraction_method = result.get('method', 'unknown')
        parsed_fields = result.get('parsed_fields', {})
        
        print(f"✅ Extracted {len(extracted_text)} characters using {extraction_method}")
        
        if len(extracted_text) < 50:
            os.unlink(temp_path)
            return jsonify({
                'error': 'Could not extract enough text from CV. Please ensure it\'s a valid document.',
                'extracted_text': extracted_text,
                'extracted_text_length': len(extracted_text)
            }), 400
        
        # Save CV file permanently (no file storage - only info in DB)
        cv_name = f"{filename.rsplit('.', 1)[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Forward to ML API for recommendations
        recommendations = []
        ml_error = None
        
        try:
            print("🤖 Sending to ML API for recommendations...")
            
            # Reopen the file to send to ML API
            with open(temp_path, 'rb') as f:
                files = {'file': (filename, f, file.content_type)}
                ml_response = requests.post(ML_API_URL, files=files, timeout=180)
            
            if ml_response.status_code == 200:
                ml_data = ml_response.json()
                recommendations = ml_data.get('recommendations', [])
                print(f"✅ Got {len(recommendations)} recommendations from ML API")
            else:
                ml_error = f'ML API returned {ml_response.status_code}'
                print(f"⚠️ ML API error: {ml_error}")
                
        except requests.exceptions.Timeout:
            ml_error = 'ML API timeout (may be starting up, please retry)'
            print(f"⚠️ {ml_error}")
            
        except Exception as e:
            ml_error = str(e)
            print(f"❌ ML API error: {ml_error}")
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Mark all previous CVs as inactive
        CV.query.filter_by(profile_id=profile.id, is_active=True).update({'is_active': False})
        
        # Create new CV record (without file storage)
        new_cv = CV(
            profile_id=profile.id,
            name=cv_name,
            file_path='',  # No file storage
            status='completed',
            is_active=True,
            extracted_fullname=parsed_fields.get('name', ''),
            extracted_email=parsed_fields.get('email', ''),
            extracted_phone=parsed_fields.get('phone', ''),
            extracted_location=parsed_fields.get('location', ''),
            extracted_summary=parsed_fields.get('summary', ''),
            extracted_data=parsed_fields
        )
        db.session.add(new_cv)
        db.session.flush()  # Get the CV ID
        
        # Save keywords if we have recommendations
        if recommendations:
            keywords = [rec.get('job_title', '') for rec in recommendations]
            cv_keyword = CVKeyword(
                cv_id=new_cv.id,
                keywords=keywords,
                extracted_text=extracted_text[:5000],  # Store first 5000 chars
                extraction_method=extraction_method
            )
            db.session.add(cv_keyword)
        
        db.session.commit()
        print(f"💾 Saved CV: {cv_name} (ID: {new_cv.id})")
        
        # Return response
        return jsonify({
            'cv_id': str(new_cv.id),
            'cv_name': cv_name,
            'extracted_text': extracted_text,
            'extracted_text_length': len(extracted_text),
            'extraction_method': extraction_method,
            'recommendations': recommendations,
            'ocr_used': extraction_method == 'ocr',
            'ml_error': ml_error
        }), 200
    
    except Exception as e:
        print(f"❌ Error processing CV: {e}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return jsonify({'error': f'Failed to process CV: {str(e)}'}), 500
