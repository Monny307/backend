from app import create_app, db
from app.models import Job
from datetime import datetime

app = create_app()

# Real CSV companies from the import
REAL_CSV_COMPANIES = [
    'Ontario International School',
    'YHS (Cambodia) Food & Beverage Pte Ltd (Yeo\'s)',
    'Ajinomoto (Cambodia) Co., Ltd.',
    'Socfin KCD Co.,Ltd',
    'Journeys Within Our Community Organization'
]

with app.app_context():
    jobs = Job.query.all()
    
    # Identify old/test jobs to delete
    # Real jobs are only those from specific CSV companies
    old_jobs = []
    
    for job in jobs:
        # Check if this is a real CSV import by company name
        is_real_csv = any(company in job.company for company in REAL_CSV_COMPANIES)
        
        if not is_real_csv:
            old_jobs.append(job)
    
    print(f"\n{'='*80}")
    print(f"DELETING OLD/TEST JOBS")
    print(f"{'='*80}\n")
    print(f"Total jobs in database: {len(jobs)}")
    print(f"Jobs to delete: {len(old_jobs)}")
    print(f"Jobs to keep: {len(jobs) - len(old_jobs)}")
    print(f"\n{'='*80}")
    print("Jobs being deleted:")
    print(f"{'='*80}\n")
    
    for i, job in enumerate(old_jobs, 1):
        posted = job.posted_date.strftime("%Y-%m-%d") if job.posted_date else "No date"
        print(f"{i}. {job.title[:50]:50} | {job.company[:30]:30} | {posted}")
        db.session.delete(job)
    
    # Commit the deletions
    try:
        db.session.commit()
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS: Deleted {len(old_jobs)} old/test jobs")
        print(f"{'='*80}\n")
        
        # Verify remaining jobs
        remaining = Job.query.count()
        print(f"📊 Remaining jobs in database: {remaining}")
        print(f"\nAll remaining jobs are from the CSV import (Dec 2025 - Jan 2026)")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n{'='*80}")
        print(f"❌ ERROR: Failed to delete jobs")
        print(f"{'='*80}")
        print(f"Error: {str(e)}")
