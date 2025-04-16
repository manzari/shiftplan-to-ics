"""
Tests for the main script functionality.
"""

import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch
from pathlib import Path
from src.main import main
from src.parser import parse_shifts


class TestMainFunctionality(unittest.TestCase):
    """Test case for the main script functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a sample input file
        self.sample_content = """
        # Sample shift plan
        Mi. 30.04 17:00 01:00 Thomas
        18:00 02:00 Julia *
        
        Do. 01.05 08:00 16:00 Thomas
        16:00 00:00 Sarah
        
        Fr. 02.05 09:00 17:00 Julia
        """
        
        # Create temporary files for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_file = Path(self.temp_dir.name) / "sample_input.txt"
        self.output_file = Path(self.temp_dir.name) / "output.ics"
        
        # Write sample content to the input file
        with open(self.input_file, 'w') as f:
            f.write(self.sample_content)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_include_functionality(self):
        """Test including shifts by name."""
        # Parse the sample content to verify our test data
        shifts = parse_shifts(self.sample_content)
        all_shifts_count = len(shifts)
        
        thomas_shifts = [s for s in shifts if s.description.rstrip('*').strip() == "Thomas"]
        julia_shifts = [s for s in shifts if s.description.rstrip('*').strip() == "Julia"]
        
        self.assertEqual(len(thomas_shifts), 2, "Should find 2 shifts for Thomas")
        self.assertEqual(len(julia_shifts), 2, "Should find 2 shifts for Julia")
        
        # Test including for Thomas
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-i', 'Thomas', '-v']):
            # Capture stdout to verify output
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that inclusion was applied
            self.assertIn("Including shifts for: Thomas", output)
            self.assertIn("Found 2 shifts", output)
            self.assertNotIn("Sarah", output)
            self.assertNotIn("Julia", output)
    
    def test_include_multiple_names(self):
        """Test including shifts by multiple names."""
        # Test including for Thomas and Julia
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-i', 'Thomas,Julia', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that inclusion was applied for both names
            self.assertIn("Including shifts for: Thomas, Julia", output)
            self.assertIn("Found 4 shifts", output)
            self.assertNotIn("Sarah", output)
    
    def test_include_nonexistent_name(self):
        """Test including with a name that doesn't exist in the shifts."""
        # Test including for a non-existent name
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-i', 'NonExistentPerson', '-v']):
            with patch('sys.stdout', new=StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    main()
                
                # Check that the program exits with an error code
                self.assertEqual(cm.exception.code, 1)
    
    def test_exclude_functionality(self):
        """Test excluding shifts by name."""
        # Test excluding Thomas
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-e', 'Thomas', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that exclusion was applied
            self.assertIn("Excluding shifts for: Thomas", output)
            self.assertIn("Found 3 shifts", output)  # Julia (2) + Sarah (1)
            self.assertNotIn("Thomas", output)
    
    def test_exclude_multiple_names(self):
        """Test excluding shifts by multiple names."""
        # Test excluding Thomas and Julia
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-e', 'Thomas,Julia', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that exclusion was applied for both names
            self.assertIn("Excluding shifts for: Thomas, Julia", output)
            self.assertIn("Found 1 shift", output)  # Only Sarah
            self.assertIn("Sarah", output)
    
    def test_exclude_all_names(self):
        """Test excluding all names in the shifts."""
        # Test excluding all names
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-e', 'Thomas,Julia,Sarah', '-v']):
            with patch('sys.stdout', new=StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    main()
                
                # Check that the program exits with an error code
                self.assertEqual(cm.exception.code, 1)
    
    def test_include_and_exclude(self):
        """Test combining include and exclude options."""
        # Include Thomas and Julia but exclude Thomas
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), 
                               '-i', 'Thomas,Julia', '-e', 'Thomas', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that both inclusion and exclusion were applied
            self.assertIn("Including shifts for: Thomas, Julia", output)
            self.assertIn("Excluding shifts for: Thomas", output)
            self.assertIn("Found 2 shifts", output)  # Only Julia's shifts
            self.assertIn("Julia", output)
            self.assertNotIn("Thomas", output)
    
    def test_reminder_functionality(self):
        """Test adding reminders for specific people."""
        # Test with reminders for Thomas
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), '-r', 'Thomas', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that reminders are being added only for Thomas
            self.assertIn("Adding reminders only for: Thomas", output)
            self.assertIn("Successfully created calendar file", output)
    
    def test_combined_include_and_reminder(self):
        """Test including shifts and adding reminders together."""
        # Test including for Julia with reminders
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), 
                               '-i', 'Julia', '-r', 'Julia', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that both inclusion and reminders are applied
            self.assertIn("Including shifts for: Julia", output)
            self.assertIn("Adding reminders only for: Julia", output)
            self.assertIn("Found 2 shifts", output)
    
    def test_special_shift_with_include(self):
        """Test the --add-special-shift option with --include."""
        # Test including Thomas but also special shifts (Julia has a special shift marked with *)
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), 
                               '-i', 'Thomas', '-s', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that we get Thomas's shifts and Julia's special shift
            self.assertIn("Including shifts for: Thomas", output)
            self.assertIn("Found 3 shifts", output)  # 2 Thomas + 1 special Julia
            self.assertIn("Thomas", output)
            self.assertIn("Julia *", output)
    
    def test_special_shift_with_exclude(self):
        """Test the --add-special-shift option with --exclude."""
        # Exclude Thomas but keep all special shifts
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), 
                               '-e', 'Thomas', '-s', '-v']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                main()
            
            output = captured_output.getvalue()
            
            # Check that Thomas is excluded but all shifts remain (special flag doesn't affect exclude)
            self.assertIn("Excluding shifts for: Thomas", output)
            self.assertIn("Found 3 shifts", output)  # Sarah + 2 Julia (including special)
            self.assertNotIn("Thomas", output)
            self.assertIn("Julia", output)
            self.assertIn("Sarah", output)
    
    def test_dry_run_functionality(self):
        """Test the --dry-run option."""
        # Test dry run with verbose output
        with patch('sys.argv', ['src.main', str(self.input_file), str(self.output_file), 
                               '-i', 'Thomas', '-v', '--dry-run']):
            captured_output = StringIO()
            with patch('sys.stdout', new=captured_output):
                # Should not raise an exception but exit with sys.exit(0)
                with self.assertRaises(SystemExit) as cm:
                    main()
                
                # Check that the program exits with success code (not an error)
                self.assertEqual(cm.exception.code, 0)
            
            output = captured_output.getvalue()
            
            # Check that dry run output contains expected content
            self.assertIn("Shifts to include (2):", output)
            self.assertIn("Shifts excluded by filters", output)
            self.assertIn("[EXCLUDED]", output)
            self.assertIn("Dry run complete", output)
            self.assertIn("No ICS file was created", output)
            
            # Should mention Thomas but not create a file for him
            self.assertIn("Thomas", output)
            self.assertNotIn("Successfully created calendar file", output)


if __name__ == '__main__':
    unittest.main() 