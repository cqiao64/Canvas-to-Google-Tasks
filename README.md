# Google Tasks Canvas ICS Importer

This Python script is designed to import assignments from Canvas (or other systems that export .ics files) into Google Tasks. This allows you to keep track of your assignments directly in Google Tasks. The script includes a graphical user interface (GUI) built with Tkinter, which provides an easy and convenient way to input information and execute the script.

## Requirements

This script requires the following Python packages:

- `requests`
- `icalendar`
- `google-auth`
- `google-auth-httplib2`
- `google-auth-oauthlib`
- `google-api-python-client`
- `pickle`
- `tkinter`
- `tkcalendar`

You can install these using pip:

pip install requests icalendar google-auth google-auth-httplib2 google-auth-oauthlib google-api-python-client pickle tkcalendar

## Usage

You can run the script in the command line by executing:

python main.py

When running the script, it will prompt you to enter the following:

- The URL of the .ics file you want to import tasks from.
- The start date in the format MM/DD/YYYY (tasks prior to this date will not be imported).
- Whether or not to include Zoom events.
- Whether or not to sort tasks chronologically.

Click the "Execute" button to start the process. The script will parse the .ics file, create tasks in Google Tasks for each event, and sort them as specified. If you want to clear all tasks, you can use the "Clear all tasks" button.

## Google API Configuration

Before running the script, you need to setup Google Tasks API in your project:

1. Use [this wizard](https://console.developers.google.com/start/api?id=tasks) to create or select a project in the Google Developers Console and automatically turn on the API. 
2. Click **Continue**, then **Go to credentials**.
3. On the **Add credentials to your project** page, click the **Cancel** button.
4. At the top of the page, select the **OAuth consent screen** tab. Select an **Email address**, enter a **Product name** if not already set, and click the **Save** button.
5. Select the **Credentials** tab, click the **Create credentials** button and select **OAuth client ID**.
6. Select the application type **Other**, enter the name "Google Tasks API Quickstart", and click the **Create** button.
7. Click **OK** to dismiss the resulting dialog.
8. Click the file_download (Download JSON) button to the right of the client ID.
9. Move this file to your working directory and rename it `credentials.json`.

## Notes

This script uses OAuth 2.0 to authorize the application to access Google Tasks API. The first time you run the script, it will open a new window prompting you to authorize access. Upon successful authorization, the script will store your access token in a file named 'token.pickle', so that you don't need to re-authorize every time you run the script.

# Canvas Event to Text File

As an alternative to importing assignments into Google Tasks, the main_no_api.py can parse the assignments into a simple text file. This might be useful if you prefer to manage your tasks manually or with a different tool.

Just like the Google Tasks version, this script will ask you for the .ics file URL, start date, whether to include Zoom events, and whether to sort tasks by class code or chronologically. The parsed assignments will be saved in a file named 'assignments.txt' in the same directory.


