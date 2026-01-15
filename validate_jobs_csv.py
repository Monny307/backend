#!/usr/bin/env python
"""
Validate jobs.csv before importing to database

This script checks:
1. CSV column mapping to database
2. Missing required fields
3. Data quality issues
4. Recommended cleaning actions

Usage:
    python validate_jobs_csv.py jobs.csv
    python validate_jobs_csv.py jobs.xlsx
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Database required fields
REQUIRED_DB_FIELDS = {
    'title': 'Job Title (NOT NULL)',
    'company': 'Company Name (NOT NULL)',
    'location': 'Location (NOT NULL)',
    'job_type': 'Schedule/Job Type (NOT NULL)',
    'category': 'Career Category (NOT NULL)',
    'description': 'Description/Summary (NOT NULL)',
}

# CSV to Database column mapping
CSV_TO_DB_MAPPING = {
    'Job Title': 'title',
    'Announcement Job Title': 'title',  # Fallback
    'Company Name': 'company',
    'Location': 'location',
    'Office Address': 'location',  # Fallback
    'Salary': 'salary',
    'Schedule': 'job_type',
    'Career Category': 'category',
    'Announcement Description': 'description',
    'Position Summary': 'description',  # Will be combined
    'Duties & Responsibilities': 'description',  # Will be combined
    'Qualifications': 'requirements',
    'Skills & Knowledge': 'requirements',  # Will be combined
    'Languages Required': 'requirements',  # Will be combined
    'Company Logo': 'logo',
    'Posting Date': 'posted_date',
    'Deadline': 'deadline',
}

def validate_csv(file_path):
    """Validate CSV file structure and data"""
    
    print("="*70)
    print("📋 JOB CSV VALIDATION REPORT")
    print("="*70)
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found: {file_path}")
        return
    
    print(f"\n📄 Reading file: {file_path}")
    
    # Read file
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            print("❌ ERROR: Unsupported file format. Use .csv, .xlsx, or .xls")
            return
    except Exception as e:
        print(f"❌ ERROR reading file: {str(e)}")
        return
    
    print(f"✅ File loaded successfully")
    print(f"📊 Total rows: {len(df)}")
    print(f"📋 Total columns: {len(df.columns)}")
    
    # Show all columns
    print(f"\n{'='*70}")
    print(f"📋 CSV COLUMNS ({len(df.columns)} columns)")
    print(f"{'='*70}")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2}. {col}")
    
    # Check column mapping
    print(f"\n{'='*70}")
    print(f"🔄 COLUMN MAPPING (CSV → Database)")
    print(f"{'='*70}")
    
    mapped_columns = {}
    unmapped_columns = []
    
    for csv_col in df.columns:
        if csv_col in CSV_TO_DB_MAPPING:
            db_col = CSV_TO_DB_MAPPING[csv_col]
            mapped_columns[csv_col] = db_col
            print(f"✅ {csv_col:35} → {db_col}")
        else:
            unmapped_columns.append(csv_col)
            print(f"⚠️  {csv_col:35} → (NOT MAPPED - will be ignored)")
    
    # Check required fields coverage
    print(f"\n{'='*70}")
    print(f"✅ REQUIRED FIELDS CHECK")
    print(f"{'='*70}")
    
    covered_required = {}
    missing_required = {}
    
    for db_field, description in REQUIRED_DB_FIELDS.items():
        # Check if any CSV column maps to this DB field
        csv_cols = [csv for csv, db in CSV_TO_DB_MAPPING.items() if db == db_field]
        available_cols = [col for col in csv_cols if col in df.columns]
        
        if available_cols:
            covered_required[db_field] = available_cols
            print(f"✅ {db_field:20} ← {', '.join(available_cols)}")
        else:
            missing_required[db_field] = description
            print(f"❌ {db_field:20} ← MISSING!")
    
    # Data quality checks
    print(f"\n{'='*70}")
    print(f"🔍 DATA QUALITY CHECK")
    print(f"{'='*70}")
    
    issues = []
    warnings = []
    
    # Check for empty/null values in key fields
    key_fields = ['Job Title', 'Announcement Job Title', 'Company Name', 'Location', 
                  'Office Address', 'Career Category', 'Schedule']
    
    for field in key_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            empty_count = (df[field].astype(str).str.strip() == '').sum()
            total_empty = null_count + empty_count
            
            if total_empty > 0:
                pct = (total_empty / len(df)) * 100
                if field in ['Job Title', 'Company Name']:
                    issues.append(f"❌ {field}: {total_empty} empty ({pct:.1f}%) - CRITICAL!")
                else:
                    warnings.append(f"⚠️  {field}: {total_empty} empty ({pct:.1f}%)")
            else:
                print(f"✅ {field}: No empty values")
    
    # Check duplicate jobs
    if 'Job Title' in df.columns and 'Company Name' in df.columns:
        duplicates = df.duplicated(subset=['Job Title', 'Company Name'], keep=False)
        dup_count = duplicates.sum()
        if dup_count > 0:
            warnings.append(f"⚠️  Duplicate jobs: {dup_count} rows (same title + company)")
            print(f"⚠️  Found {dup_count} potential duplicate jobs")
        else:
            print(f"✅ No duplicate jobs found")
    
    # Sample data preview
    print(f"\n{'='*70}")
    print(f"📝 SAMPLE DATA (First 3 Rows)")
    print(f"{'='*70}")
    
    preview_cols = ['Job Title', 'Company Name', 'Location', 'Salary', 'Career Category']
    available_preview = [col for col in preview_cols if col in df.columns]
    
    if available_preview:
        print(df[available_preview].head(3).to_string(index=False))
    
    # Summary and recommendations
    print(f"\n{'='*70}")
    print(f"📊 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    if missing_required:
        print(f"\n❌ CRITICAL ISSUES ({len(missing_required)}):")
        for field, desc in missing_required.items():
            print(f"   • Missing required field: {desc}")
    
    if issues:
        print(f"\n❌ DATA ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"   • {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not missing_required and not issues:
        print(f"\n✅ VALIDATION PASSED!")
        print(f"   Your CSV is ready to import!")
    
    # Recommendations
    print(f"\n{'='*70}")
    print(f"💡 RECOMMENDATIONS")
    print(f"{'='*70}")
    
    recommendations = []
    
    if missing_required:
        recommendations.append("❌ CANNOT IMPORT: Missing required database fields")
        recommendations.append("   → Fix: Ensure your CSV has these columns:")
        for field, desc in missing_required.items():
            recommendations.append(f"      • {desc}")
    
    if issues:
        recommendations.append("⚠️  Clean empty values in critical fields (Job Title, Company Name)")
        recommendations.append("   → Fix: Remove rows with empty Job Title or Company Name")
    
    if warnings:
        if any('empty' in w for w in warnings):
            recommendations.append("⚠️  Some optional fields have empty values")
            recommendations.append("   → Optional: Fill in missing data or leave as-is")
        
        if any('Duplicate' in w for w in warnings):
            recommendations.append("⚠️  Duplicate jobs will be skipped during import")
            recommendations.append("   → Optional: Remove duplicates before importing")
    
    if unmapped_columns:
        recommendations.append(f"ℹ️  {len(unmapped_columns)} columns will be ignored during import:")
        for col in unmapped_columns[:5]:  # Show first 5
            recommendations.append(f"   • {col}")
        if len(unmapped_columns) > 5:
            recommendations.append(f"   • ... and {len(unmapped_columns) - 5} more")
    
    if not missing_required and not issues:
        recommendations.append("✅ CSV is ready to import!")
        recommendations.append(f"   → Run: python import_jobs_from_csv.py {os.path.basename(file_path)}")
        recommendations.append(f"   → This will import {len(df)} jobs to the database")
    
    if recommendations:
        for rec in recommendations:
            print(rec)
    
    # Data cleaning script suggestion
    if issues or warnings:
        print(f"\n{'='*70}")
        print(f"🛠️  DATA CLEANING SUGGESTIONS")
        print(f"{'='*70}")
        print(f"")
        print(f"You can clean your CSV using pandas:")
        print(f"")
        print(f"```python")
        print(f"import pandas as pd")
        print(f"")
        print(f"# Read CSV")
        print(f"df = pd.read_csv('{os.path.basename(file_path)}')")
        print(f"")
        
        if any('Job Title' in i for i in issues):
            print(f"# Remove rows with empty Job Title")
            print(f"df = df[df['Job Title'].notna()]")
            print(f"df = df[df['Job Title'].str.strip() != '']")
            print(f"")
        
        if any('Company Name' in i for i in issues):
            print(f"# Remove rows with empty Company Name")
            print(f"df = df[df['Company Name'].notna()]")
            print(f"df = df[df['Company Name'].str.strip() != '']")
            print(f"")
        
        if any('Duplicate' in w for w in warnings):
            print(f"# Remove duplicate jobs (keep first occurrence)")
            print(f"df = df.drop_duplicates(subset=['Job Title', 'Company Name'], keep='first')")
            print(f"")
        
        print(f"# Save cleaned CSV")
        print(f"df.to_csv('jobs_cleaned.csv', index=False)")
        print(f"```")
    
    print(f"\n{'='*70}")
    print(f"End of validation report")
    print(f"{'='*70}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_jobs_csv.py <file.csv|file.xlsx>")
        print("\nExample:")
        print("  python validate_jobs_csv.py jobs.csv")
        print("  python validate_jobs_csv.py jobs.xlsx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    validate_csv(file_path)

if __name__ == '__main__':
    main()
