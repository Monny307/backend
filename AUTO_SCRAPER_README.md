# Auto Job Scraper

Automated job scraping system that runs daily to collect jobs from BongThom.

## Features

- 🤖 **Automated Daily Scraping**: Runs automatically every day at 2:00 AM
- 🔍 **Duplicate Detection**: Checks database before importing (avoids duplicates)
- 🖼️ **No Logo Filtering**: Keeps all jobs, even without company logos
- 🧹 **Auto Cleaning**: Removes duplicates and cleans data
- 💾 **Auto Import**: Directly imports to PostgreSQL database
- 📊 **Detailed Logging**: All operations logged to files

## Files

### 1. `auto_scraper.py`
Main scraper class with:
- Web scraping with Selenium
- Duplicate detection against database
- Data cleaning
- Database import

### 2. `scheduler.py`
Scheduler that runs the scraper daily:
- Uses APScheduler
- Scheduled for 2:00 AM daily (configurable)
- Runs once on startup

### 3. `run_scraper_now.py`
Manual runner for testing or on-demand scraping

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install selenium beautifulsoup4 pandas APScheduler openpyxl
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### 2. Install Chrome WebDriver

The scraper uses Chrome. Make sure you have:
- Google Chrome installed
- ChromeDriver installed (matches your Chrome version)

**Download ChromeDriver:**
- Visit: https://chromedriver.chromium.org/downloads
- Download version matching your Chrome version
- Add to PATH or place in backend folder

**OR use automatic installation:**
```bash
pip install webdriver-manager
```

Then update `auto_scraper.py` to use webdriver_manager (optional).

## Usage

### Option 1: Run Manually (Test First!)

```bash
cd backend
python run_scraper_now.py
```

This will:
1. Scrape all pages from BongThom
2. Check for duplicates
3. Save CSV with timestamp
4. Import new jobs to database

### Option 2: Run Scheduled (Production)

```bash
cd backend
python scheduler.py
```

This will:
1. Run scraper immediately on startup
2. Schedule daily runs at 2:00 AM
3. Keep running (press Ctrl+C to stop)

### Option 3: Change Schedule Time

Edit `scheduler.py` line 37:
```python
# Run at different time (e.g., 8:00 PM)
scheduler.add_job(
    run_scraper,
    CronTrigger(hour=20, minute=0),  # 8:00 PM daily
    ...
)
```

## How It Works

### 1. Scraping Process
```
BongThom → Selenium → BeautifulSoup → Extract Data
```

For each job listing:
- Visits job detail page
- Extracts all positions (one row per position)
- Collects contact info, requirements, etc.
- **Keeps jobs without logos** (empty logo field)

### 2. Duplicate Detection

Before importing, checks database:
```python
Job.query.filter(
    Job.title == title,
    Job.company == company
).first()
```

If exists → Skip
If new → Import

### 3. Data Cleaning

- Remove duplicate rows in scraped data
- Clean whitespace
- Replace empty strings with None

### 4. Database Import

Maps BongThom data to your Job model:
- `Job Title` → `title`
- `Company Name` → `company`
- `Company Logo` → `logo` (empty if no logo)
- `Contact Email` → `contact_email`
- `Phone` → `contact_phone`
- `Website` → `website`
- etc.

## Logs

### `scraper_logs.log`
All scraping operations:
- Jobs scraped
- Duplicates found
- Import results
- Errors

### `scheduler.log`
Scheduler operations:
- Schedule triggers
- Run times
- Status updates

## Example Output

```
==============================================================
🤖 AUTO SCRAPER STARTED at 2026-01-15 02:00:00
==============================================================

📄 Scraping page 1
📄 Scraping page 2
⏭️  Duplicate found: Marketing Manager at ABC Company
✅ Imported: Sales Executive at XYZ Corp
✅ Imported: IT Developer at Tech Solutions
🧹 Cleaning data...
💾 Saved CSV: bongthom_scraped_20260115_020145.csv

📊 Import Summary:
✅ Successfully imported: 15
❌ Failed: 0

==============================================================
✅ AUTO SCRAPER COMPLETED
⏱️  Duration: 245.67 seconds
🆕 New jobs found: 15
⏭️  Duplicates skipped: 8
==============================================================
```

## Troubleshooting

### Chrome/ChromeDriver Issues

**Error: "chromedriver not found"**
```bash
# Install webdriver-manager
pip install webdriver-manager

# Update auto_scraper.py to use:
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

### Import Errors

**Error: "contact_phone too long"**

Some jobs have addresses in phone field. The scraper will log these as failed but continue with other jobs.

To fix permanently, increase phone field size:
```bash
# Create migration
flask db revision -m "increase_contact_phone_size"

# Edit migration file to change:
op.alter_column('jobs', 'contact_phone', type_=sa.String(500))

# Run migration
flask db upgrade
```

## Production Deployment

### Run as Background Service (Linux/Ubuntu)

Create systemd service:
```bash
sudo nano /etc/systemd/system/job-scraper.service
```

Add:
```ini
[Unit]
Description=BongThom Job Scraper
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/.venv/bin"
ExecStart=/path/to/backend/.venv/bin/python scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable job-scraper
sudo systemctl start job-scraper
sudo systemctl status job-scraper
```

### Run as Windows Service

Use NSSM (Non-Sucking Service Manager):
1. Download NSSM
2. Run: `nssm install JobScraper`
3. Set path to `python.exe` and `scheduler.py`
4. Start service

## Configuration

### Adjust Scraping Frequency

In `scheduler.py`:
```python
# Every 6 hours
CronTrigger(hour='*/6')

# Twice daily (2 AM and 2 PM)
scheduler.add_job(..., CronTrigger(hour='2,14'))

# Only weekdays
CronTrigger(day_of_week='mon-fri', hour=2)
```

### Adjust Pages Scraped

In `auto_scraper.py`:
```python
# Scrape 10 pages instead of 7
jobs = self.scrape_bongthom(max_pages=10)
```

### Add More Sources

Extend `BongThomScraper` class to scrape other sites:
```python
def scrape_camhr(self):
    # Add CamHR scraping logic
    pass

def run(self):
    self.scrape_bongthom()
    self.scrape_camhr()
    # etc.
```

## Notes

- ✅ Keeps jobs **with OR without** logos
- ✅ Checks duplicates **before** importing
- ✅ Auto-cleans data
- ✅ Logs everything
- ✅ Runs daily automatically
- ✅ Can run manually anytime

## Support

If scraper fails:
1. Check `scraper_logs.log`
2. Verify Chrome/ChromeDriver versions match
3. Check database connection
4. Run manually first: `python run_scraper_now.py`
