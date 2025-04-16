"""
Tests for parsing the German format.
"""

import unittest
from datetime import datetime, date, time
from src.parser import parse_shifts, parse_line_with_date, parse_line_without_date


class TestParser(unittest.TestCase):
    """Test case for parsing German format shift plans."""
    
    def test_parse_line_with_german_date(self):
        """Test parsing a line with German day abbreviation and date."""
        line = "Mi. 30.04 17:00 01:00 Evening Shift"
        shift_data = parse_line_with_date(line)
        
        self.assertIsNotNone(shift_data)
        self.assertEqual(shift_data["start_time"], time(17, 0))
        self.assertEqual(shift_data["end_time"], time(1, 0))
        self.assertEqual(shift_data["date"].day, 30)
        self.assertEqual(shift_data["date"].month, 4)
        self.assertTrue(shift_data["midnight_shift"])
        self.assertEqual(shift_data["description"], "Evening Shift")
    
    def test_parse_line_without_date(self):
        """Test parsing a line without date information."""
        line = "18:00 02:00 Night Shift *"
        current_date = date(2023, 4, 30)
        shift = parse_line_without_date(line, current_date)
        
        self.assertIsNotNone(shift)
        self.assertEqual(shift.start_time, time(18, 0))
        self.assertEqual(shift.end_time, time(2, 0))
        self.assertEqual(shift.date, current_date)
        self.assertTrue(shift.spans_midnight)
        self.assertEqual(shift.description, "Night Shift *")
    
    def test_parse_special_shifts(self):
        """Test parsing shifts marked with asterisk as special."""
        text = """
        Mi. 30.04 17:00 01:00 Regular Shift
        18:00 02:00 Special Shift *
        """
        
        shifts = parse_shifts(text)
        
        self.assertEqual(len(shifts), 2)
        self.assertFalse('*' in shifts[0].description)
        self.assertTrue('*' in shifts[1].description)
    
    def test_parse_full_german_format(self):
        """Test parsing a complete shift plan in German format."""
        text = """
        Mi. 30.04 17:00 01:00 Shift 1
        18:00 02:00 Shift 2
        
        Do. 01.05 00:00 08:00 Shift 3
        08:00 16:00 Shift 4
        """
        
        shifts = parse_shifts(text)
        
        self.assertEqual(len(shifts), 4)
        
        # Check that dates are correctly carried over
        self.assertEqual(shifts[0].date.day, 30)
        self.assertEqual(shifts[0].date.month, 4)
        self.assertEqual(shifts[1].date.day, 30)
        self.assertEqual(shifts[1].date.month, 4)
        
        self.assertEqual(shifts[2].date.day, 1)
        self.assertEqual(shifts[2].date.month, 5)
        self.assertEqual(shifts[3].date.day, 1)
        self.assertEqual(shifts[3].date.month, 5)


if __name__ == '__main__':
    unittest.main() 