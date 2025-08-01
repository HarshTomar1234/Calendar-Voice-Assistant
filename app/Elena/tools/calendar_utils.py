
"""
Utility functions for Google Calendar integration.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define scopes needed for Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Path for token storage
TOKEN_PATH = Path(os.path.expanduser("~/.credentials/calendar_token.json"))
CREDENTIALS_PATH = Path("credentials.json")


def get_calendar_service():
    """
    Authenticate and create a Google Calendar service object.

    Returns:
        A Google Calendar service object or None if authentication fails
    """
    creds = None

    # Check if token exists and is valid
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_info(
            json.loads(TOKEN_PATH.read_text()), SCOPES
        )

    # If credentials don't exist or are invalid, refresh or get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If credentials.json doesn't exist, we can't proceed with OAuth flow
            if not CREDENTIALS_PATH.exists():
                print(
                    f"Error: {CREDENTIALS_PATH} not found. Please follow setup instructions."
                )
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            # Request offline access to get refresh tokens
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

        # Save the credentials for the next run
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())

    # Create and return the Calendar service
    return build("calendar", "v3", credentials=creds)


def format_event_time(event_time):
    """
    Format an event time into a human-readable string.

    Args:
        event_time (dict): The event time dictionary from Google Calendar API

    Returns:
        str: A human-readable time string
    """
    if "dateTime" in event_time:
        # This is a datetime event
        dt = datetime.fromisoformat(event_time["dateTime"].replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %I:%M %p")
    elif "date" in event_time:
        # This is an all-day event
        return f"{event_time['date']} (All day)"
    return "Unknown time format"


def parse_datetime(datetime_str):
    """
    Parse a datetime string into a datetime object.

    Args:
        datetime_str (str): A string representing a date and time

    Returns:
        datetime: A datetime object or None if parsing fails
    """
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y",
        "%B %d, %Y %H:%M",
        "%B %d, %Y %I:%M %p",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue

    return None


def get_current_time() -> dict:
    """
    Get the current time and date
    """
    now = datetime.now()

    # Format date as MM-DD-YYYY
    formatted_date = now.strftime("%m-%d-%Y")

    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "formatted_date": formatted_date,
    }


def convert_relative_date(date_input: str) -> str:
    """
    Convert relative date expressions to YYYY-MM-DD format.
    
    Args:
        date_input (str): Date input like 'today', 'tomorrow', 'next week', or already formatted date
        
    Returns:
        str: Date in YYYY-MM-DD format
    """
    if not date_input or date_input.strip() == "":
        return ""
    
    date_input = date_input.lower().strip()
    today = datetime.now().date()
    
    # Handle relative dates
    if date_input in ["today"]:
        return today.strftime("%Y-%m-%d")
    elif date_input in ["tomorrow"]:
        return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_input in ["yesterday"]:
        return (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    elif "next week" in date_input:
        return (today + datetime.timedelta(weeks=1)).strftime("%Y-%m-%d")
    elif "next month" in date_input:
        return (today + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    elif "this week" in date_input:
        return today.strftime("%Y-%m-%d")
    elif "this month" in date_input:
        return today.strftime("%Y-%m-%d")
    
    # If it's already in a valid format or unrecognized, return as-is
    try:
        # Try to parse as existing YYYY-MM-DD format
        datetime.strptime(date_input, "%Y-%m-%d")
        return date_input
    except ValueError:
        pass
    
    # Try to parse other common formats and convert to YYYY-MM-DD
    parsed_date = parse_datetime(date_input)
    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    
    # If all else fails, return today's date
    return today.strftime("%Y-%m-%d")
