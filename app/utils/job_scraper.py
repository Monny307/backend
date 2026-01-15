import re
from datetime import datetime
from app import db
from app.models import Job
from typing import Dict, Optional, List

class JobScraperImporter:
    """
    Maps scraped job data to database Job model
    Only imports jobs that have a company logo
    """
    
    # Map scraped job types to database job_type enum
    JOB_TYPE_MAPPING = {
        'full time': 'Full-time',
        'full-time': 'Full-time',
        'fulltime': 'Full-time',
        'part time': 'Part-time',
        'part-time': 'Part-time',
        'parttime': 'Part-time',
        'contract': 'Contract',
        'contractor': 'Contract',
        'internship': 'Internship',
        'intern': 'Internship',
        'temporary': 'Contract',
        'freelance': 'Contract',
    }
    
    # Map scraped categories to database categories
    CATEGORY_MAPPING = {
        'technology': 'Technology',
        'it': 'Technology',
        'software': 'Technology',
        'engineering': 'Engineering',
        'marketing': 'Marketing',
        'sales': 'Sales / Marketing',
        'design': 'Design',
        'finance': 'Finance',
        'accounting': 'Finance',
        'hr': 'Human Resources',
        'human resources': 'Human Resources',
        'customer service': 'Customer Service',
        'support': 'Customer Service',
        'administrative': 'Administrative',
        'admin': 'Administrative',
        'healthcare': 'Healthcare',
        'education': 'Educate/Train/Teaching',
        'legal': 'Legal',
        'construction': 'Construction',
        'manufacturing': 'Manufacturing',
        'logistics': 'Logistics',
        'retail': 'Retail',
        'hospitality': 'Hospitality',
        'other': 'Other',
    }
    
    @staticmethod
    def parse_salary(salary_text: Optional[str]) -> Optional[str]:
        """Parse salary from various formats"""
        if not salary_text:
            return None
            
        salary_text = str(salary_text).strip()
        
        # If already in good format, return
        if re.match(r'\$\d+[\s-]+\$\d+', salary_text):
            return salary_text
            
        # Extract numbers
        numbers = re.findall(r'\d+', salary_text)
        
        if len(numbers) >= 2:
            return f"${numbers[0]} - ${numbers[1]}"
        elif len(numbers) == 1:
            return f"${numbers[0]}"
        else:
            return salary_text if salary_text else None
    
    @staticmethod
    def parse_job_type(schedule: Optional[str]) -> str:
        """Parse job type from schedule field"""
        if not schedule:
            return 'Full-time'
            
        schedule_lower = str(schedule).lower().strip()
        
        return JobScraperImporter.JOB_TYPE_MAPPING.get(schedule_lower, 'Full-time')
    
    @staticmethod
    def parse_category(career_category: Optional[str]) -> str:
        """Parse category from career category field"""
        if not career_category:
            return 'Other'
            
        # Return as-is if it's already a valid category
        category_str = str(career_category).strip()
        if category_str:
            return category_str
        
        return 'Other'
    
    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date from various formats"""
        if not date_str:
            return None
            
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
                
        return None
    
    @staticmethod
    def build_description(scraped_data: Dict) -> str:
        """Build comprehensive description from multiple fields"""
        parts = []
        
        # Add announcement description
        if scraped_data.get('Announcement Description'):
            parts.append(str(scraped_data['Announcement Description']))
        
        # Add position summary
        if scraped_data.get('Position Summary'):
            parts.append('\n\n**Position Summary:**\n' + str(scraped_data['Position Summary']))
        
        # Add duties & responsibilities
        if scraped_data.get('Duties & Responsibilities'):
            parts.append('\n\n**Duties & Responsibilities:**\n' + str(scraped_data['Duties & Responsibilities']))
        
        return '\n'.join(parts) if parts else 'No description available'
    
    @staticmethod
    def build_requirements(scraped_data: Dict) -> str:
        """Build requirements from multiple fields"""
        parts = []
        
        # Add qualifications
        if scraped_data.get('Qualifications'):
            parts.append('**Qualifications:**\n' + str(scraped_data['Qualifications']))
        
        # Add skills & knowledge
        if scraped_data.get('Skills & Knowledge'):
            parts.append('\n**Skills & Knowledge:**\n' + str(scraped_data['Skills & Knowledge']))
        
        # Add languages
        if scraped_data.get('Languages Required'):
            parts.append('\n**Languages Required:**\n' + str(scraped_data['Languages Required']))
        
        return '\n'.join(parts) if parts else 'No requirements specified'
    
    @staticmethod
    def import_job(scraped_data: Dict) -> Optional[Job]:
        """
        Import a single scraped job into the database
        Only imports if job has a logo URL
        """
        try:
            # Skip jobs without logo
            logo = scraped_data.get('Company Logo')
            if not logo or str(logo).strip() == '' or str(logo).lower() in ['nan', 'none', 'null']:
                print(f"⏭️  Skipping job (no logo): {scraped_data.get('Job Title')} at {scraped_data.get('Company Name')}")
                return None
            
            # Check if job already exists
            existing_job = Job.query.filter_by(
                title=scraped_data.get('Job Title') or scraped_data.get('Announcement Job Title'),
                company=scraped_data.get('Company Name')
            ).first()
            
            if existing_job:
                print(f"⏭️  Job already exists: {existing_job.title} at {existing_job.company}")
                return existing_job
            
            # Create new job
            job = Job(
                title=scraped_data.get('Job Title') or scraped_data.get('Announcement Job Title'),
                company=scraped_data.get('Company Name'),
                location=scraped_data.get('Location') or scraped_data.get('Office Address'),
                salary=JobScraperImporter.parse_salary(scraped_data.get('Salary')),
                job_type=JobScraperImporter.parse_job_type(scraped_data.get('Schedule')),
                category=JobScraperImporter.parse_category(scraped_data.get('Career Category')),
                description=JobScraperImporter.build_description(scraped_data),
                requirements=JobScraperImporter.build_requirements(scraped_data),
                logo=str(logo).strip(),
                contact_email=scraped_data.get('Contact Email'),
                contact_phone=scraped_data.get('Phone'),
                website=scraped_data.get('Website'),
                status='active',
                deadline=JobScraperImporter.parse_date(scraped_data.get('Deadline')),
                posted_date=JobScraperImporter.parse_date(scraped_data.get('Posting Date')) or datetime.utcnow(),
            )
            
            db.session.add(job)
            db.session.commit()
            
            # Create notifications for matching CVs
            from app.routes.notifications import check_and_create_notifications
            check_and_create_notifications(str(job.id))
            
            print(f"✅ Imported job: {job.title} at {job.company}")
            return job
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error importing job: {str(e)}")
            return None
    
    @staticmethod
    def import_jobs_batch(scraped_jobs: List[Dict]) -> Dict[str, int]:
        """Import multiple jobs at once"""
        stats = {
            'total': len(scraped_jobs),
            'imported': 0,
            'skipped': 0,
            'no_logo': 0,
            'failed': 0
        }
        
        for job_data in scraped_jobs:
            result = JobScraperImporter.import_job(job_data)
            
            if result is None:
                # Check if skipped due to no logo
                logo = job_data.get('Company Logo')
                if not logo or str(logo).strip() == '' or str(logo).lower() in ['nan', 'none', 'null']:
                    stats['no_logo'] += 1
                else:
                    stats['failed'] += 1
            elif result:
                # New import or existing
                stats['imported'] += 1
        
        return stats
