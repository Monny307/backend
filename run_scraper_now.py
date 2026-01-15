"""
Manual scraper runner - for testing or manual runs
"""
from auto_scraper import BongThomScraper

if __name__ == "__main__":
    print("\n🚀 Running BongThom scraper manually...")
    scraper = BongThomScraper()
    scraper.run()
    print("\n✅ Manual scrape complete!")
