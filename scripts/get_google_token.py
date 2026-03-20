#!/usr/bin/env python3
"""
One-time script to get Google Calendar OAuth token.
Run this locally to authorize your bot to access your calendar.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os
import json

# Scopes required for calendar access
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_token():
    """Get Google Calendar OAuth token."""
    creds = None
    
    # Check if we have saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load client secrets
            with open('client_secret.json', 'r') as f:
                client_config = json.load(f)
            
            # Check if it's a web or desktop app
            if 'web' in client_config:
                # Web application - need to add redirect URI
                print("\n⚠️  You're using a Web application OAuth client.")
                print("You need to add this redirect URI in Google Cloud Console:")
                print("http://localhost:8080/")
                print("\nSteps:")
                print("1. Go to Google Cloud Console → APIs & Services → Credentials")
                print("2. Click on your OAuth 2.0 Client ID")
                print("3. Under 'Authorized redirect URIs', add: http://localhost:8080/")
                print("4. Save and try again\n")
                
                # Try to run with web flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', 
                    SCOPES,
                    redirect_uri='http://localhost:8080/'
                )
            else:
                # Desktop application
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', SCOPES)
            
            creds = flow.run_local_server(port=8080)
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("\n✅ Success! Your tokens:")
    print(f"\nAccess Token:\n{creds.token}")
    print(f"\nRefresh Token:\n{creds.refresh_token}")
    print(f"\nClient ID:\n{creds.client_id}")
    print(f"\nClient Secret:\n{creds.client_secret}")
    
    print("\n" + "="*60)
    print("📝 Copy these to your .dev.vars file:")
    print("="*60)
    print(f"GOOGLE_CALENDAR_ACCESS_TOKEN={creds.token}")
    print(f"GOOGLE_CALENDAR_REFRESH_TOKEN={creds.refresh_token}")
    print(f"GOOGLE_CALENDAR_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CALENDAR_CLIENT_SECRET={creds.client_secret}")
    print("="*60)
    
    print("\n✨ With these credentials, your bot will:")
    print("   • Automatically refresh the access token when it expires")
    print("   • Work indefinitely without manual token updates")
    print("   • Handle token expiration gracefully")
    
    print("\n⚠️  Keep these credentials secure!")
    print("   • Never commit .dev.vars to git")
    print("   • Use 'wrangler secret put' for production deployment")
    
    return creds

if __name__ == '__main__':
    print("🔐 Google Calendar OAuth Token Generator")
    print("=" * 50)
    print("\nMake sure you have 'client_secret.json' in this directory")
    print("(Download it from Google Cloud Console)\n")
    
    input("Press Enter to start the OAuth flow...")
    
    try:
        get_calendar_token()
    except FileNotFoundError:
        print("\n❌ Error: client_secret.json not found!")
        print("Download it from Google Cloud Console → Credentials")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf you see 'redirect_uri_mismatch', follow these steps:")
        print("1. Go to Google Cloud Console → APIs & Services → Credentials")
        print("2. Click on your OAuth 2.0 Client ID")
        print("3. Under 'Authorized redirect URIs', add: http://localhost:8080/")
        print("4. Save and try running this script again")

