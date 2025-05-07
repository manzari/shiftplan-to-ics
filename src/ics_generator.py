"""
Generate ICS (iCalendar) files from shift data.

This module provides functions to create ICS calendar files from Shift objects.
"""

import os
from typing import List
from datetime import datetime, timedelta
import pytz
from icalendar import Calendar, Event, Alarm
from src.parser import Shift

# Default timezone for events
DEFAULT_TIMEZONE = pytz.timezone('Europe/Berlin')

def generate_ics(shifts: List[Shift], output_file: str, reminder_names: List[str] = None, all_shifts: List[Shift] = None) -> str:
    """
    Generate an ICS file from a list of shifts.
    
    Args:
        shifts: List of Shift objects to include in the calendar
        output_file: Path to the output file
        reminder_names: Optional list of names to add reminders for (default: None)
        all_shifts: Optional list of all shifts for overlap detection (default: None, will use shifts parameter)
        
    Returns:
        Path to the generated ICS file
    """
    # Create a calendar
    cal = Calendar()
    
    # Set calendar properties
    cal.add('prodid', '-//ShiftPlan to ICS Converter//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-timezone', 'Europe/Berlin')
    
    shifts_for_overlap = all_shifts if all_shifts is not None else shifts
    
    # Add each shift as an event
    for shift in shifts:
        # Pass all shifts to create_event for overlap checking
        event = create_event(shift, reminder_names, shifts_for_overlap)
        cal.add_component(event)
    
    # Write to file
    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())
    
    return output_file


def create_event(shift: Shift, reminder_names: List[str] = None, all_shifts: List[Shift] = None) -> Event:
    """
    Create an iCalendar Event from a Shift.
    
    Args:
        shift: Shift object
        reminder_names: Optional list of names to add reminders for (default: None)
        all_shifts: Optional list of all shifts for overlap detection (default: None)
        
    Returns:
        iCalendar Event
    """
    event = Event()
    
    # Strip any trailing asterisk from description (often used to mark special shifts)
    description = shift.description.rstrip('*').strip()
    is_special = '*' in shift.description  # Check if it was marked as special
    
    # Basic event properties - changed to remove prefixes and add asterisk directly to name
    if is_special:
        event.add('summary', f"{description}*")
    else:
        event.add('summary', description)
    
    # Apply timezone to the start and end times
    start_dt = DEFAULT_TIMEZONE.localize(shift.start_datetime)
    end_dt = DEFAULT_TIMEZONE.localize(shift.end_datetime)
    
    # Add date-time information with timezone
    event.add('dtstart', start_dt)
    event.add('dtend', end_dt)
    
    # Use current time as creation time (also with timezone)
    now = DEFAULT_TIMEZONE.localize(datetime.now())
    event.add('dtstamp', now)
    event.add('created', now)
    
    # Generate a UID based on start time and description
    uid = f"{shift.start_datetime.strftime('%Y%m%dT%H%M%S')}-{hash(shift.description) & 0xffffffff}@shiftplan-to-ics"
    event.add('uid', uid)
    
    # Add description with overlapping shifts for all shifts (including special shifts)
    if all_shifts:
        overlapping_shifts = find_overlapping_shifts(shift, all_shifts)
        if overlapping_shifts:
            overlap_desc = []
            for overlap in overlapping_shifts:
                start_str = overlap.start_time.strftime('%H:%M')
                end_str = overlap.end_time.strftime('%H:%M')
                overlap_desc.append(f"{start_str} {end_str} {overlap.description}")
            
            event.add('description', '\n'.join(overlap_desc))
    
    # Add typical work shift properties
    categories = ['WORK']
    if is_special:
        categories.append('SPECIAL')
    event.add('categories', categories)
    
    # Add reminder only if the person is in the reminder_names list
    if reminder_names and description in reminder_names:
        # Create an Alarm component
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Reminder: Work shift starting in 1 hour')
        alarm.add('trigger', timedelta(hours=-1))
        
        # Add the alarm as a subcomponent to the event
        event.add_component(alarm)
    
    return event


def find_overlapping_shifts(current_shift: Shift, all_shifts: List[Shift]) -> List[Shift]:
    """
    Find shifts that overlap with the current shift.
    
    Args:
        current_shift: The shift to check for overlaps
        all_shifts: List of all shifts to check against
        
    Returns:
        List of shifts that overlap with the current shift
    """
    overlapping = []
    
    # Get the start and end datetimes of the current shift
    current_start = current_shift.start_datetime
    current_end = current_shift.end_datetime
    
    for other in all_shifts:
        # Skip the current shift itself
        if other is current_shift:
            continue
        
        # Get the start and end datetimes of the other shift
        other_start = other.start_datetime
        other_end = other.end_datetime
        
        # Check if the shifts overlap
        # Two shifts overlap if one starts before the other ends and ends after the other starts
        if (other_start < current_end and other_end > current_start):
            overlapping.append(other)
    
    return overlapping


def merge_ics_files(input_files: List[str], output_file: str) -> str:
    """
    Merge multiple ICS files into one.
    
    Args:
        input_files: List of paths to input ICS files
        output_file: Path to the output file
        
    Returns:
        Path to the merged ICS file
    """
    merged_cal = Calendar()
    merged_cal.add('prodid', '-//ShiftPlan to ICS Converter//EN')
    merged_cal.add('version', '2.0')
    merged_cal.add('calscale', 'GREGORIAN')
    merged_cal.add('method', 'PUBLISH')
    
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist. Skipping.")
            continue
            
        with open(file_path, 'rb') as f:
            cal = Calendar.from_ical(f.read())
            
            # Add all events from this calendar
            for component in cal.walk():
                if component.name == 'VEVENT':
                    merged_cal.add_component(component)
    
    # Write to file
    with open(output_file, 'wb') as f:
        f.write(merged_cal.to_ical())
    
    return output_file 