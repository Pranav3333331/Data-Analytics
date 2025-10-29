import pandas as pd
import requests
from datetime import datetime
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import pickle
import time

# CONFIGURATION - CHANGE THESE VALUES

# Number of top cryptocurrencies to track (by market cap)
TOP_CRYPTO_COUNT = 250  # (max 250 for free API)

# Your Google Sheet name (MUST CREATE THIS FIRST!)
GOOGLE_SHEET_NAME = "Crypto Price Tracker" 

# Google Sheets API scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# GOOGLE SHEETS AUTHENTICATION

import gspread

def authenticate_google_sheets_service():
    """
    Authenticates with Google Sheets using a Service Account JSON.
    """
    # Ensure your service account file is named and referenced correctly
    gc = gspread.service_account(filename='service_account.json')
    print("✓ Service Account authentication successful!")
    return gc

    
    # Authorize gspread
    client = gspread.authorize(creds)
    print("✓ Authentication successful!")
    return client

# STEP 1: EXTRACT DATA FROM API

def extract_data():
    """
    Fetches live cryptocurrency prices from CoinGecko API.
    Returns a pandas DataFrame with crypto data.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting data extraction...")
    print(f"Fetching top {TOP_CRYPTO_COUNT} cryptocurrencies by market cap...")
    
    try:
        # CoinGecko API endpoint (free, no key required)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        
        # Parameters for the API request
        params = {
            'vs_currency': 'usd',              # Prices in USD
            'order': 'market_cap_desc',        # Order by market cap (largest first)
            'per_page': TOP_CRYPTO_COUNT,      # Number of results to fetch
            'page': 1,                         # Page number
            'sparkline': False                 # Don't include chart data
        }
        
        # Make the API request
        response = requests.get(url, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            print(f"✓ Successfully extracted {len(df)} cryptocurrencies")
            print(f"✓ Range: #{1} to #{len(df)} by market cap")
            return df
        else:
            print(f"✗ API request failed with status code: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Error during extraction: {str(e)}")
        return None

# STEP 2: TRANSFORM AND CLEAN DATA

def transform_data(df):
    """
    Cleans and transforms the raw data.
    Returns a cleaned DataFrame ready for Google Sheets.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting data transformation...")
    
    try:
        # Select only the columns we need
        columns_to_keep = [
            'market_cap_rank',                # Rank by market cap
            'name',                           # Cryptocurrency name
            'symbol',                         # Symbol (BTC, ETH, etc.)
            'current_price',                  # Current price in USD
            'market_cap',                     # Total market capitalization
            'total_volume',                   # 24h trading volume
            'price_change_percentage_24h',    # 24h price change %
            'circulating_supply',             # Circulating supply
            'total_supply',                   # Total supply
            'ath',                            # All-time high price
            'atl'                             # All-time low price
        ]
        
        df_clean = df[columns_to_keep].copy()
        
        # Rename columns for clarity
        df_clean.columns = [
            'Rank',
            'Cryptocurrency',
            'Symbol',
            'Price (USD)',
            'Market Cap',
            'Volume (24h)',
            '24h Change (%)',
            'Circulating Supply',
            'Total Supply',
            'All-Time High',
            'All-Time Low'
        ]
        
        # Handle missing values
        df_clean = df_clean.fillna(0)
        
        # Round numerical values for better readability
        df_clean['Price (USD)'] = df_clean['Price (USD)'].round(2)
        df_clean['Market Cap'] = df_clean['Market Cap'].round(0)
        df_clean['Volume (24h)'] = df_clean['Volume (24h)'].round(0)
        df_clean['24h Change (%)'] = df_clean['24h Change (%)'].round(2)
        df_clean['Circulating Supply'] = df_clean['Circulating Supply'].round(0)
        df_clean['Total Supply'] = df_clean['Total Supply'].round(0)
        df_clean['All-Time High'] = df_clean['All-Time High'].round(2)
        df_clean['All-Time Low'] = df_clean['All-Time Low'].round(6)
        
        # Convert symbol to uppercase
        df_clean['Symbol'] = df_clean['Symbol'].str.upper()
        
        # Add timestamp
        df_clean['Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add calculated columns
        df_clean['Market Cap (B)'] = (df_clean['Market Cap'] / 1_000_000_000).round(2)
        df_clean['% from ATH'] = (((df_clean['Price (USD)'] - df_clean['All-Time High']) / df_clean['All-Time High']) * 100).round(2)
        
        print(f"✓ Data cleaned successfully: {df_clean.shape[0]} rows, {df_clean.shape[1]} columns")
        print(f"\nPreview of top 10 cryptocurrencies:")
        print(df_clean.head(10)[['Rank', 'Cryptocurrency', 'Symbol', 'Price (USD)', 'Market Cap (B)', '24h Change (%)']].to_string(index=False))
        
        return df_clean
        
    except Exception as e:
        print(f"✗ Error during transformation: {str(e)}")
        return None

# STEP 3: SEND DATA TO GOOGLE SHEETS

def send_to_google_sheets(df, client):
    """
    Sends the cleaned data directly to YOUR Google Sheet.
    Clears old data and uploads new data with formatting.
    """
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sending data to Google Sheets...")
    
    try:
        # Open your Google Sheet by name
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        
        # Clear existing data
        sheet.clear()
        print("✓ Cleared old data from sheet")
        
        # Fill NaN and infinite values BEFORE exporting to Google Sheets!
        import numpy as np
        df = df.replace([np.nan, np.inf, -np.inf], '')  # replaces NaN/inf/-inf with empty string

        # Prepare data (header + rows) after fixing all invalid values
        data_to_upload = [df.columns.tolist()] + df.values.tolist()

        # Upload to Google Sheets starting at cell A1
        sheet.update('A1', data_to_upload)

        print(f"✓ Uploaded {len(df)} rows to Google Sheets")
        
        # Format header row (blue background, white text, bold)
        header_format = {
            "backgroundColor": {"red": 0.26, "green": 0.52, "blue": 0.96},
            "textFormat": {
                "bold": True,
                "foregroundColor": {"red": 1, "green": 1, "blue": 1}
            },
            "horizontalAlignment": "CENTER"
        }
        sheet.format(f'A1:{chr(65 + len(df.columns) - 1)}1', header_format)
        
        # Freeze header row so it stays visible when scrolling
        sheet.freeze(rows=1)
        
        # Auto-resize columns for better readability
        sheet.columns_auto_resize(0, len(df.columns))
        
        # Get the spreadsheet URL
        sheet_url = f"https://docs.google.com/spreadsheets/d/1Cl6cz7xblBjt5BRmGI5vpGHl_mF8owWt3YGUEo8yN1g/edit?gid=0#gid=0"
        
        print(f"✓ Formatting applied successfully")
        print(f"✓ Sheet URL: {sheet_url}")
        
        # Print summary statistics
        print(f"\n📊 Data Summary:")
        print(f"  • Total cryptocurrencies: {len(df)}")
        print(f"  • Total market cap: ${df['Market Cap'].sum():,.0f}")
        print(f"  • Average 24h change: {df['24h Change (%)'].mean():.2f}%")
        print(f"  • Highest price: ${df['Price (USD)'].max():,.2f}")
        print(f"  • Lowest price: ${df['Price (USD)'].min():.6f}")
        
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"\n✗ ERROR: Could not find Google Sheet named '{GOOGLE_SHEET_NAME}'")
        print("\n📝 Quick Fix:")
        print("1. Go to https://sheets.google.com")
        print(f"2. Create a new sheet named exactly: '{GOOGLE_SHEET_NAME}'")
        print("3. Run this script again")
    except Exception as e:
        print(f"✗ Error sending to Google Sheets: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Make sure you created a Google Sheet with the exact name specified")
        print("2. Make sure you're logged into the correct Google account")
        print("3. Try deleting token.pickle and running again")

