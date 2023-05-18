import requests
from icalendar import Calendar
from datetime import datetime, date, timezone
import re
from collections import defaultdict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/tasks.readonly', 'https://www.googleapis.com/auth/tasks']

def parse_ics(file_url, start_date_str, include_zoom, sort_chronologically):
    try:
        response = requests.get(file_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return
    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        return

    cal = Calendar.from_ical(response.text)
    start_date = datetime.strptime(start_date_str, "%m/%d/%Y").date() if start_date_str else None
    assignments = []

    for component in cal.walk():
        if component.name == "VEVENT":
            description = component.get('description')
            summary = component.get('summary')

            match = re.search(r'\b[A-Za-z]{3}\d{4}\b', summary)
            class_code = match.group(0) if match else None
            start = component.get('dtstart').dt
            
            if isinstance(start, datetime):
                start = start.date()

            if start_date and start < start_date:
                continue

            zoom = any(word in description for word in ['zoom', 'Zoom', 'ZOOM']) if description else False

            if not include_zoom and zoom:
                continue

            assignments.append((start, summary))

    if sort_chronologically:
        assignments.sort()

    service = connect_to_tasks_api()
    for assignment in assignments:
        due_date = assignment[0]
        task_title = assignment[1]
        create_task(service, task_title, due_date)

def connect_to_tasks_api():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
                        pickle.dump(creds, token)

    service = build('tasks', 'v1', credentials=creds)
    return service

def create_task(service, task_title, due_date):
    task = {
        'title': task_title,
        'due': due_date.isoformat() + 'T00:00:00Z'
    }

    try:
        result = service.tasks().insert(tasklist='@default', body=task).execute()
        print(f"Created task {result['title']}")
    except Exception as e:
        print(f"An error occurred: {e}")

file_url = input("Enter .ics file URL: ")
start_date_str = input("Enter start date (MM/DD/YYYY): ")
include_zoom = input("Include zoom events? (Y/N): ").lower() == 'y'
sort_chronologically = input("Sort chronologically? (Y/N): ").lower() == 'y'

parse_ics(file_url, start_date_str, include_zoom, sort_chronologically)