import threading
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.messagebox import showinfo
from tkinter import filedialog, ttk, messagebox
from tkcalendar import DateEntry
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

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ICS to Google Tasks Converter")
        self.geometry("315x175")

        self.file_url = tk.StringVar()
        self.include_zoom = tk.BooleanVar()
        self.sort_chronologically = tk.BooleanVar()

        self.create_widgets()

    def create_widgets(self):
        file_label = tk.Label(self, text="ICS File:")
        file_label.grid(row=0, column=0, sticky="w")

        file_entry = tk.Entry(self, textvariable=self.file_url)
        file_entry.grid(row=0, column=1)

        file_button = tk.Button(self, text="Browse", command=self.browse_file)
        file_button.grid(row=0, column=2)

        start_date_label = tk.Label(self, text="Start Date:")
        start_date_label.grid(row=1, column=0, sticky="w")

        # DateEntry widget for date selection
        self.start_date_entry = DateEntry(self, width=12, background='darkblue',
        foreground='white', borderwidth=2)
        self.start_date_entry.grid(row=1, column=1, sticky="w")

        include_zoom_checkbox = tk.Checkbutton(self, text="Include Zoom events", variable=self.include_zoom)
        include_zoom_checkbox.grid(row=2, column=0, sticky="w")

        sort_chronologically_checkbox = tk.Checkbutton(self, text="Sort chronologically", variable=self.sort_chronologically)
        sort_chronologically_checkbox.grid(row=3, column=0, sticky="w")

        execute_button = tk.Button(self, text="Execute", command=self.execute)
        execute_button.grid(row=4, column=0, columnspan=3)

        # Button to clear all tasks
        clear_tasks_button = tk.Button(self, text="Clear all tasks", command=self.clear_all_tasks)
        clear_tasks_button.grid(row=5, column=0, columnspan=3)

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[('ICS Files', '*.ics')])
        self.file_url.set(file_path)

    def execute(self):
        file_url = self.file_url.get()
        start_date_str = self.start_date_entry.get_date().strftime("%m/%d/%Y")  # Get the selected date from the DateEntry widget
        include_zoom = self.include_zoom.get()
        sort_chronologically = self.sort_chronologically.get()

        threading.Thread(target=self.parse_ics, args=(file_url, start_date_str, include_zoom, sort_chronologically)).start()

        messagebox.showinfo("Info", "Processing started!")

    

    def clear_all_tasks(self):
        try:
            credentials = self.get_credentials()
            service = build('tasks', 'v1', credentials=credentials)
            tasklist = self.get_tasklist(service)

            # Initialize a variable for the page token.
            page_token = None

            while True:
                # Get a page of tasks.
                response = service.tasks().list(tasklist=tasklist, pageToken=page_token).execute()

                tasks = response.get('items', [])
                for task in tasks:
                    service.tasks().delete(tasklist=tasklist, task=task['id']).execute()

                # Get the token for the next page.
                page_token = response.get('nextPageToken')

                # If there is no next page, break the loop.
                if not page_token:
                    break

        except Exception as e:
            return f"Failed to clear tasks: {e}"

        return "All tasks cleared!"



    def parse_ics(self, file_url, start_date_str, include_zoom, sort_chronologically):
        try:
            with open(file_url, 'r') as file:
                cal = Calendar.from_ical(file.read())
        except Exception as e:
            return f"Error reading file: {e}"

        start_date = datetime.strptime(start_date_str, "%m/%d/%Y").date() if start_date_str else None
        assignments = []

        for component in cal.walk():
            if component.name == "VEVENT":
                description = component.get('description')
                summary = component.get('summary')

                match = re.search(r'\b[A-Za-z]{3}\d{4}\b', summary)
                        
                class_code = match.group(0) if match else None

                zoom_link = None
                if description and 'zoom.us' in description:
                    zoom_link = re.search("(?P<url>https?://[^\s]+)", description).group("url")
                    
                # If include_zoom is False and zoom_link is not None, skip this event
                if not include_zoom and zoom_link:
                    continue

                dtstart = component.get('dtstart').dt
                dtstart = dtstart.astimezone(timezone.utc).date() if isinstance(dtstart, datetime) else dtstart

                if start_date and dtstart < start_date:
                    continue

                assignments.append((dtstart, f"{class_code}: {summary}", zoom_link))

        if sort_chronologically:
            assignments.sort()

        credentials = self.get_credentials()
        if not credentials:
            return "Failed to authenticate with Google."

        try:
            service = build('tasks', 'v1', credentials=credentials)
            tasklist = self.get_tasklist(service)
        except Exception as e:
            return f"Failed to connect to Google Tasks: {e}"

        for dtstart, title, zoom_link in assignments:
            task = {
                'title': title,
                'notes': f"Due date: {dtstart}\n{zoom_link if zoom_link else ''}",
                'due': dtstart.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            }

            try:
                service.tasks().insert(tasklist=tasklist, body=task).execute()
            except Exception as e:
                return f"Failed to add task: {e}"

        return "Success"

    def get_credentials(self):
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
        return creds

    def get_tasklist(self, service):
        results = service.tasklists().list().execute()
        items = results.get('items', [])

        if not items:
            tasklist = {
                'title': 'ICS to Google Tasks'
            }
            tasklist = service.tasklists().insert(body=tasklist).execute()
        else:
            tasklist = items[0]['id']
        return tasklist


if __name__ == "__main__":
    app = Application()
    app.mainloop()
