import schedule
import time
from datetime import datetime
from pipeline import run_pipeline,email_sheet_link

print("="*70)
print("    CRYPTO TRACKER - AUTOMATED GOOGLE SHEETS UPDATER")
print("="*70)
print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nSchedule: Updates Google Sheets daily at 09:00 AM")
print("\nPress Ctrl+C to stop\n")
print("="*70)

# Schedule to run every 5 mins (customize as needed)
schedule.every(5).minutes.do(lambda: (run_pipeline(), email_sheet_link()))

# Optionally, run pipeline immediately on startup
print("\n🚀 Running pipeline now (initial test run)...")
run_pipeline()
email_sheet_link()
print("\n⏰ Scheduler is active. Waiting for next automatic update...")

while True:
    schedule.run_pending()
    time.sleep(60)
