"""
Nextcloud Integration for ShiftPlan to ICS Converter

This module handles integration with Nextcloud calendars.
"""

import caldav
from datetime import datetime
import uuid
from icalendar import Calendar


def sync_with_nextcloud(ics_file, settings, date_range, logger_callback=None):
    """
    Sync an ICS file with a Nextcloud calendar.
    
    Args:
        ics_file: Path to the ICS file to sync
        settings: Dictionary with Nextcloud settings (url, username, password, calendar)
        date_range: Tuple of (first_date, last_date) to clear events in that range
        logger_callback: Function to call for logging messages
    
    Returns:
        dict: Dictionary with success status and additional information
    """
    first_date, last_date = date_range
    
    if logger_callback:
        logger_callback("\nSyncing with Nextcloud calendar...")
    
    try:
        # Ensure URL ends with /remote.php/dav
        url = settings['url'].rstrip('/')
        if not url.endswith('/remote.php/dav'):
            url += '/remote.php/dav'
        
        # Connect to Nextcloud
        if logger_callback:
            logger_callback(f"Connecting to Nextcloud at {url}...")
            
        client = caldav.DAVClient(
            url=url,
            username=settings['username'],
            password=settings['password']
        )
        
        # Get principal
        principal = client.principal()
        
        # Find the target calendar
        calendars = principal.calendars()
        target_calendar = None
        for calendar in calendars:
            if calendar.name == settings['calendar']:
                target_calendar = calendar
                break
        
        if not target_calendar:
            available_calendars = [cal.name for cal in calendars]
            if logger_callback:
                logger_callback(f"Error: Calendar '{settings['calendar']}' not found. Available calendars: {available_calendars}")
            return {
                'success': False,
                'error': f"Calendar '{settings['calendar']}' not found. Available calendars: {available_calendars}"
            }
        
        # Calculate search range (from first date to last date)
        if not first_date or not last_date:
            if logger_callback:
                logger_callback("Error: Date range not available")
            return {
                'success': False,
                'error': "Date range not available"
            }
        
        # Adjust the range to include the whole day
        start_date = datetime.combine(first_date, datetime.min.time())
        end_date = datetime.combine(last_date, datetime.max.time())
        
        # Find existing events in the date range
        if logger_callback:
            logger_callback(f"Searching for existing events from {start_date.date()} to {end_date.date()}...")
            
        events = target_calendar.date_search(
            start=start_date,
            end=end_date
        )
        
        # Delete all events in the range
        if events:
            if logger_callback:
                logger_callback(f"Found {len(events)} existing events to delete...")
                
            for event in events:
                event.delete()
                
            if logger_callback:
                logger_callback("All existing events deleted.")
        else:
            if logger_callback:
                logger_callback("No existing events found in this date range.")
        
        # Read the ICS file
        with open(ics_file, 'r') as f:
            ics_content = f.read()
        
        # Upload events individually
        if logger_callback:
            logger_callback("Parsing ICS file and adding individual events...")
        
        try:
            # Parse the ICS file into individual events
            cal = Calendar.from_ical(ics_content)
            
            events_added = 0
            
            # Add each event individually
            for component in cal.walk('VEVENT'):
                event_data = component.to_ical().decode('utf-8')
                try:
                    target_calendar.add_event(event_data)
                    events_added += 1
                except Exception as e_inner:
                    if logger_callback:
                        logger_callback(f"Warning: Could not add individual event: {str(e_inner)}")
            
            if events_added > 0:
                if logger_callback:
                    logger_callback(f"Successfully added {events_added} individual events")
                
                return {
                    'success': True,
                    'calendar': settings['calendar'],
                    'date_range': (start_date.date(), end_date.date()),
                    'events_added': events_added
                }
            else:
                raise Exception("Could not add any individual events")
                
        except Exception as e:
            detailed_error = (f"Error adding events to Nextcloud calendar: {str(e)}\n\n"
                             f"Please check:\n"
                             f"1. Your Nextcloud URL is correct and ends with /remote.php/dav\n"
                             f"2. Your username and password are correct\n"
                             f"3. The calendar name exists and is accessible\n"
                             f"4. Your Nextcloud server accepts ICS file imports\n"
                             f"5. The ICS file is properly formatted")
            
            if logger_callback:
                logger_callback(detailed_error)
            
            return {
                'success': False,
                'error': detailed_error
            }
        
    except Exception as e:
        error_message = str(e)
        if logger_callback:
            logger_callback(f"Error syncing with Nextcloud: {error_message}")
        
        return {
            'success': False,
            'error': error_message
        } 