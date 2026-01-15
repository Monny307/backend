"""
Quick command reference for Flask-Migrate database operations
"""

# ============================================
# INITIAL SETUP (Run once)
# ============================================

# 1. Initialize migrations folder
flask db init

# 2. Create first migration
flask db migrate -m "Initial migration"

# 3. Apply migration to database
flask db upgrade

# 4. Seed database with demo data
python seed.py


# ============================================
# AFTER MODEL CHANGES
# ============================================

# Create migration after model changes
flask db migrate -m "Add new field to User model"

# Review migration file in migrations/versions/
# Then apply:
flask db upgrade


# ============================================
# COMMON COMMANDS
# ============================================

# Check current migration version
flask db current

# Show migration history
flask db history

# Upgrade to latest
flask db upgrade

# Upgrade to specific version
flask db upgrade <revision>

# Downgrade one version
flask db downgrade

# Downgrade to specific version
flask db downgrade <revision>

# Show SQL without executing
flask db upgrade --sql


# ============================================
# RESET DATABASE (Development only!)
# ============================================

# Option 1: Drop and recreate
# In psql:
#   DROP DATABASE webcv_db;
#   CREATE DATABASE webcv_db;

# Then:
# rm -rf migrations
# flask db init
# flask db migrate -m "Initial migration"
# flask db upgrade
# python seed.py


# Option 2: Downgrade all
# flask db downgrade base
# flask db upgrade


# ============================================
# TROUBLESHOOTING
# ============================================

# If migrations folder exists but commands fail:
# 1. Delete migrations folder
# 2. Run: flask db init
# 3. Run: flask db migrate -m "Initial migration"
# 4. Run: flask db upgrade

# If tables already exist:
# flask db stamp head  # Mark current state
# flask db migrate -m "Sync existing tables"

# Check database connection:
# flask shell
# >>> from app import db
# >>> db.engine.execute('SELECT 1').scalar()
