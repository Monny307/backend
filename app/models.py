from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='user', cascade='all, delete-orphan')
    job_alerts = db.relationship('JobAlert', backref='user', cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', backref='user', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'fullname': self.fullname,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Profile(db.Model):
    __tablename__ = 'profiles'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False, unique=True)
    email = db.Column(db.String(255))  # Email from CV (can be different from account email)
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    location = db.Column(db.String(200))
    professional_summary = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    cvs = db.relationship('CV', backref='profile', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'email': self.email,  # Email from CV
            'phone': self.phone,
            'gender': self.gender,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'location': self.location,
            'professional_summary': self.professional_summary,
            'profile_photo': self.profile_photo,
            'cvs': [cv.to_dict() for cv in self.cvs]
        }


class CV(db.Model):
    __tablename__ = 'cvs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = db.Column(UUID(as_uuid=True), db.ForeignKey('profiles.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='completed')  # 'completed', 'needs-editing'
    is_active = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Extracted data from CV - specific to each CV
    # Key fields stored as columns for quick access
    extracted_fullname = db.Column(db.String(200), nullable=True)
    extracted_email = db.Column(db.String(120), nullable=True)
    extracted_phone = db.Column(db.String(50), nullable=True)
    extracted_location = db.Column(db.Text, nullable=True)
    extracted_summary = db.Column(db.Text, nullable=True)
    
    # Complete extracted data stored as JSON for flexibility
    # Structure: {name, email, phone, location, summary, education: [...], experience: [...], skills: [...], languages: [...], certifications: [...]}
    extracted_data = db.Column(db.JSON, nullable=True)
    
    # CV Builder Data - User can manually build CV or edit extracted data
    # Structure: {fullname, email, phone, location, professional_summary, educations: [...], experiences: [...], skills: [...], languages: [...], certifications: [...]}
    cv_builder_data = db.Column(db.JSON, nullable=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'profile_id': str(self.profile_id),
            'name': self.name,
            'file_path': self.file_path,
            'status': self.status,
            'is_active': self.is_active,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'extracted_fullname': self.extracted_fullname,
            'extracted_email': self.extracted_email,
            'extracted_phone': self.extracted_phone,
            'extracted_location': self.extracted_location,
            'extracted_summary': self.extracted_summary,
            'extracted_data': self.extracted_data,
            'cv_builder_data': self.cv_builder_data
        }





class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(200), nullable=False, index=True)
    company = db.Column(db.String(200), nullable=False, index=True)
    location = db.Column(db.String(200), nullable=False)
    salary = db.Column(db.String(100))
    job_type = db.Column(db.String(50), nullable=False)  # 'Full-time', 'Part-time', 'Contract', 'Internship'
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    logo = db.Column(db.String(500))
    contact_email = db.Column(db.String(255), nullable=True)  # Contact email for applications
    contact_phone = db.Column(db.String(100), nullable=True)  # Contact phone for applications
    website = db.Column(db.String(500), nullable=True)  # Company website
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active', 'inactive'
    deadline = db.Column(db.DateTime, nullable=True)  # Application deadline
    posted_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', backref='job', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'salary': self.salary,
            'jobType': self.job_type,
            'category': self.category,
            'description': self.description,
            'requirements': self.requirements,
            'logo': self.logo,
            'contactEmail': self.contact_email,
            'contactPhone': self.contact_phone,
            'website': self.website,
            'status': self.status,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'postedDate': self.posted_date.isoformat() if self.posted_date else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }


class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.id'), nullable=True)  # Nullable for manual entries
    
    # Job details for manual applications (when job_id is NULL)
    job_title = db.Column(db.String(200), nullable=True)
    company = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    salary = db.Column(db.String(100), nullable=True)
    job_type = db.Column(db.String(50), nullable=True)
    
    status = db.Column(db.String(50), default='applied', nullable=False)  # 'applied', 'interview', 'offer', 'rejected'
    applied_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cover_letter = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # Create unique constraint only for non-manual entries
    __table_args__ = (
        db.CheckConstraint(
            'job_id IS NOT NULL OR (job_title IS NOT NULL AND company IS NOT NULL)',
            name='check_job_or_manual_fields'
        ),
    )
    
    def to_dict(self):
        # For manual applications, use stored job details
        if self.job_id is None:
            job_data = {
                'title': self.job_title,
                'company': self.company,
                'location': self.location,
                'salary': self.salary,
                'job_type': self.job_type,
                'is_manual': True
            }
        else:
            job_data = self.job.to_dict() if self.job else None
            if job_data:
                job_data['is_manual'] = False
        
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'job_id': str(self.job_id) if self.job_id else None,
            'status': self.status,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None,
            'cover_letter': self.cover_letter,
            'notes': self.notes,
            'job': job_data
        }


class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='unique_user_saved_job'),
    )

    def to_dict(self, include_job=False):
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'job_id': str(self.job_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_job:
            data['job'] = self.job.to_dict() if self.job else None
        return data


class JobAlert(db.Model):
    __tablename__ = 'job_alerts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    keywords = db.Column(db.String(500))
    location = db.Column(db.String(200))
    category = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    frequency = db.Column(db.String(20), default='daily')  # 'instant', 'daily', 'weekly'
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_sent = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title,
            'keywords': self.keywords,
            'location': self.location,
            'category': self.category,
            'job_type': self.job_type,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'frequency': self.frequency,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_sent': self.last_sent.isoformat() if self.last_sent else None
        }


class CVKeyword(db.Model):
    __tablename__ = 'cv_keywords'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cv_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cvs.id', ondelete='CASCADE'), nullable=False)
    keywords = db.Column(db.JSON, nullable=False)  # Array of ML-recommended keywords
    extracted_text = db.Column(db.Text, nullable=True)  # Full extracted CV text
    extraction_method = db.Column(db.String(20), nullable=True)  # 'ocr' or 'text'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'cv_id': str(self.cv_id),
            'keywords': self.keywords,
            'extracted_text': self.extracted_text,
            'extraction_method': self.extraction_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class JobNotification(db.Model):
    __tablename__ = 'job_notifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(UUID(as_uuid=True), db.ForeignKey('jobs.id'), nullable=False)
    cv_id = db.Column(UUID(as_uuid=True), db.ForeignKey('cvs.id'), nullable=True)  # Nullable for active CV notifications
    notification_type = db.Column(db.String(50), nullable=False)  # 'active_cv' or 'past_cv'
    matched_keywords = db.Column(db.JSON, nullable=True)  # Array of keywords that matched
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'job_id': str(self.job_id),
            'cv_id': str(self.cv_id) if self.cv_id else None,
            'notification_type': self.notification_type,
            'matched_keywords': self.matched_keywords,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
