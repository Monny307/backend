# WebCV Backend - Flask API

A professional Flask backend API for the WebCV job portal application with PostgreSQL database.

## Features

- 🔐 **Authentication & Authorization**: JWT-based authentication with role-based access control (User/Admin)
- 👤 **User Management**: User registration, login, profile management
- 💼 **Job Management**: CRUD operations for job postings with advanced filtering
- 📝 **Application System**: Job application tracking with status management
- 📄 **CV/Resume Management**: Upload, manage multiple CVs with active CV selection
- 🔔 **Job Alerts**: Customizable job alerts with frequency settings
- 📊 **Admin Dashboard**: Comprehensive statistics and management tools
- 📧 **Contact System**: Contact form with message management
- 🗄️ **PostgreSQL Database**: Robust relational database with proper relationships

## Tech Stack

- **Framework**: Flask 3.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-JWT-Extended
- **Password Hashing**: Flask-Bcrypt
- **CORS**: Flask-CORS
- **Migrations**: Flask-Migrate (Alembic)
- **Server**: Gunicorn (production)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # Database models
│   ├── utils.py             # Utility functions
│   └── routes/              # API endpoints
│       ├── auth.py          # Authentication endpoints
│       ├── users.py         # User management
│       ├── jobs.py          # Job management
│       ├── applications.py  # Application management
│       ├── profiles.py      # Profile & CV management
│       ├── job_alerts.py    # Job alerts
│       ├── admin.py         # Admin endpoints
│       └── contact.py       # Contact form
├── uploads/                 # File uploads (CVs, photos)
│   ├── cvs/
│   └── profiles/
├── config.py               # Configuration
├── run.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .env.example           # Environment template
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pgAdmin (optional, for database management)

### 1. Install PostgreSQL

**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Install and remember your postgres password
- Default port: 5432

**Linux:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

### 2. Create Database

Open PostgreSQL command line or pgAdmin and run:

```sql
CREATE DATABASE webcv_db;
```

Or using command line:
```bash
# Windows
psql -U postgres
CREATE DATABASE webcv_db;
\q

# Linux/Mac
sudo -u postgres psql
CREATE DATABASE webcv_db;
\q
```

### 3. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 4. Configure Environment

Edit `.env` file with your settings:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-me
JWT_SECRET_KEY=your-jwt-secret-key-here-change-me

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/webcv_db

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Important**: Replace `your_password` with your PostgreSQL password!

### 5. Initialize Database

```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 6. Seed Database (Optional)

Create `seed.py` in backend directory to add sample data:

```python
from app import create_app, db
from app.models import User, Job
from app import bcrypt

app = create_app()

with app.app_context():
    # Create admin user
    admin = User(
        email='admin@demo.com',
        password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
        fullname='Admin User',
        role='admin'
    )
    
    # Create regular user
    user = User(
        email='user@demo.com',
        password_hash=bcrypt.generate_password_hash('user123').decode('utf-8'),
        fullname='Demo User',
        role='user'
    )
    
    db.session.add(admin)
    db.session.add(user)
    db.session.commit()
    
    print("✓ Users created successfully!")
```

Run: `python seed.py`

### 7. Run Development Server

```bash
python run.py
```

The API will be available at: `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user
- `POST /api/auth/change-password` - Change password

### Users
- `GET /api/users` - Get all users (admin)
- `GET /api/users/<id>` - Get user by ID
- `PUT /api/users/<id>` - Update user
- `DELETE /api/users/<id>` - Delete user (admin)

### Jobs
- `GET /api/jobs` - Get jobs (with filters)
- `GET /api/jobs/<id>` - Get job by ID
- `POST /api/jobs` - Create job (admin)
- `PUT /api/jobs/<id>` - Update job (admin)
- `DELETE /api/jobs/<id>` - Delete job (admin)
- `GET /api/jobs/categories` - Get all categories
- `GET /api/jobs/types` - Get all job types

### Applications
- `GET /api/applications` - Get user applications
- `GET /api/applications/<id>` - Get application by ID
- `POST /api/applications` - Apply for job
- `PUT /api/applications/<id>` - Update application
- `DELETE /api/applications/<id>` - Withdraw application
- `GET /api/applications/check/<job_id>` - Check if applied

