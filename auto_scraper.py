"""
Automated Job Scraper for BongThom
Runs daily to scrape new jobs, check duplicates, and import to database
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import re
import logging
from pathlib import Path
from app import create_app, db
from app.models import Job
from sqlalchemy import and_

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BongThomScraper:
    def __init__(self):
        self.app = create_app()
        self.all_jobs = []
        self.new_jobs_count = 0
        self.duplicate_count = 0
        
    def parse_posting_date(self, text):
        """Parse relative posting dates like '2 days ago' or '3 hours'"""
        text = text.lower()
        today = datetime.today()

        # Extract number from text
        num_match = re.search(r"\d+", text)
        if not num_match:
            return ""
            
        if "day" in text:
            days = int(num_match.group())
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")
        elif "hour" in text or "minute" in text:
            return today.strftime("%Y-%m-%d")
        else:
            return ""

    def setup_driver(self):
        """Setup Selenium Chrome driver"""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        return driver

    def job_exists_in_db(self, title, company):
        """Check if job already exists in database"""
        with self.app.app_context():
            existing = Job.query.filter(
                and_(
                    Job.title == title,
                    Job.company == company
                )
            ).first()
            return existing is not None

    def scrape_bongthom(self, max_pages=3):
        """Scrape jobs from BongThom"""
        logger.info("🚀 Starting BongThom scraper...")
        
        driver = self.setup_driver()
        wait = WebDriverWait(driver, 10)
        
        try:
            page = 1
            while page <= max_pages:
                logger.info(f"📄 Scraping page {page}")
                driver.get(f"https://www.bongthom.com/job_list.html?page={page}")

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='job_detail']")))
                soup = BeautifulSoup(driver.page_source, "html.parser")

                job_boxes = soup.select("a[href*='job_detail']")

                if not job_boxes:
                    logger.info(f"No more jobs found on page {page}")
                    break

                for box in job_boxes:
                    desc = box.select_one(".desc")
                    if not desc:
                        continue

                    # Job list fields
                    job_url = box["href"]
                    if not job_url.startswith("http"):
                        job_url = "https://www.bongthom.com" + job_url

                    job_title = desc.select_one("h5 span")
                    job_title = job_title.text.strip() if job_title else ""

                    company = desc.select_one(".ellipsis-text span")
                    company_name = company.text.strip() if company else ""

                    # Extract deadline and posting date from listing
                    deadline = ""
                    posting_date = ""

                    for info in desc.select(".info div"):
                        text = info.get_text(strip=True)
                        # Check for deadline (format: DD-MMM-YYYY like "31-Jan-2026")
                        if re.match(r"\d{1,2}-[A-Za-z]{3}-\d{4}", text):
                            deadline = text
                        # Check for posting date (relative time)
                        elif "day" in text.lower() or "hour" in text.lower():
                            posting_date = self.parse_posting_date(text)

                    # Visit job detail page
                    driver.get(job_url)
                    time.sleep(1)
                    detail = BeautifulSoup(driver.page_source, "html.parser")

                    # Extract company logo from detail page
                    logo_elem = detail.select_one('img[src*="library"]')
                    logo_url = logo_elem["src"] if logo_elem else ""

                    # Announcement Description
                    ann_desc = detail.select_one("#announcemnt-description + .ql-editor")
                    announcement_description = ann_desc.get_text(" ", strip=True) if ann_desc else ""

                    # Contact Info
                    office_address = ""
                    contact_email = ""
                    phone = ""
                    website = ""

                    for li in detail.select("ul.no-list li"):
                        text = li.get_text(" ", strip=True)
                        if "@" in text:
                            contact_email = text
                        elif "http" in text:
                            website = text
                        elif re.search(r"\d{3,}", text):
                            phone = text
                        elif "Phnom Penh" in text or "Cambodia" in text:
                            office_address = text

                    # Attempt to extract deadline from detail page if not found in listing
                    if not deadline:
                        # Look for explicit labels mentioning deadline
                        cand = detail.find(string=re.compile(r"deadline|application deadline|close date", re.I))
                        if cand:
                            parent_text = cand.parent.get_text(" ", strip=True) if cand.parent else cand
                            m = re.search(r"\d{1,2}[-\s][A-Za-z]{3,9}[-\s]\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2}", parent_text)
                            if m:
                                deadline = m.group()

                        # Fallback: search entire detail page for a date-like pattern
                        if not deadline:
                            page_text = detail.get_text(" ", strip=True)
                            m = re.search(r"\d{1,2}-[A-Za-z]{3}-\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2}", page_text)
                            if m:
                                deadline = m.group()

                    # Positions loop
                    positions = detail.select("h3[id^='position-']")

                    for pos in positions:
                        pos_id = pos["id"].replace("position-", "")
                        pos_title = pos.get_text(strip=True)

                        pos_div = detail.find(id=f"job-detail-pos-{pos_id}")
                        if not pos_div:
                            continue

                        location = ""
                        languages = ""
                        career_category = ""
                        schedule = ""
                        salary = ""
                        position_summary = ""
                        duties = ""
                        qualifications = ""
                        skills = ""

                        # Key lists
                        for li in pos_div.select("li"):
                            strong = li.find("strong")
                            value = li.find("span", class_="value")
                            if not strong or not value:
                                continue

                            label = strong.get_text(strip=True).lower()
                            val = value.get_text(" ", strip=True)

                            if "location" in label:
                                location = val
                            elif "languages" in label:
                                languages = val
                            elif "career category" in label:
                                career_category = val
                            elif "schedule" in label:
                                schedule = val
                            elif "salary" in label:
                                salary = val

                        # Position Summary
                        summary_div = pos_div.select_one(".ql-editor")
                        if summary_div:
                            position_summary = summary_div.get_text(" ", strip=True)

                        # Duties
                        duties_ul = pos_div.find("strong", string=re.compile("Duties"))
                        if duties_ul:
                            ul = duties_ul.find_next("ul")
                            if ul:
                                duties = " | ".join(li.get_text(" ", strip=True) for li in ul.find_all("li"))

                        # Qualifications & Skills
                        for strong in pos_div.find_all("strong"):
                            if "Qualifications" in strong.get_text():
                                ul = strong.find_next("ul")
                                if ul:
                                    qualifications = " | ".join(li.get_text(" ", strip=True) for li in ul.find_all("li"))

                            if "Skills" in strong.get_text():
                                ul = strong.find_next("ul")
                                if ul:
                                    skills = " | ".join(li.get_text(" ", strip=True) for li in ul.find_all("li"))

                        # Check for duplicates
                        if self.job_exists_in_db(pos_title, company_name):
                            logger.info(f"⏭️  Duplicate found: {pos_title} at {company_name}")
                            self.duplicate_count += 1
                            continue

                        # Add job data
                        self.all_jobs.append({
                            "Job Title": pos_title,
                            "Announcement Job Title": job_title,
                            "Company Name": company_name,
                            "Company Logo": logo_url,
                            "Posting Date": posting_date,
                            "Deadline": deadline,
                            "Announcement Description": announcement_description,
                            "Office Address": office_address,
                            "Contact Email": contact_email,
                            "Phone": phone,
                            "Website": website,
                            "Location": location,
                            "Languages Required": languages,
                            "Career Category": career_category,
                            "Schedule": schedule,
                            "Salary": salary,
                            "Position Summary": position_summary,
                            "Duties & Responsibilities": duties,
                            "Qualifications": qualifications,
                            "Skills & Knowledge": skills,
                            "Source": "BongThom"
                        })
                        self.new_jobs_count += 1

                page += 1

        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}", exc_info=True)
        finally:
            driver.quit()

        return self.all_jobs

    def clean_data(self, df):
        """Clean scraped data"""
        logger.info("🧹 Cleaning data...")
        
        # Remove duplicates within scraped data
        before_count = len(df)
        df = df.drop_duplicates(subset=['Job Title', 'Company Name'], keep='first')
        after_count = len(df)
        
        if before_count > after_count:
            logger.info(f"🗑️  Removed {before_count - after_count} duplicate rows")
        
        # Clean whitespace
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
        
        # Replace empty strings with None
        df = df.replace('', None)
        
        # Normalize Deadline column to ISO date (YYYY-MM-DD) when present
        if 'Deadline' in df.columns:
            def normalize_deadline(val):
                if val is None:
                    return None
                s = str(val).strip()
                # Try multiple common formats
                for fmt in ("%d-%b-%Y", "%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
                    try:
                        return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
                    except Exception:
                        continue
                # Try to extract a date-like substring
                m = re.search(r"\d{1,2}[-\s][A-Za-z]{3,9}[-\s]\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}", s)
                if m:
                    sub = m.group()
                    for fmt in ("%d-%b-%Y", "%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
                        try:
                            return datetime.strptime(sub, fmt).strftime('%Y-%m-%d')
                        except Exception:
                            continue
                return None

            df['Deadline'] = df['Deadline'].apply(normalize_deadline)
        
        return df

    def import_to_database(self, df):
        """Import cleaned jobs to database"""
        logger.info("💾 Importing to database...")
        
        with self.app.app_context():
            imported = 0
            failed = 0
            
            for _, row in df.iterrows():
                try:
                    # Map CSV columns to Job model
                    job = Job(
                        title=row['Job Title'],
                        company=row['Company Name'],
                        location=row['Location'] or 'Not specified',
                        salary=row['Salary'] or 'Negotiable',
                        job_type=row['Schedule'] or 'Full-time',
                        category=row['Career Category'] or 'Other',
                        description=self.build_description(row),
                        requirements=self.build_requirements(row),
                        logo=row['Company Logo'],
                        contact_email=row['Contact Email'],
                        contact_phone=row['Phone'],
                        website=row['Website'],
                        status='active',
                        deadline=datetime.strptime(row['Deadline'], '%Y-%m-%d') if row.get('Deadline') else None,
                        posted_date=datetime.strptime(row['Posting Date'], '%Y-%m-%d') if row['Posting Date'] else datetime.now()
                    )
                    
                    db.session.add(job)
                    db.session.commit()
                    imported += 1
                    logger.info(f"✅ Imported: {row['Job Title']} at {row['Company Name']}")
                    # Create notifications for this job if it matches any CV keywords
                    try:
                        from app.routes.notifications import check_and_create_notifications
                        check_and_create_notifications(str(job.id))
                    except Exception as e:
                        logger.error(f"⚠️ Failed to create notifications for job {job.id}: {str(e)}")
                    
                except Exception as e:
                    db.session.rollback()
                    failed += 1
                    logger.error(f"❌ Failed to import {row['Job Title']}: {str(e)}")
            
            logger.info(f"\n📊 Import Summary:")
            logger.info(f"✅ Successfully imported: {imported}")
            logger.info(f"❌ Failed: {failed}")

    def build_description(self, row):
        """Build job description from multiple fields"""
        parts = []
        
        if row['Announcement Description']:
            parts.append(row['Announcement Description'])
        
        if row['Position Summary']:
            parts.append(f"\n\n**Position Summary:**\n{row['Position Summary']}")
        
        if row['Duties & Responsibilities']:
            parts.append(f"\n\n**Duties & Responsibilities:**\n{row['Duties & Responsibilities']}")
        
        return '\n'.join(parts) if parts else 'No description available'

    def build_requirements(self, row):
        """Build requirements from qualifications and skills"""
        parts = []
        
        if row['Qualifications']:
            parts.append(f"**Qualifications:**\n{row['Qualifications']}")
        
        if row['Skills & Knowledge']:
            parts.append(f"\n**Skills & Knowledge:**\n{row['Skills & Knowledge']}")
        
        if row['Languages Required']:
            parts.append(f"\n**Languages Required:**\n{row['Languages Required']}")
        
        return '\n'.join(parts) if parts else 'No specific requirements listed'

    def run(self):
        """Main execution method"""
        start_time = datetime.now()
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 AUTO SCRAPER STARTED at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*60}\n")
        
        # Scrape jobs
        jobs = self.scrape_bongthom(max_pages=3)
        
        if not jobs:
            logger.info("ℹ️  No new jobs found. All jobs are duplicates or no jobs available.")
            return
        
        # Save to CSV
        df = pd.DataFrame(jobs)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"bongthom_scraped_{timestamp}.csv"
        
        # Clean data
        df = self.clean_data(df)
        
        # Save CSV
        df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
        logger.info(f"💾 Saved CSV: {csv_filename}")
        
        # Import to database
        self.import_to_database(df)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ AUTO SCRAPER COMPLETED")
        logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        logger.info(f"🆕 New jobs found: {self.new_jobs_count}")
        logger.info(f"⏭️  Duplicates skipped: {self.duplicate_count}")
        logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    scraper = BongThomScraper()
    scraper.run()
