import requests
from icalendar import Calendar, Event
from datetime import datetime as dt, timezone, date
import re
from collections import defaultdict

def parse_ics(file_url, start_date=None, include_zoom=True, sort_by_class_code=False, sort_chronologically=False):
    response = requests.get(file_url)
    cal = Calendar.from_ical(response.content)
        
    assignments = defaultdict(list)
    class_code_pattern = re.compile(r'\b[A-Za-z]{3}\d{4}\b')
    
    for component in cal.walk():
        if component.name == "VEVENT":
            location = component.get('location', '').lower()
            description = component.get('description', '').lower()
            if not include_zoom and ('zoom' in location or 'zoom' in description):
                continue
            
            class_code_match = class_code_pattern.search(component.get('summary'))
            if class_code_match:
                class_code = class_code_match.group(0)
            else:
                class_code = None
            
            start = component.get('dtstart').dt
            if isinstance(start, dt):  # if it's a datetime object, convert to naive
                start = start.astimezone(timezone.utc).replace(tzinfo=None)  
            elif isinstance(start, date):  # if it's a date object, convert to datetime
                start = dt.combine(start, dt.min.time())
            if start_date and start < start_date:
                continue
            
            summary = component.get('summary')
            summary = summary.replace('Lecture Quiz', 'LQ').replace('Chapter', 'Ch')
            
            assignment = {
                'start': start,
                'summary': summary,
                'class_code': class_code,
            }
            assignments[class_code].append(assignment)
    
    if sort_chronologically:
        for class_code in assignments:
            assignments[class_code].sort(key=lambda x: x['start'])
        
    with open('assignments.txt', 'w') as f:
        for class_code in sorted(assignments, key=lambda x: (x is None, x)) if sort_by_class_code else assignments:
            f.write(f"\nClass Code: {class_code if class_code else 'N/A'}\n")
            for assignment in assignments[class_code]:
                f.write(f"{assignment['start'].strftime('%m/%d/%y')}: {assignment['summary']}\n")

if __name__ == '__main__':
    file_url = input("Enter .ics file URL: ")
    start_date_str = input("Enter start date (MM-DD-YYYY): ")
    start_date = dt.strptime(start_date_str, "%m-%d-%Y") if start_date_str else None
    include_zoom = input("Include zoom events? (Y/N): ").lower() == 'y'
    sort_by_class_code = input("Sort by class code? (Y/N): ").lower() == 'y'
    sort_chronologically = input("Sort chronologically? (Y/N): ").lower() == 'y'
    
    parse_ics(file_url, start_date, include_zoom, sort_by_class_code, sort_chronologically)
