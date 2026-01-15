from app import create_app, db
from app.models import Job
from datetime import datetime

app = create_app()

with app.app_context():
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    
    print(f"\n{'='*80}")
    print(f"TOTAL JOBS IN DATABASE: {len(jobs)}")
    print(f"{'='*80}\n")
    
    # Group by posted date
    recent_jobs = []
    old_jobs = []
    
    for job in jobs:
        if job.posted_date:
            # Jobs from recent CSV import (Dec 22, 2025 - Jan 5, 2026)
            if job.posted_date.year >= 2025 and job.posted_date.month >= 12:
                recent_jobs.append(job)
            else:
                old_jobs.append(job)
        else:
            old_jobs.append(job)
    
    print(f"📊 BREAKDOWN:")
    print(f"  ✅ Recent CSV Jobs (Dec 2025 - Jan 2026): {len(recent_jobs)}")
    print(f"  🗑️  Old/Test Jobs: {len(old_jobs)}")
    print(f"\n{'='*80}")
    
    if old_jobs:
        print(f"\n🗑️  OLD/TEST JOBS TO DELETE ({len(old_jobs)}):")
        print(f"{'='*80}")
        for i, job in enumerate(old_jobs[:20], 1):
            posted = job.posted_date.strftime("%Y-%m-%d") if job.posted_date else "No date"
            print(f"{i}. {job.title[:50]:50} | {job.company[:30]:30} | {posted}")
        
        if len(old_jobs) > 20:
            print(f"... and {len(old_jobs) - 20} more")
    
    if recent_jobs:
        print(f"\n✅ RECENT CSV JOBS TO KEEP ({len(recent_jobs)}):")
        print(f"{'='*80}")
        for i, job in enumerate(recent_jobs[:10], 1):
            posted = job.posted_date.strftime("%Y-%m-%d") if job.posted_date else "No date"
            print(f"{i}. {job.title[:50]:50} | {job.company[:30]:30} | {posted}")
        
        if len(recent_jobs) > 10:
            print(f"... and {len(recent_jobs) - 10} more")
    
    print(f"\n{'='*80}")
