#Automated Data Pipeline & Reporting

Overview:
Automates extraction from CoinGecko API.
Cleans, formats, and loads data into Google Sheets.
Sends email notifications after each update.
Schedules ETL pipeline to run every 5 minutes.

Features:
Fetches top 250 cryptocurrencies and market information.
Data cleaning, validation, and formatting.
Google Sheets integration with authentication.
Fully automated execution via Python scheduler.
Email notifications with Sheet link.

Setup Steps:
Clone this repository:
git clone https://github.com/YOUR_GITHUB_USERNAME/Automated-Data-Pipeline-Reporting.git
Install requirements:
pip install -r requirements.txt

Create a new Google Sheet and name it exactly as in pipeline.py (default: Crypto Price Tracker).
Download your Google Service Account key file (service_account.json)—see instructions below.
Place the service_account.json in your project directory (do NOT upload to GitHub).

(Optional) Set up a Gmail App Password if you want to enable email notifications.
How to Download the Service Account File:
Go to Google Cloud Console: https://console.cloud.google.com/
Make sure the correct project is selected.
Navigate to IAM & Admin > Service Accounts.
Click Create Service Account.
Enter a name and description, then click Create and Continue.
Assign the Editor role or just Sheets API access as needed.
Click Done.
In the Service Accounts list, click your account, then go to Keys tab.
Click Add Key > Create New Key > JSON > Create.
Download the service_account.json file to your machine.
Share your Google Sheet with the service account email (found inside your JSON file).

How to Run:
From your terminal, run:
python scheduler.py
The pipeline will run immediately for a test, then continue every 5 minutes.

File Structure:
pipeline.py — ETL, Google Sheets, and email logic
scheduler.py — job scheduling script
requirements.txt — required Python dependencies

Credits:
Data from CoinGecko API
Sheets API, Python open-source libraries