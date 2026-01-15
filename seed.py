from app import create_app, db
from app.models import User, Job, Profile
from app import bcrypt
from datetime import datetime

app = create_app()

def seed_database():
    """Seed the database with initial data"""
    with app.app_context():
        print("Starting database seeding...")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        # db.drop_all()
        # db.create_all()
        
        # Check if admin exists
        admin_exists = User.query.filter_by(email='admin@demo.com').first()
        if not admin_exists:
            # Create admin user
            admin = User(
                email='admin@demo.com',
                password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                fullname='Admin User',
                role='admin',
                is_active=True
            )
            db.session.add(admin)
            print("✓ Admin user created (admin@demo.com / admin123)")
        else:
            print("✓ Admin user already exists")
        
        # Check if demo user exists
        user_exists = User.query.filter_by(email='user@demo.com').first()
        if not user_exists:
            # Create demo user
            user = User(
                email='user@demo.com',
                password_hash=bcrypt.generate_password_hash('user123').decode('utf-8'),
                fullname='Demo User',
                role='user',
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            
            # Create profile for demo user
            profile = Profile(user_id=user.id)
            db.session.add(profile)
            
            print("✓ Demo user created (user@demo.com / user123)")
        else:
            print("✓ Demo user already exists")
        
        db.session.commit()
        
        # Create sample jobs
        sample_jobs = [
            {
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp Inc.',
                'location': 'Phnom Penh, Cambodia',
                'salary': '$1200 - $1800',
                'job_type': 'Full-time',
                'category': 'Technology',
                'description': 'We are looking for an experienced software engineer to join our growing team. You will be responsible for developing high-quality applications and working on exciting projects.',
                'requirements': "- Bachelor's degree in Computer Science or related field\n- 5+ years of experience in software development\n- Proficiency in Python, JavaScript, or Java\n- Experience with modern frameworks and databases\n- Strong problem-solving skills",
                'logo': 'https://logo.clearbit.com/google.com',
                'status': 'active'
            },
            {
                'title': 'Marketing Manager',
                'company': 'Digital Marketing Pro',
                'location': 'Siem Reap, Cambodia',
                'salary': '$800 - $1200',
                'job_type': 'Full-time',
                'category': 'Marketing',
                'description': 'Lead our marketing team and drive digital campaigns. Develop strategies to increase brand awareness and customer engagement.',
                'requirements': "- 3+ years in marketing management\n- Experience with digital marketing tools\n- Strong analytical and communication skills\n- Proven track record of successful campaigns",
                'logo': 'https://logo.clearbit.com/hubspot.com',
                'status': 'active'
            },
            {
                'title': 'UI/UX Designer',
                'company': 'Creative Studio',
                'location': 'Remote',
                'salary': '$600 - $1000',
                'job_type': 'Part-time',
                'category': 'Design',
                'description': 'Design beautiful and intuitive user interfaces. Work with product teams to create amazing user experiences.',
                'requirements': "- Portfolio required\n- 2+ years of UI/UX design experience\n- Proficiency in Figma, Adobe XD, or Sketch\n- Understanding of user-centered design principles",
                'logo': 'https://logo.clearbit.com/figma.com',
                'status': 'active'
            },
            {
                'title': 'Data Analyst',
                'company': 'Analytics Corp',
                'location': 'Phnom Penh, Cambodia',
                'salary': '$700 - $1100',
                'job_type': 'Full-time',
                'category': 'Data Science',
                'description': 'Analyze data to drive business decisions. Create reports and dashboards to help stakeholders understand key metrics.',
                'requirements': "- Bachelor's degree in Statistics, Mathematics, or related field\n- Experience with SQL and data visualization tools\n- Strong analytical and problem-solving skills\n- Knowledge of Python or R is a plus",
                'logo': 'https://logo.clearbit.com/tableau.com',
                'status': 'active'
            },
            {
                'title': 'Content Writer',
                'company': 'Media House',
                'location': 'Remote',
                'salary': '$500 - $800',
                'job_type': 'Part-time',
                'category': 'Writing',
                'description': 'Create engaging content for various platforms. Write blog posts, articles, and social media content.',
                'requirements': "- Excellent writing and editing skills\n- 1+ years of content writing experience\n- Understanding of SEO best practices\n- Ability to adapt writing style for different audiences",
                'logo': 'https://logo.clearbit.com/medium.com',
                'status': 'active'
            },
            {
                'title': 'Sales Representative',
                'company': 'Sales Pro Inc.',
                'location': 'Phnom Penh, Cambodia',
                'salary': '$600 - $1000 + Commission',
                'job_type': 'Full-time',
                'category': 'Sales',
                'description': 'Drive sales and build relationships with clients. Meet sales targets and provide excellent customer service.',
                'requirements': "- 2+ years of sales experience\n- Strong communication and negotiation skills\n- Self-motivated and target-driven\n- Experience in B2B sales is a plus",
                'logo': 'https://logo.clearbit.com/salesforce.com',
                'status': 'active'
            },
            {
                'title': 'Project Manager',
                'company': 'Project Solutions',
                'location': 'Phnom Penh, Cambodia',
                'salary': '$1000 - $1500',
                'job_type': 'Full-time',
                'category': 'Management',
                'description': 'Lead project teams and ensure successful project delivery. Manage timelines, resources, and stakeholder communications.',
                'requirements': "- PMP or equivalent certification preferred\n- 4+ years of project management experience\n- Strong leadership and organizational skills\n- Experience with project management tools (Jira, Asana, etc.)",
                'logo': 'https://logo.clearbit.com/atlassian.com',
                'status': 'active'
            },
            {
                'title': 'Customer Support Specialist',
                'company': 'Support Center',
                'location': 'Remote',
                'salary': '$400 - $700',
                'job_type': 'Full-time',
                'category': 'Customer Service',
                'description': 'Provide excellent customer support via email, chat, and phone. Resolve customer issues and ensure satisfaction.',
                'requirements': "- 1+ years of customer service experience\n- Excellent communication skills\n- Patient and empathetic\n- Ability to work in a fast-paced environment",
                'logo': 'https://logo.clearbit.com/zendesk.com',
                'status': 'active'
            }
        ]
        
        # Check if jobs exist
        existing_jobs_count = Job.query.count()
        if existing_jobs_count == 0:
            for job_data in sample_jobs:
                job = Job(**job_data, posted_date=datetime.utcnow())
                db.session.add(job)
            
            db.session.commit()
            print(f"✓ Created {len(sample_jobs)} sample jobs")
        else:
            print(f"✓ Jobs already exist ({existing_jobs_count} jobs in database)")
        
        print("\n" + "="*50)
        print("Database seeding completed successfully!")
        print("="*50)
        print("\nDemo Accounts:")
        print("  Admin: admin@demo.com / admin123")
        print("  User:  user@demo.com / user123")
        print("\nYou can now start the server with: python run.py")


if __name__ == '__main__':
    seed_database()
