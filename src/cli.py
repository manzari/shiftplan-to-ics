"""
Command-Line Interface for ShiftPlan to ICS Converter

This module provides command-line interface functionality.
"""

import os
import sys
import argparse

from src.parser import parse_shifts
from src.ics_generator import generate_ics
from src.main import get_text_from_file
from src.nextcloud_integration import sync_with_nextcloud
from src.config import get_nextcloud_settings, get_output_dir


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert ShiftPlan text files to ICS calendar format."
    )
    
    # Input files
    parser.add_argument(
        "input_files",
        nargs="+",
        help="Input files to process (text or image)"
    )
    
    # Output directory
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory (default: from config)",
        default=get_output_dir()
    )
    
    # Reminders
    parser.add_argument(
        "-r", "--reminders",
        nargs="+",
        help="Add reminders for these shift names (space-separated)",
        default=[]
    )
    
    # Filter by name
    parser.add_argument(
        "-i", "--include",
        nargs="+",
        help="Only include shifts with these names (space-separated)",
        default=[]
    )
    
    parser.add_argument(
        "-e", "--exclude",
        nargs="+",
        help="Exclude shifts with these names (space-separated)",
        default=[]
    )
    
    # Special shifts
    parser.add_argument(
        "-s", "--special",
        action="store_true",
        help="Include special shifts (*) when filtering"
    )
    
    # Nextcloud replace
    parser.add_argument(
        "--nextcloud-replace",
        action="store_true",
        help="Upload to Nextcloud calendar after creating ICS file"
    )
    
    # Verbose output
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    
    return parser.parse_args()


def validate_nextcloud_settings():
    """Validate Nextcloud settings from config.
    
    Returns:
        tuple: (settings, error) where settings is a dict with Nextcloud settings and
               error is None if valid, or an error message if invalid.
    """
    settings = get_nextcloud_settings()
    
    # Check if all required fields are filled
    if not all([
        settings.get('url'),
        settings.get('username'),
        settings.get('password'),
        settings.get('calendar')
    ]):
        return settings, "Nextcloud settings are incomplete. Use the GUI to set them up first."
    
    return settings, None


def process_files(args):
    """Process input files and generate ICS file.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        tuple: (output_file, shifts, first_date, last_date) or None if error.
    """
    all_shifts = []
    
    # Process each input file
    for input_file in args.input_files:
        if not os.path.exists(input_file):
            print(f"Error: Input file not found: {input_file}")
            return None
        
        try:
            # Extract text from file
            text = get_text_from_file(input_file)
            
            # Parse shifts
            shifts = parse_shifts(text)
            
            if not shifts:
                print(f"Warning: No shifts were parsed from file {input_file}")
                continue
            
            if args.verbose:
                print(f"Found {len(shifts)} shifts in {input_file}")
            
            all_shifts.extend(shifts)
            
        except Exception as e:
            print(f"Error processing file {input_file}: {e}")
            return None
    
    if not all_shifts:
        print("Error: No shifts were parsed from the input files.")
        return None
    
    # Apply filters
    shifts_to_use = all_shifts.copy()
    
    # Include filter
    if args.include:
        include_names = set(args.include)
        filtered_shifts = []
        
        for shift in shifts_to_use:
            # Strip any trailing asterisk before checking
            shift_name = shift.description.rstrip('*').strip()
            
            # Check if it's a special shift (has an asterisk)
            is_special = '*' in shift.description
            
            # Include the shift if it matches the include filter OR if it's special and the special flag is set
            if shift_name in include_names or (is_special and args.special):
                filtered_shifts.append(shift)
        
        shifts_to_use = filtered_shifts
        
        if args.verbose:
            print(f"Applied include filter: {len(shifts_to_use)} shifts remaining")
        
        if not shifts_to_use:
            print("Error: No shifts left after applying include filter.")
            return None
    
    # Exclude filter
    if args.exclude:
        exclude_names = set(args.exclude)
        filtered_shifts = []
        
        for shift in shifts_to_use:
            shift_name = shift.description.rstrip('*').strip()
            if shift_name not in exclude_names:
                filtered_shifts.append(shift)
        
        shifts_to_use = filtered_shifts
        
        if args.verbose:
            print(f"Applied exclude filter: {len(shifts_to_use)} shifts remaining")
        
        if not shifts_to_use:
            print("Error: No shifts left after applying exclude filter.")
            return None
    
    # Sort shifts by date
    sorted_shifts = sorted(shifts_to_use, key=lambda x: x.date)
    first_date = sorted_shifts[0].date
    last_date = sorted_shifts[-1].date
    
    # Create filename
    first_date_str = first_date.strftime('%d-%m')
    last_date_str = last_date.strftime('%d-%m')
    filename = f"Shifts_{first_date_str}_{last_date_str}.ics"
    
    # Ensure output directory exists
    if not os.path.exists(args.output_dir):
        try:
            os.makedirs(args.output_dir)
            print(f"Created output directory: {args.output_dir}")
        except OSError as e:
            print(f"Error: Could not create output directory: {e}")
            return None
    
    # Generate ICS file
    output_file = os.path.join(args.output_dir, filename)
    
    try:
        # Generate ICS file
        generate_ics(shifts_to_use, output_file, args.reminders, all_shifts=all_shifts)
        print(f"Successfully created calendar file: {output_file}")
        print(f"Found and processed {len(shifts_to_use)} shifts spanning {len(set(shift.date for shift in shifts_to_use))} days")
        
        return output_file, shifts_to_use, first_date, last_date
    except Exception as e:
        print(f"Error generating ICS file: {e}")
        return None


def run_cli():
    """Run the command-line interface."""
    args = parse_arguments()
    
    result = process_files(args)
    if not result:
        sys.exit(1)
    
    output_file, shifts, first_date, last_date = result
    
    # Handle Nextcloud replace
    if args.nextcloud_replace:
        nextcloud_settings, error = validate_nextcloud_settings()
        
        if error:
            print(f"Error: {error}")
            sys.exit(1)
        
        print("\nReplacing events in Nextcloud calendar...")
        
        result = sync_with_nextcloud(
            output_file,
            nextcloud_settings,
            (first_date, last_date),
            print  # Use print as the logger callback
        )
        
        if result.get('success'):
            print(f"Successfully replaced events in Nextcloud calendar '{result['calendar']}'")
            print(f"Date range: {result['date_range'][0]} to {result['date_range'][1]}")
        else:
            print(f"Error syncing with Nextcloud: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    run_cli() 