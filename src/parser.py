"""
Parse shift information from text.

This module contains functions to extract dates, times, and shift information
from text input in German format.
"""

import re
import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Any, Optional, Tuple


def is_valid_shift_name(name: str) -> bool:
    """
    Validate that a shift name does not contain numbers or colons.
    
    Args:
        name: The shift name to validate
        
    Returns:
        True if the name is valid, False otherwise
    """
    return not any(char.isdigit() or char == ':' for char in name)


class Shift:
    """Represents a work shift with start and end times."""
    
    def __init__(self, date: datetime.date, start_time: datetime.time, 
                 end_time: datetime.time, description: str = "", spans_midnight: bool = False):
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        self.spans_midnight = spans_midnight
        
    def __repr__(self) -> str:
        midnight_info = " (spans midnight)" if self.spans_midnight else ""
        return (f"Shift({self.date}, {self.start_time} - {self.end_time}{midnight_info}, "
                f"'{self.description}')")
    
    @property
    def start_datetime(self) -> datetime.datetime:
        """Get the start datetime by combining date and start time."""
        return datetime.datetime.combine(self.date, self.start_time)
    
    @property
    def end_datetime(self) -> datetime.datetime:
        """Get the end datetime by combining date and end time."""
        if self.spans_midnight:
            # If the shift spans midnight, the end date is the next day
            next_day = self.date + datetime.timedelta(days=1)
            return datetime.datetime.combine(next_day, self.end_time)
        return datetime.datetime.combine(self.date, self.end_time)


def parse_shifts(text: str) -> List[Shift]:
    """
    Parse shift information from text.
    
    Args:
        text: The text containing shift information
        
    Returns:
        A list of Shift objects
    """
    shifts = []
    
    # Split text into lines and process each line
    lines = text.strip().split('\n')
    current_date = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Try to parse as a line with date
        shift_data = parse_line_with_date(line)
        
        if shift_data:
            current_date = shift_data["date"]
            shifts.append(Shift(
                current_date, 
                shift_data["start_time"], 
                shift_data["end_time"], 
                shift_data["description"], 
                shift_data["midnight_shift"]
            ))
        elif current_date:
            # If no date in line, use the current date
            shift = parse_line_without_date(line, current_date)
            if shift:
                shifts.append(shift)
    
    return shifts


def clean_text(text: str) -> str:
    """
    Clean up text by removing extra spaces and other unwanted characters.
    Only allows A-z, 0-9, and the special characters *:.
    """
    if not text:
        return ""
    
    # Filter out all characters that are not A-z, 0-9, *, :, . or space
    text = re.sub(r'[^A-Za-z0-9*:.\s]', '', text)
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_line_with_date(line: str, default_date: Optional[datetime.date] = None) -> Optional[dict]:
    """
    Parse a line of text with a date.
    Handles various formats of day abbreviations and focuses on extracting 
    the day number, month number, times, and description.
    
    Examples:
     Mi. 30.04 17:00 01:00 Description
     i. 30.04 17:00 01:00 Description
     . 30.04 17:00 01:00 Description
     DF30.04 17:00 01:00 Description
     M 30.04 17:00 01:00 Description
    """
    line = clean_text(line)
    
    # More flexible pattern that focuses on the day/month numbers, times, and description
    # Match anything before the date numbers, as long as the date format is correct
    match = re.match(r'.*?(\d{1,2})[.\-/](\d{1,2})(?:[.\-/](\d{2,4}))?\s+(\d{1,2}(?:[:.]\d{1,2})?)\s+(\d{1,2}(?:[:.]\d{1,2})?)\s+(.*)', line)
    if match:
        return extract_shift_from_match_with_date(match)
    
    return None


def parse_line_without_date(line: str, current_date: datetime.date) -> Optional[Shift]:
    """Parse a line that doesn't include date information."""
    # Clean the line
    cleaned_line = clean_text(line)
    
    # Standard pattern for shift without date
    pattern = r'(?P<start_time>[\d:]+)\s+(?P<end_time>[\d:]+)(?:\s+(?P<description>.+))?'
    
    match = re.search(pattern, cleaned_line)
    if match:
        try:
            description = match.group('description') if 'description' in match.groupdict() and match.group('description') else ""
            
            # Validate shift name
            if description and not is_valid_shift_name(description):
                print(f"Warning: Invalid shift name '{description}' contains numbers or colons. Skipping.")
                return None
            
            # Handle asterisk - make sure it's directly after the name without space
            if description.endswith('*'):
                description = description.rstrip('* ').strip() + '*'
            elif '*' in description:
                # If asterisk is in the middle, normalize it
                base_name = description.replace('*', '').strip()
                description = base_name + '*'
            
            # Parse times
            start_time = parse_time(match.group('start_time'))
            end_time = parse_time(match.group('end_time'))
            
            if not start_time or not end_time:
                return None
            
            # Check if the shift spans midnight
            spans_midnight = end_time < start_time
            
            return Shift(current_date, start_time, end_time, description, spans_midnight)
        except Exception as e:
            print(f"Error parsing shift without date: {e}")
    
    return None


def extract_shift_from_match_with_date(match) -> Optional[dict]:
    """
    Extract shift information from a regex match with date.
    Always uses the current year regardless of any year specified in input.
    """
    day, month, _ = match.group(1), match.group(2), match.group(3)
    start_time_str, end_time_str = match.group(4), match.group(5)
    description = match.group(6)
    
    # Validate shift name
    if not is_valid_shift_name(description):
        print(f"Warning: Invalid shift name '{description}' contains numbers or colons. Skipping.")
        return None
    
    # Handle asterisk - make sure it's directly after the name without space
    if description.endswith('*'):
        description = description.rstrip('* ').strip() + '*'
    elif '*' in description:
        # If asterisk is in the middle, normalize it
        base_name = description.replace('*', '').strip()
        description = base_name + '*'
    
    # Convert to integers
    try:
        day = int(day)
        month = int(month)
        
        # Always use current year
        current_year = datetime.datetime.now().year
        year = current_year
        
        # Create date object
        try:
            date = datetime.date(year, month, day)
        except ValueError:
            # Handle invalid dates
            return None
        
        start_time = parse_time(start_time_str)
        end_time = parse_time(end_time_str)
        
        if start_time and end_time:
            # Check if shift spans midnight
            midnight_shift = False
            if end_time < start_time:
                midnight_shift = True
            
            return {
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "midnight_shift": midnight_shift
            }
    except:
        pass
    
    return None


def parse_time(time_str: str) -> Optional[datetime.time]:
    """
    Parse time string to datetime.time object.
    """
    if not time_str:
        return None
    
    # Clean the time string
    time_str = clean_text(time_str)
    
    # Handle simple hour format (e.g. "9" or "14")
    if re.match(r'^\d{1,2}$', time_str):
        hour = int(time_str)
        if 0 <= hour <= 23:
            return datetime.time(hour, 0)
    
    # Handle standard time format (e.g. "9:30" or "14:45")
    match = re.match(r'^(\d{1,2})[:\.]?(\d{2})$', time_str)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return datetime.time(hour, minute)
    
    # As a last resort, try using dateutil
    try:
        from dateutil import parser as date_parser
        parsed_time = date_parser.parse(time_str)
        return parsed_time.time()
    except:
        pass
    
    return None 