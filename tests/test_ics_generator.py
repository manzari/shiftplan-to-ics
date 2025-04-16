"""
Tests for the ICS generator functionality.
"""

import unittest
import tempfile
import os
from datetime import date, time, datetime, timedelta
from icalendar import Calendar
from src.parser import Shift
from src.ics_generator import generate_ics, create_event, find_overlapping_shifts


class TestIcsGenerator(unittest.TestCase):
    """Test case for ICS calendar file generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test shifts with names that exactly match what would be in reminder_names
        # Note that the reminder comparison is done with shift.description.rstrip('*').strip()
        self.shifts = [
            Shift(date(2023, 4, 30), time(17, 0), time(1, 0), "Thomas", spans_midnight=True),
            Shift(date(2023, 4, 30), time(18, 0), time(2, 0), "Julia", spans_midnight=True),
            Shift(date(2023, 5, 1), time(8, 0), time(16, 0), "Thomas", spans_midnight=False),
            Shift(date(2023, 5, 1), time(16, 0), time(0, 0), "Sarah", spans_midnight=True),
            # Special shift with asterisk - the asterisk will be stripped for comparison
            Shift(date(2023, 5, 2), time(9, 0), time(17, 0), "Julia *", spans_midnight=False),
        ]
    
    def test_create_event_with_reminder(self):
        """Test creating an event with a reminder for specific people."""
        # Test with reminder for Thomas
        shift = self.shifts[0]  # Thomas's shift
        event = create_event(shift, reminder_names=["Thomas"])
        
        # Check if the event has a VALARM component (reminder)
        alarms = event.walk('VALARM')
        self.assertEqual(len(alarms), 1, "Event should have one alarm (reminder)")
        
        # Verify reminder details
        alarm = alarms[0]
        self.assertEqual(alarm['ACTION'], 'DISPLAY')
        self.assertEqual(alarm['DESCRIPTION'], 'Reminder: Work shift starting in 1 hour')
        
        # The TRIGGER will be a vDDDTypes object from the icalendar library
        # We just check that it's present without comparing the exact value
        self.assertTrue('TRIGGER' in alarm, "Alarm should have a TRIGGER property")
        
        # Test with a shift not in the reminder list
        shift = self.shifts[1]  # Julia's shift
        event = create_event(shift, reminder_names=["Thomas"])
        
        # Check that no reminder was added
        alarms = event.walk('VALARM')
        self.assertEqual(len(alarms), 0, "Event should not have any alarms")
    
    def test_create_event_with_multiple_reminders(self):
        """Test creating events with reminders for multiple people."""
        # Set reminders for both Thomas and Julia
        reminder_names = ["Thomas", "Julia"]
        
        # Test Thomas's shift
        thomas_event = create_event(self.shifts[0], reminder_names)
        thomas_alarms = thomas_event.walk('VALARM')
        self.assertEqual(len(thomas_alarms), 1, "Thomas's event should have a reminder")
        
        # Test Julia's shift
        julia_event = create_event(self.shifts[1], reminder_names)
        julia_alarms = julia_event.walk('VALARM')
        self.assertEqual(len(julia_alarms), 1, "Julia's event should have a reminder")
        
        # Test Julia's special shift (with asterisk)
        # The asterisk should be stripped off before comparison
        julia_special_event = create_event(self.shifts[4], reminder_names)
        julia_special_alarms = julia_special_event.walk('VALARM')
        self.assertEqual(len(julia_special_alarms), 1, 
                        "Julia's special event (with asterisk) should have a reminder")
        
        # Test Sarah's shift (should not have a reminder)
        sarah_event = create_event(self.shifts[3], reminder_names)
        sarah_alarms = sarah_event.walk('VALARM')
        self.assertEqual(len(sarah_alarms), 0, "Sarah's event should not have a reminder")
    
    def test_event_summary_format(self):
        """Test the new event summary format with and without asterisks."""
        # Regular shift (Thomas)
        regular_event = create_event(self.shifts[0])
        self.assertEqual(regular_event['SUMMARY'], "Thomas", 
                         "Regular event summary should be just the name")
        
        # Special shift (Julia*)
        special_event = create_event(self.shifts[4])
        self.assertEqual(special_event['SUMMARY'], "Julia*", 
                         "Special event summary should be name with asterisk")
    
    def test_overlap_detection(self):
        """Test detecting overlapping shifts."""
        # Thomas's shift overlaps with Julia's
        overlaps = find_overlapping_shifts(self.shifts[0], self.shifts)
        self.assertEqual(len(overlaps), 1, "Thomas's shift should overlap with Julia's shift")
        self.assertEqual(overlaps[0].description, "Julia", "The overlapping shift should be Julia's")
        
        # Test with more overlapping shifts
        overlapping_shifts = [
            Shift(date(2023, 4, 30), time(16, 0), time(20, 0), "Alice"),  # Overlaps with Thomas
            Shift(date(2023, 4, 30), time(19, 0), time(23, 0), "Bob"),    # Overlaps with Julia
            Shift(date(2023, 4, 30), time(22, 0), time(6, 0), "Charlie", spans_midnight=True), # Overlaps with both
            Shift(date(2023, 5, 1), time(10, 0), time(12, 0), "Dave"),    # Doesn't overlap with any
        ]
        
        all_shifts = self.shifts + overlapping_shifts
        
        # Check Thomas's overlaps
        thomas_overlaps = find_overlapping_shifts(self.shifts[0], all_shifts)
        self.assertEqual(len(thomas_overlaps), 4, 
                         "Thomas's shift should overlap with Julia, Alice, Bob, and Charlie")
        
        # Check that descriptions get added for overlapping shifts
        thomas_event = create_event(self.shifts[0], all_shifts=all_shifts)
        self.assertTrue('DESCRIPTION' in thomas_event, 
                        "Event should have a description with overlapping shifts")
        desc = str(thomas_event['DESCRIPTION'])
        self.assertIn("Julia", desc, "Description should include Julia's shift")
        self.assertIn("Alice", desc, "Description should include Alice's shift")
        self.assertIn("Charlie", desc, "Description should include Charlie's shift")
    
    def test_special_shift_with_overlaps(self):
        """Test that special shifts also get descriptions with overlapping shift information."""
        # Create an additional special shift that overlaps with others
        special_shift = Shift(date(2023, 4, 30), time(19, 30), time(23, 30), "Max *", spans_midnight=True)
        
        # Create some overlapping shifts
        overlapping_shifts = [
            Shift(date(2023, 4, 30), time(18, 0), time(22, 0), "Alice"),  # Overlaps with Max
            Shift(date(2023, 4, 30), time(23, 0), time(3, 0), "Bob", spans_midnight=True),  # Overlaps with Max
        ]
        
        all_shifts = [special_shift] + overlapping_shifts
        
        # Create event for the special shift with overlapping shifts
        event = create_event(special_shift, all_shifts=all_shifts)
        
        # Check that the description includes overlapping shifts
        self.assertTrue('DESCRIPTION' in event, 
                        "Special shift should have a description with overlapping shifts")
        desc = str(event['DESCRIPTION'])
        self.assertIn("Alice", desc, "Description should include Alice's shift")
        self.assertIn("Bob", desc, "Description should include Bob's shift")
        
        # Check that the summary still has the asterisk
        self.assertEqual(event['SUMMARY'], "Max*", 
                        "Special shift summary should still have the asterisk")
    
    def test_generate_ics_with_reminders(self):
        """Test generating an ICS file with reminders for specific people."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.ics', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Generate ICS file with reminders for Thomas
            output_file = generate_ics(self.shifts, tmp_path, reminder_names=["Thomas"])
            
            # Read back the ICS file
            with open(output_file, 'rb') as f:
                cal = Calendar.from_ical(f.read())
            
            # Count events with reminders
            thomas_events_with_reminders = 0
            other_events_with_reminders = 0
            total_events = 0
            
            for component in cal.walk('VEVENT'):
                total_events += 1
                has_alarm = len(component.walk('VALARM')) > 0
                summary = str(component.get('summary', ''))
                
                # Check if this is a Thomas event by checking the summary
                # The summary format is now just "Thomas"
                if summary == "Thomas":
                    self.assertTrue(has_alarm, f"Event for Thomas should have a reminder: {summary}")
                    thomas_events_with_reminders += 1
                else:
                    self.assertFalse(has_alarm, f"Event not for Thomas should not have a reminder: {summary}")
                    if has_alarm:
                        other_events_with_reminders += 1
            
            # Verify we found the expected number of events
            self.assertEqual(thomas_events_with_reminders, 2, 
                           "Should have 2 events with reminders (for Thomas)")
            self.assertEqual(other_events_with_reminders, 0, 
                           "Events for other people should not have reminders")
            self.assertEqual(total_events, 5, "Should have 5 total events")
            
        finally:
            # Clean up the temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_special_shifts_with_reminders(self):
        """Test that special shifts (with asterisk) still get reminders properly."""
        # Create a special shift with asterisk
        special_shift = Shift(date(2023, 5, 2), time(9, 0), time(17, 0), "Thomas *", spans_midnight=False)
        
        # The asterisk should be stripped for reminder comparison
        event = create_event(special_shift, reminder_names=["Thomas"])
        
        # Verify a reminder was added
        alarms = event.walk('VALARM')
        self.assertEqual(len(alarms), 1, 
                        "Special shift (with asterisk) for Thomas should have a reminder")
        
        # Check that the summary has the asterisk
        self.assertEqual(event['SUMMARY'], "Thomas*", 
                        "Special shift summary should be 'Thomas*'")
    
    def test_create_event_without_reminders(self):
        """Test creating events with no reminders (default behavior)."""
        # No reminder names provided
        for shift in self.shifts:
            event = create_event(shift)
            alarms = event.walk('VALARM')
            self.assertEqual(len(alarms), 0, f"Event for {shift.description} should not have a reminder by default")
        
        # Empty reminder list
        for shift in self.shifts:
            event = create_event(shift, reminder_names=[])
            alarms = event.walk('VALARM')
            self.assertEqual(len(alarms), 0, f"Event for {shift.description} should not have a reminder with empty list")


if __name__ == '__main__':
    unittest.main() 