"""
Reset jobs table and import only jobs with logos from CSV
"""
from app import create_app, db
from app.models import Job
import pandas as pd
from datetime import datetime
import uuid

def reset_and_import():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("RESETTING JOBS TABLE AND IMPORTING JOBS WITH LOGOS")
        print("=" * 60)
        
        # Step 1: Delete all jobs
        print("\n🗑️  Deleting all jobs from database...")
        deleted_count = Job.query.delete()
        db.session.commit()
        print(f"✅ Deleted {deleted_count} jobs")
        
        # Step 2: Read CSV
        csv_file = 'bongthom_scraped_20260115_141352.csv'
        print(f"\n📄 Reading CSV file: {csv_file}")
        df = pd.read_csv(csv_file)
        print(f"✅ Found {len(df)} total jobs in CSV")
        
        # Step 3: Filter only jobs with logos
        df_with_logos = df[df['Company Logo'].notna() & (df['Company Logo'] != '')]
        print(f"\n🖼️  Jobs with logos: {len(df_with_logos)}")
        print(f"⏭️  Jobs without logos (skipped): {len(df) - len(df_with_logos)}")
        
        # Step 4: Import jobs
        imported = 0
        failed = 0
        
        print(f"\n💾 Importing {len(df_with_logos)} jobs with logos...")
        
        for _, row in df_with_logos.iterrows():
            try:
                # Build description
                description_parts = []
                if pd.notna(row['Announcement Description']):
                    description_parts.append(row['Announcement Description'])
                if pd.notna(row['Position Summary']):
                    description_parts.append(f"\n\n**Position Summary:**\n{row['Position Summary']}")
                if pd.notna(row['Duties & Responsibilities']):
                    description_parts.append(f"\n\n**Duties & Responsibilities:**\n{row['Duties & Responsibilities']}")
                
                description = '\n'.join(description_parts) if description_parts else 'No description available'
                
                # Build requirements
                requirements_parts = []
                if pd.notna(row['Qualifications']):
                    requirements_parts.append(f"**Qualifications:**\n{row['Qualifications']}")
                if pd.notna(row['Skills & Knowledge']):
                    requirements_parts.append(f"\n**Skills & Knowledge:**\n{row['Skills & Knowledge']}")
                if pd.notna(row['Languages Required']):
                    requirements_parts.append(f"\n**Languages Required:**\n{row['Languages Required']}")
                
                requirements = '\n'.join(requirements_parts) if requirements_parts else 'No specific requirements listed'
                
                # Parse posting date
                posting_date = None
                if pd.notna(row['Posting Date']) and row['Posting Date']:
                    try:
                        posting_date = datetime.strptime(row['Posting Date'], '%Y-%m-%d')
                    except:
                        posting_date = datetime.now()
                else:
                    posting_date = datetime.now()
                
                # Create job
                job = Job(
                    title=row['Job Title'],
                    company=row['Company Name'],
                    location=row['Location'] if pd.notna(row['Location']) else 'Not specified',
                    salary=row['Salary'] if pd.notna(row['Salary']) else 'Negotiable',
                    job_type=row['Schedule'] if pd.notna(row['Schedule']) else 'Full-time',
                    category=row['Career Category'] if pd.notna(row['Career Category']) else 'Other',
                    description=description,
                    requirements=requirements,
                    logo=row['Company Logo'],  # Logo is guaranteed to exist
                    contact_email=row['Contact Email'] if pd.notna(row['Contact Email']) else None,
                    contact_phone=row['Phone'] if pd.notna(row['Phone']) else None,
                    website=row['Website'] if pd.notna(row['Website']) else None,
                    status='active',
                    posted_date=posting_date
                )
                
                db.session.add(job)
                db.session.commit()
                imported += 1
                
                if imported % 50 == 0:
                    print(f"  ✅ Imported {imported} jobs...")
                
            except Exception as e:
                db.session.rollback()
                failed += 1
                print(f"  ❌ Failed: {row['Job Title']} - {str(e)}")
        
        print("\n" + "=" * 60)
        print("📊 IMPORT SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully imported: {imported}")
        print(f"❌ Failed: {failed}")
        print(f"📋 Total jobs in database: {Job.query.count()}")
        print("=" * 60)

if __name__ == "__main__":
    reset_and_import()
