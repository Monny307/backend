from app import create_app, db
from app.models import Job

app = create_app()

with app.app_context():
    # Check Ontario jobs
    ontario_jobs = Job.query.filter_by(company='Ontario International School').all()
    
    print(f"\nOntario International School jobs: {len(ontario_jobs)}\n")
    for i, job in enumerate(ontario_jobs, 1):
        posted = job.posted_date.strftime("%Y-%m-%d") if job.posted_date else "N/A"
        logo = "Yes" if job.logo else "No"
        print(f"{i}. {job.title}")
        print(f"   Posted: {posted} | Logo: {logo}")
        if job.logo:
            print(f"   Logo URL: {job.logo[:80]}...")
        print()
