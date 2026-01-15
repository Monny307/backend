#!/usr/bin/env python
"""
Import scraped jobs from CSV/Excel file to database

Usage:
    python import_jobs_from_csv.py jobs.csv
    python import_jobs_from_csv.py jobs.xlsx
"""

import sys
import os
import pandas as pd
from app import create_app, db
from app.utils.job_scraper import JobScraperImporter

def import_from_file(file_path):
    """Import jobs from CSV or Excel file"""
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📄 Reading file: {file_path}")
    
    # Read file based on extension
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        print("❌ Unsupported file format. Use .csv, .xlsx, or .xls")
        return
    
    print(f"📊 Found {len(df)} jobs in file")
    print(f"📋 Columns: {', '.join(df.columns.tolist())}")
    
    # Convert DataFrame to list of dictionaries
    jobs_data = df.to_dict('records')
    
    # Clean NaN values (replace with None)
    for job in jobs_data:
        for key, value in job.items():
            if pd.isna(value):
                job[key] = None
    
    # Show sample
    print(f"\n📝 Sample job:")
    if jobs_data:
        sample = jobs_data[0]
        for key, value in list(sample.items())[:5]:  # Show first 5 fields
            print(f"   {key}: {value}")
        print("   ...")
    
    # Confirm import
    print(f"\n⚠️  About to import {len(jobs_data)} jobs to database")
    response = input("Continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        return
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print(f"\n🚀 Starting import...\n")
        
        # Import jobs
        stats = JobScraperImporter.import_jobs_batch(jobs_data)
        
        print(f"\n{'='*50}")
        print(f"📊 IMPORT RESULTS")
        print(f"{'='*50}")
        print(f"📋 Total jobs processed: {stats['total']}")
        print(f"✅ Successfully imported: {stats['imported']}")
        print(f"⏭️  Skipped (duplicates): {stats['skipped']}")
        print(f"🚫 Skipped (no logo): {stats['no_logo']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"{'='*50}")
        
        if stats['imported'] > 0:
            print(f"\n🎉 Success! {stats['imported']} jobs added to database")
        
        if stats['skipped'] > 0:
            print(f"\nℹ️  {stats['skipped']} jobs were already in database (skipped)")
        
        if stats['failed'] > 0:
            print(f"\n⚠️  {stats['failed']} jobs failed to import (check logs above)")

def main():
    if len(sys.argv) < 2:
        print("Usage: python import_jobs_from_csv.py <file.csv|file.xlsx>")
        print("\nExample:")
        print("  python import_jobs_from_csv.py jobs.csv")
        print("  python import_jobs_from_csv.py jobs.xlsx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    import_from_file(file_path)

if __name__ == '__main__':
    main()
