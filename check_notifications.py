from app import create_app, db
from app.models import JobNotification, Job, User, CV

app = create_app()

with app.app_context():
    total = JobNotification.query.count()
    print(f"Total job notifications: {total}")
    recent = JobNotification.query.order_by(JobNotification.created_at.desc()).limit(10).all()
    for n in recent:
        job = Job.query.get(n.job_id)
        cv = CV.query.get(n.cv_id) if n.cv_id else None
        user = User.query.get(n.user_id)
        print('---')
        print(n.to_dict())
        print('job_title:', job.title if job else 'N/A')
        print('cv_name:', cv.name if cv else None)
        print('user_email:', user.email if user else 'N/A')
    
    # If there are no notifications, try creating notifications for recent jobs
    if total == 0:
        from app.routes.notifications import check_and_create_notifications
        recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(100).all()
        print(f"Attempting to create notifications for {len(recent_jobs)} recent jobs...")
        for j in recent_jobs:
            try:
                check_and_create_notifications(str(j.id))
            except Exception as e:
                print(f"Error creating notifications for job {j.id}: {e}")

        # Re-check count
        total_after = JobNotification.query.count()
        print(f"Total job notifications after attempt: {total_after}")

    # Quick DB write test: try inserting a test notification to verify writes
    try:
        user = User.query.first()
        job = Job.query.first()
        if user and job:
            from app.models import JobNotification as JN
            test_notif = JN(
                user_id=user.id,
                job_id=job.id,
                notification_type='active_cv',
                matched_keywords=['__test__'],
                is_read=False
            )
            db.session.add(test_notif)
            db.session.commit()
            print('Inserted test notification id:', test_notif.id)
            # clean up
            db.session.delete(test_notif)
            db.session.commit()
        else:
            print('No user or job found to test DB write')
    except Exception as e:
        print('DB write test failed:', e)