### Profiles
- `GET /api/profiles` - Get user profile
- `PUT /api/profiles` - Update profile
- `POST /api/profiles/photo` - Upload profile photo
- `GET /api/profiles/cvs` - Get user CVs
- `POST /api/profiles/cvs` - Upload CV
- `POST /api/profiles/cvs/<id>/set-active` - Set active CV
- `DELETE /api/profiles/cvs/<id>` - Delete CV
- `POST /api/profiles/education` - Add education
- `PUT /api/profiles/education/<id>` - Update education
- `DELETE /api/profiles/education/<id>` - Delete education

### Job Alerts
- `GET /api/job-alerts` - Get user job alerts
- `GET /api/job-alerts/<id>` - Get job alert by ID
- `POST /api/job-alerts` - Create job alert
- `PUT /api/job-alerts/<id>` - Update job alert
- `DELETE /api/job-alerts/<id>` - Delete job alert
- `POST /api/job-alerts/<id>/toggle` - Toggle active status

### Admin
- `GET /api/admin/stats` - Get dashboard statistics
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users/<id>/toggle-status` - Toggle user status
- `GET /api/admin/applications` - Get all applications
- `PUT /api/admin/applications/<id>/status` - Update application status
- `GET /api/admin/jobs/<id>/applications` - Get job applications
- `GET /api/admin/contact-messages` - Get contact messages
- `PUT /api/admin/contact-messages/<id>/status` - Update message status

### Contact
- `POST /api/contact` - Submit contact form

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. After login, include the token in requests:

```javascript
headers: {
  'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
  'Content-Type': 'application/json'
}
```

## Production Deployment

### Option 1: Traditional Server (VPS, EC2, DigitalOcean)

1. **Prepare server**:
```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx
```

2. **Setup application**:
```bash
cd /var/www
git clone your-repo
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure Gunicorn**:
Create `gunicorn_config.py`:
```python
bind = "127.0.0.1:5000"
workers = 4
```

4. **Create systemd service** (`/etc/systemd/system/webcv.service`):
```ini
[Unit]
Description=WebCV Flask API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/backend
Environment="PATH=/var/www/backend/venv/bin"
ExecStart=/var/www/backend/venv/bin/gunicorn -c gunicorn_config.py run:app

[Install]
WantedBy=multi-user.target
```

5. **Configure Nginx** (`/etc/nginx/sites-available/webcv`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

6. **Start services**:
```bash
sudo systemctl start webcv
sudo systemctl enable webcv
sudo systemctl restart nginx
```

### Option 2: Heroku

1. **Create `Procfile`**:
```
web: gunicorn run:app
```

2. **Deploy**:
```bash
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
heroku run flask db upgrade
```

### Option 3: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: webcv_db
      POSTGRES_PASSWORD: yourpassword
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://postgres:yourpassword@db:5432/webcv_db
    depends_on:
      - db

volumes:
  postgres_data:
```

Run: `docker-compose up`

## Database Schema

### Users
- User accounts with role-based access (user/admin)
- Secure password hashing

### Profiles
- User profile information
- One-to-one with Users

### CVs
- Multiple CVs per user
- File upload support
- Active CV designation

### Jobs
- Job postings with rich details
- Category and type classification
- Status management

### Applications
- Track job applications
- Status workflow (applied → interview → offer/rejected)

### Job Alerts
- User-defined job search criteria
- Frequency settings

### Education, Experience, Languages, Certifications, Skills
- Profile components
- Many-to-one with Profiles

### Contact Messages
- Contact form submissions
- Status tracking

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | - |
| `JWT_SECRET_KEY` | JWT secret key | - |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000 |
| `UPLOAD_FOLDER` | File upload directory | uploads |
| `MAX_CONTENT_LENGTH` | Max upload size (bytes) | 16777216 (16MB) |

## Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `sudo service postgresql status`
- Check DATABASE_URL in `.env`
- Ensure database exists: `psql -U postgres -l`

### Migration Issues
```bash
# Reset migrations
rm -rf migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### CORS Issues
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Clear browser cache

## Support

For issues or questions, please open an issue on GitHub or contact support.

## License

MIT License
#   b a c k  
 