import smtplib
from email.message import EmailMessage

def email_sheet_link():
    # Replace with your info
    sender = "pranavpaliwal3138@gmail.com"
    password = "qptydetjrtmilwwe"  # create a Gmail app password (not your normal login)
    receiver = "pranavpaliwal3138@gmail.com"
    sheet_link = "https://docs.google.com/spreadsheets/d/1Cl6cz7xblBjt5BRmGI5vpGHl_mF8owWt3YGUEo8yN1g/edit?gid=0#gid=0"
    
    msg = EmailMessage()
    msg.set_content(f"Hello!\n\nYour Google Sheet has been updated.\n\nOpen it here: {sheet_link}\n\n-Automated Bot")
    msg['Subject'] = "Crypto Price Tracker Updated"
    msg['From'] = sender
    msg['To'] = receiver

    # Sending the email (no setup needed except app password)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

# MAIN PIPELINE FUNCTION
def run_pipeline():
    """
    Executes the complete ETL pipeline:
    1. Authenticate with Google Sheets
    2. Extract data from CoinGecko API
    3. Transform and clean data
    4. Send directly to Google Sheets
    """
    print("\n" + "="*70)
    print("   CRYPTO PRICE TRACKER - PYTHON TO GOOGLE SHEETS (TOP 250)")
    print("="*70)
    
    try:
        # Authenticate with Google Sheets (opens browser ONCE on first run)
        client = authenticate_google_sheets_service()
        
        # Step 1: Extract
        raw_data = extract_data()
        if raw_data is None:
            print("\n✗ Pipeline failed at extraction stage")
            return
        
        # Wait 1 second to respect API rate limits
        time.sleep(1)
        
        # Step 2: Transform
        cleaned_data = transform_data(raw_data)
        if cleaned_data is None:
            print("\n✗ Pipeline failed at transformation stage")
            return
        
        # Step 3: Send to Google Sheets
        send_to_google_sheets(cleaned_data, client)
        
        print("\n" + "="*70)
        print("✓✓✓ PIPELINE COMPLETED SUCCESSFULLY! ✓✓✓")
        print("✓ Check your Google Sheet for updated cryptocurrency data!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ PIPELINE ERROR: {str(e)}\n")

# RUN THE PIPELINE
if __name__ == "__main__":
    run_pipeline()
    email_sheet_link()

