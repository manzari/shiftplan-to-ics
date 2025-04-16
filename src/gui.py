#!/usr/bin/env python3
"""
ShiftPlan to ICS Converter - GUI Interface

This module provides a graphical user interface for the ShiftPlan to ICS converter.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout
from datetime import datetime

from src.parser import parse_shifts
from src.ics_generator import generate_ics
from src.main import get_text_from_file
from src.widgets import MultiSelectFrame
from src.settings_dialog import SettingsDialog
from src.nextcloud_integration import sync_with_nextcloud
from src.config import (
    get_nextcloud_settings, save_nextcloud_settings,
    get_output_dir, save_output_dir,
    get_appearance_settings
)


class ShiftPlanGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ShiftPlan to ICS Converter")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)
        
        # Define color palette for pink theme
        self.pink_bg = "#FFEBEE"  # Light pink background
        self.pink_accent = "#F48FB1"  # Medium pink accent
        self.pink_dark = "#CE93D8"  # Darker pink/purple for highlights
        self.pink_text = "#880E4F"  # Dark pink for text
        
        # Define color palette for rainbow theme (unicorn puke)
        self.rainbow_bg = "#E3F2FD"  # Light blue background
        self.rainbow_accent = "#64FFDA"  # Teal/mint accent
        self.rainbow_highlight = "#FF4081"  # Bright pink highlight
        self.rainbow_text = "#7C4DFF"  # Purple text
        
        # Default system colors for default theme
        self.default_bg = self.root.cget('bg')
        self.default_fg = 'black'
        self.default_accent = '#d9d9d9'  # Standard button color in most systems
        
        # Get theme preference from config
        appearance_settings = get_appearance_settings()
        self.theme_name = appearance_settings.get('theme_name', 'pink')
        
        # Set current theme colors based on preference
        if self.theme_name == 'pink':
            self.bg_color = self.pink_bg
            self.accent_color = self.pink_accent
            self.highlight_color = self.pink_dark
            self.text_color = self.pink_text
        elif self.theme_name == 'rainbow':
            self.bg_color = self.rainbow_bg
            self.accent_color = self.rainbow_accent
            self.highlight_color = self.rainbow_highlight
            self.text_color = self.rainbow_text
        else:  # default
            self.bg_color = self.default_bg
            self.accent_color = self.default_accent
            self.highlight_color = self.default_accent
            self.text_color = self.default_fg
        
        # Create and configure custom style based on theme
        self.style = ttk.Style()
        
        if self.theme_name != 'default':
            # Configure ttk styles with the theme
            self.style.configure("TFrame", background=self.bg_color)
            self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color)
            self.style.configure("TButton", background=self.accent_color, foreground=self.text_color)
            self.style.map("TButton", 
                          background=[("active", self.highlight_color), ("pressed", self.highlight_color)],
                          foreground=[("active", self.text_color)])
            self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color)
            self.style.configure("TEntry", fieldbackground=self.bg_color)
            self.style.configure("TLabelframe", background=self.bg_color, foreground=self.text_color)
            self.style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.text_color)
            self.style.configure("TNotebook", background=self.bg_color)
            self.style.configure("TNotebook.Tab", background=self.bg_color, foreground=self.text_color)
            
            # Set root window color
            self.root.configure(bg=self.bg_color)
        
        # For storing shift data
        self.shifts = []
        self.shift_names = set()
        self.input_files = []
        
        # For storing Nextcloud credentials and last generated ICS
        nextcloud_settings = get_nextcloud_settings()
        self.nextcloud_url = nextcloud_settings.get('url', '')
        self.nextcloud_username = nextcloud_settings.get('username', '')
        self.nextcloud_password = nextcloud_settings.get('password', '')
        self.nextcloud_calendar = nextcloud_settings.get('calendar', '')
        self.last_generated_ics = None
        self.first_date = None
        self.last_date = None
        
        # Set up default output directory
        self.default_output_dir = get_output_dir()
        self.ensure_output_directory_exists()
        
        self.create_widgets()
        self.setup_layout()
        
        # Set default values
        self.output_entry.insert(0, self.default_output_dir)
        
        # Update the Nextcloud button state
        self.validate_nextcloud_credentials()
    
    def ensure_output_directory_exists(self):
        """Ensure the default output directory exists."""
        try:
            if not os.path.exists(self.default_output_dir):
                os.makedirs(self.default_output_dir)
                print(f"Created default output directory: {self.default_output_dir}")
            else:
                print(f"Using existing output directory: {self.default_output_dir}")
        except Exception as e:
            print(f"Warning: Could not create output directory: {e}")
    
    def create_widgets(self):
        # Title and description
        self.title_label = ttk.Label(self.root, text="ShiftPlan to ICS Converter", font=("Helvetica", 16))
        self.desc_label = ttk.Label(self.root, text="Convert text-based shift plans or images into ICS calendar files")
        
        # Create main container frames for two-column layout
        self.main_frame = ttk.Frame(self.root)
        self.left_frame = ttk.Frame(self.main_frame, padding=10, width=350)
        self.separator = ttk.Separator(self.main_frame, orient='vertical')
        self.right_frame = ttk.Frame(self.main_frame, padding=10)
        
        # Input file selection
        self.input_label = ttk.Label(self.left_frame, text="Input Files (Text or Image):")
        self.input_frame = ttk.Frame(self.left_frame)
        self.add_file_button = ttk.Button(self.input_frame, text="📁 Add Files", command=self.browse_input_files)
        
        # File list display with scrollbar
        self.files_frame = ttk.LabelFrame(self.left_frame, text="Selected Files")
        self.files_list = tk.Listbox(self.files_frame, width=35, height=5, 
                                    bg=self.bg_color, fg=self.text_color, 
                                    selectbackground=self.accent_color)
        self.files_scrollbar = ttk.Scrollbar(self.files_frame, orient="vertical", command=self.files_list.yview)
        self.files_list.configure(yscrollcommand=self.files_scrollbar.set)
        
        # Button to remove selected files
        self.file_buttons_frame = ttk.Frame(self.files_frame)
        self.remove_file_button = ttk.Button(self.file_buttons_frame, text="🗑️ Remove", 
                                            command=self.remove_selected_files)
        self.clear_files_button = ttk.Button(self.file_buttons_frame, text="❌ Clear All", 
                                           command=self.clear_all_files)
        
        # Output file selection
        self.output_label = ttk.Label(self.left_frame, text="Output Directory:")
        self.output_frame = ttk.Frame(self.left_frame)
        self.output_entry = ttk.Entry(self.output_frame, width=35)
        self.output_button = ttk.Button(self.output_frame, text="📁", command=self.browse_output_directory)
        
        # Include, Exclude and options with multi-select
        self.include_frame = MultiSelectFrame(self.left_frame, "Include Shifts by Names:", 
                                             bg_color=self.bg_color, fg_color=self.text_color, 
                                             select_bg_color=self.accent_color)
        self.exclude_frame = MultiSelectFrame(self.left_frame, "Exclude Shifts by Names:", 
                                            bg_color=self.bg_color, fg_color=self.text_color, 
                                            select_bg_color=self.accent_color)
        self.reminder_frame = MultiSelectFrame(self.left_frame, "Add Reminders for Names:", 
                                             bg_color=self.bg_color, fg_color=self.text_color, 
                                             select_bg_color=self.accent_color)
        
        # Checkboxes
        self.special_var = tk.BooleanVar()
        self.special_check = ttk.Checkbutton(self.left_frame, text="Include Special Shifts (*) when Filtering", 
                                            variable=self.special_var)
        
        self.verbose_var = tk.BooleanVar()
        self.verbose_check = ttk.Checkbutton(self.left_frame, text="Verbose Output", 
                                           variable=self.verbose_var)
        
        # Action buttons
        self.button_frame = ttk.Frame(self.left_frame)
        self.settings_button = ttk.Button(self.button_frame, text="\u2699", command=self.open_settings, width=2)
        self.dry_run_button = ttk.Button(self.button_frame, text="Dry Run", command=self.dry_run)
        self.convert_button = ttk.Button(self.button_frame, text="Convert", command=self.convert)
        self.nextcloud_button = ttk.Button(self.button_frame, text="Replace in Nextcloud", 
                                         command=self.replace_in_nextcloud)
        self.exit_button = ttk.Button(self.button_frame, text="Exit", command=self.root.destroy)
        
        # Initially disable the Nextcloud button until credentials are provided
        self.nextcloud_button.config(state='disabled')
        
        # Console output (right side)
        self.console_label = ttk.Label(self.right_frame, text="Console Output:")
        self.console = scrolledtext.ScrolledText(self.right_frame, height=30, width=80, wrap=tk.WORD, 
                                                borderwidth=2, relief=tk.SUNKEN)
        self.console.configure(state='disabled', font=('Courier', 9), 
                             bg=self.bg_color, fg=self.text_color)
    
    def setup_layout(self):
        # Title and description
        self.title_label.pack(pady=(10, 5))
        self.desc_label.pack(pady=(0, 10))
        
        # Set up main two-column layout
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        self.left_frame.pack(side=tk.LEFT, fill='both', expand=False)
        self.left_frame.pack_propagate(False) 
        self.left_frame.configure(width=350)
        self.separator.pack(side=tk.LEFT, fill='y', padx=5)
        self.right_frame.pack(side=tk.LEFT, fill='both', expand=True)
        
        # Input file selection
        self.input_label.pack(anchor='w', pady=(0, 2))
        self.input_frame.pack(fill='x', pady=(0, 5))
        self.add_file_button.pack(side=tk.LEFT, expand=True, fill='x')
        
        # File list display
        self.files_frame.pack(fill='x', pady=(0, 10))
        self.files_list.pack(side=tk.LEFT, fill='both', expand=True)
        self.files_scrollbar.pack(side=tk.RIGHT, fill='y')
        
        # File buttons
        self.file_buttons_frame.pack(fill='x', pady=2)
        self.remove_file_button.pack(side=tk.LEFT, padx=2)
        self.clear_files_button.pack(side=tk.LEFT, padx=2)
        
        # Output file selection
        self.output_label.pack(anchor='w', pady=(0, 2))
        self.output_frame.pack(fill='x', pady=(0, 10))
        self.output_entry.pack(side=tk.LEFT, expand=True, fill='x')
        self.output_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Include, Exclude and options
        self.include_frame.pack(fill='x', pady=5)
        self.exclude_frame.pack(fill='x', pady=5)
        self.reminder_frame.pack(fill='x', pady=5)
        
        # Checkboxes
        self.special_check.pack(anchor='w', pady=2)
        self.verbose_check.pack(anchor='w', pady=2)
        
        # Action buttons
        self.button_frame.pack(pady=10)
        self.settings_button.pack(side=tk.LEFT, padx=5)
        self.dry_run_button.pack(side=tk.LEFT, padx=5)
        self.convert_button.pack(side=tk.LEFT, padx=5)
        self.nextcloud_button.pack(side=tk.LEFT, padx=5)
        self.exit_button.pack(side=tk.LEFT, padx=5)
        
        # Console output (right side)
        self.console_label.pack(anchor='w', pady=(0, 5))
        self.console.pack(fill='both', expand=True)
    
    def browse_input_files(self):
        """Browse for and select multiple input files."""
        filetypes = [
            ("Text Files", "*.txt"),
            ("Image Files", "*.png;*.jpg;*.jpeg"),
            ("All Files", "*.*")
        ]
        filenames = filedialog.askopenfilenames(title="Select Input Files", filetypes=filetypes)
        if filenames:
            for filename in filenames:
                self.add_input_file(filename)
            self.process_all_input_files()
    
    def add_input_file(self, file_path):
        """Add a file to the input files list if it's not already there."""
        abs_path = os.path.abspath(file_path)
        
        if abs_path not in self.input_files:
            self.input_files.append(abs_path)
            self.files_list.insert(tk.END, os.path.basename(abs_path))
            self.console_print(f"Added file: {abs_path}")
    
    def remove_selected_files(self):
        """Remove selected files from the list."""
        selected_indices = self.files_list.curselection()
        if not selected_indices:
            return
            
        for index in sorted(selected_indices, reverse=True):
            removed_file = self.input_files.pop(index)
            self.files_list.delete(index)
            self.console_print(f"Removed file: {removed_file}")
        
        # Reset shifts data since we've changed input files
        self.shifts = []
        self.shift_names = set()
    
    def clear_all_files(self):
        """Clear all files from the list."""
        self.input_files = []
        self.files_list.delete(0, tk.END)
        self.console_print("Cleared all input files")
        
        # Reset shifts data
        self.shifts = []
        self.shift_names = set()
    
    def process_all_input_files(self):
        """Process all input files to extract shifts and names."""
        try:
            # Reset shifts data
            self.shifts = []
            self.shift_names = set()
            
            self.console_print("\n" + "="*50)
            self.console_print(f"Processing {len(self.input_files)} input files...")
            
            # Process each file
            for file_path in self.input_files:
                self.console_print(f"\nProcessing file: {os.path.basename(file_path)}")
                
                try:
                    # Extract text from file or image
                    text = get_text_from_file(file_path, True)
                    
                    # Parse shifts with stdout captured to display warnings in the GUI
                    captured_output = StringIO()
                    with redirect_stdout(captured_output):
                        file_shifts = parse_shifts(text)
                    
                    # Display any captured output (warnings, etc.)
                    captured_text = captured_output.getvalue()
                    if captured_text.strip():
                        self.console_print(captured_text.strip())
                    
                    if not file_shifts:
                        self.console_print(f"Warning: No shifts were parsed from file {os.path.basename(file_path)}.")
                        continue
                    
                    # Add these shifts to our master list
                    self.shifts.extend(file_shifts)
                    
                    # Extract unique names from this file
                    for shift in file_shifts:
                        # Strip any trailing asterisk
                        name = shift.description.rstrip('*').strip()
                        if name:
                            self.shift_names.add(name)
                    
                    self.console_print(f"Found {len(file_shifts)} shifts in this file.")
                
                except Exception as e:
                    self.console_print(f"Error processing file {os.path.basename(file_path)}: {str(e)}")
            
            # Update the dropdown menus with all names from all files
            self.include_frame.set_items(self.shift_names)
            self.exclude_frame.set_items(self.shift_names)
            self.reminder_frame.set_items(self.shift_names)
            
            self.console_print(f"\nTotal: Found {len(self.shifts)} shifts with {len(self.shift_names)} unique names across all files.")
            
        except Exception as e:
            self.console_print(f"Error processing files: {str(e)}")
    
    def browse_output_directory(self):
        """Browse for an output directory instead of a specific file."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
            # Save the output directory to config
            save_output_dir(directory)
    
    def console_print(self, message):
        """Print a message to the console widget."""
        self.console.configure(state='normal')
        self.console.insert(tk.END, message + '\n')
        self.console.see(tk.END)
        self.console.configure(state='disabled')
        self.root.update_idletasks()
    
    def clear_console(self):
        """Clear the console output."""
        self.console.configure(state='normal')
        self.console.delete(1.0, tk.END)
        self.console.configure(state='disabled')
    
    def convert(self):
        """Convert shifts to an ICS file."""
        self.console_print("\n" + "="*50)
        self.console_print("CONVERT OPERATION")
        
        if not self.input_files:
            self.console_print("Error: Please add at least one input file.")
            return
        
        # Process shifts
        shifts_to_use, success = self._process_shifts()
        if not success:
            return
        
        # Generate ICS file
        try:
            # Generate filename based on first and last shift date
            if shifts_to_use:
                # Sort shifts by date
                sorted_shifts = sorted(shifts_to_use, key=lambda x: x.date)
                self.first_date = sorted_shifts[0].date
                self.last_date = sorted_shifts[-1].date
                
                # Format dates as DD-MM
                first_date_str = self.first_date.strftime('%d-%m')
                last_date_str = self.last_date.strftime('%d-%m')
                
                # Create filename
                filename = f"Shifts_{first_date_str}_{last_date_str}.ics"
                output_dir = self.output_entry.get()
                output_file = os.path.join(output_dir, filename)
                
                verbose = self.verbose_var.get()
                if verbose:
                    self.console_print(f"Using automatically generated filename: {filename}")
                    self.console_print(f"Generating ICS file '{output_file}'...")
            else:
                self.console_print("Error: No shifts to process.")
                return
            
            # Call ICS generator with stdout captured to display warnings in the GUI
            reminder_names = self.reminder_frame.get_selected_items()
            captured_output = StringIO()
            with redirect_stdout(captured_output):
                output_file = generate_ics(shifts_to_use, output_file, reminder_names)
            
            # Display any captured output (warnings, etc.)
            captured_text = captured_output.getvalue()
            if captured_text.strip():
                self.console_print(captured_text.strip())
                
            self.console_print(f"Successfully created calendar file: {output_file}")
            self.console_print(f"Found and processed {len(shifts_to_use)} shifts spanning {len(set(shift.date for shift in shifts_to_use))} days")
            self.console_print(f"Combined data from {len(self.input_files)} input files.")
            
            # Store the generated file and date range
            self.last_generated_ics = output_file
            
            # Show success message
            messagebox.showinfo("Success", f"Successfully created calendar file:\n{output_file}")
            
        except Exception as e:
            self.console_print(f"Error generating ICS file: {e}")
    
    def dry_run(self):
        """Perform a dry run to show shifts that would be included without creating an ICS file."""
        self.console_print("\n" + "="*50)
        self.console_print("=== DRY RUN MODE ===")
        
        if not self.input_files:
            self.console_print("Error: Please add at least one input file.")
            return
        
        # Process shifts
        shifts_to_use, success = self._process_shifts(is_dry_run=True)
        if not success:
            return
            
        # Display shifts that would be included
        if shifts_to_use:
            sorted_shifts = sorted(shifts_to_use, key=lambda x: x.date)
            date_range = (
                sorted_shifts[0].date.strftime('%d-%m'),
                sorted_shifts[-1].date.strftime('%d-%m')
            )
            
            self.console_print(f"\nDry run complete - found {len(shifts_to_use)} shifts that would be included")
            self.console_print(f"Date range: {date_range[0]} to {date_range[1]}")
            self.console_print(f"Shifts would span {len(set(shift.date for shift in shifts_to_use))} days")
            self.console_print(f"From {len(self.input_files)} input files")
            
            reminder_names = self.reminder_frame.get_selected_items()
            if reminder_names:
                self.console_print(f"Reminders would be added for: {', '.join(reminder_names)}")
            else:
                self.console_print("No reminders would be added")
            
            self.console_print("\nNo ICS file was created. Click 'Convert' to generate the actual ICS file.")
        else:
            self.console_print("No shifts would be included in output.")
    
    def _process_shifts(self, is_dry_run=False):
        """
        Process input files and apply filtering to get shifts to use.
        
        Args:
            is_dry_run: Whether this is a dry run (affects verbose output)
            
        Returns:
            Tuple of (shifts_to_use, success_flag)
        """
        # Get values from GUI
        output_dir = self.output_entry.get()
        include_names = self.include_frame.get_selected_items()
        exclude_names = self.exclude_frame.get_selected_items()
        include_special = self.special_var.get()
        verbose = self.verbose_var.get()
        
        # Keep track of filtered shifts for verbose output
        excluded_shifts = []
        
        # Validation
        if not self.input_files:
            self.console_print('Error: Please add at least one input file.')
            return [], False
            
        if not output_dir and not is_dry_run:
            self.console_print('Error: Please specify an output directory.')
            return [], False
            
        # Ensure output directory exists if not a dry run
        if not is_dry_run and not os.path.isdir(output_dir):
            self.console_print(f"Error: Output directory '{output_dir}' does not exist.")
            return [], False
        
        try:
            # Process input files if we don't have shifts yet
            if not self.shifts:
                self.process_all_input_files()
                
                if not self.shifts:
                    self.console_print("Warning: No shifts were parsed from the input files.")
                    return [], False
            
            # Start with all shifts
            all_shifts = self.shifts.copy()
            shifts_to_use = self.shifts.copy()
            
            # First apply inclusion filter if specified
            if include_names:
                if verbose:
                    self.console_print(f"Including shifts for: {', '.join(include_names)}")
                
                # Filter shifts by name
                filtered_shifts = []
                for shift in shifts_to_use:
                    # Strip any trailing asterisk before checking
                    shift_name = shift.description.rstrip('*').strip()
                    
                    # Check if it's a special shift (has an asterisk)
                    is_special = '*' in shift.description
                    
                    # Include the shift if it matches the include filter OR if it's special and the special flag is set
                    if shift_name in include_names or (is_special and include_special):
                        filtered_shifts.append(shift)
                    elif verbose and is_dry_run:
                        excluded_shifts.append((shift, "Not in include list"))
                
                shifts_to_use = filtered_shifts
                
                if not shifts_to_use:
                    self.console_print(f"Warning: No shifts found for the specified inclusion names.")
                    return [], False
            
            # Then apply exclusion filter if specified
            if exclude_names:
                if verbose:
                    self.console_print(f"Excluding shifts for: {', '.join(exclude_names)}")
                
                # Filter out shifts by name
                filtered_shifts = []
                for shift in shifts_to_use:
                    shift_name = shift.description.rstrip('*').strip()
                    if shift_name not in exclude_names:
                        filtered_shifts.append(shift)
                    elif verbose and is_dry_run:
                        excluded_shifts.append((shift, "In exclude list"))
                
                shifts_to_use = filtered_shifts
                
                if not shifts_to_use:
                    self.console_print(f"Warning: No shifts left after excluding specified names.")
                    return [], False
            
            # Always display the included shifts, regardless of verbose mode
            self.console_print(f"\nShifts to include ({len(shifts_to_use)}):")
            for i, shift in enumerate(sorted(shifts_to_use, key=lambda x: (x.date, x.start_time)), 1):
                date_str = shift.date.strftime('%d.%m.%Y')
                day_str = shift.date.strftime('%a')
                start_str = shift.start_time.strftime('%H:%M')
                end_str = shift.end_time.strftime('%H:%M')
                
                # Display end time on next day if the shift spans midnight
                if shift.spans_midnight:
                    end_day = f"({day_str}+1)"
                    self.console_print(f"  {i:2d}. {date_str} {day_str} {start_str} - {end_str} {end_day} {shift.description}")
                else:
                    self.console_print(f"  {i:2d}. {date_str} {day_str} {start_str} - {end_str} {shift.description}")
            
            # In verbose mode, also show excluded shifts
            if verbose and is_dry_run and excluded_shifts:
                self.console_print(f"\nShifts excluded by filters ({len(excluded_shifts)}):")
                for i, (shift, reason) in enumerate(sorted(excluded_shifts, key=lambda x: (x[0].date, x[0].start_time)), 1):
                    date_str = shift.date.strftime('%d.%m.%Y')
                    day_str = shift.date.strftime('%a')
                    start_str = shift.start_time.strftime('%H:%M')
                    end_str = shift.end_time.strftime('%H:%M')
                    
                    # Display end time on next day if the shift spans midnight
                    if shift.spans_midnight:
                        end_day = f"({day_str}+1)"
                        self.console_print(f"  [EXCLUDED] {i:2d}. {date_str} {day_str} {start_str} - {end_str} {end_day} {shift.description}")
                    else:
                        self.console_print(f"  [EXCLUDED] {i:2d}. {date_str} {day_str} {start_str} - {end_str} {shift.description}")
            
            return shifts_to_use, True
            
        except Exception as e:
            self.console_print(f"Error: {str(e)}")
            return [], False
    
    def update_frame_sizes(self):
        """Update frame sizes after the window is displayed to ensure all content is visible."""
        self.root.update_idletasks()
        self.left_frame.update_idletasks()
        
        # Get all packed widgets in the left frame to calculate total required height
        required_height = 0
        for widget in self.left_frame.winfo_children():
            if widget.winfo_manager() == 'pack':
                required_height += widget.winfo_reqheight() + 10  # Add padding
        
        required_height += 50
        
        # Get current window dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # If we need more height, resize the window
        if required_height > window_height:
            new_height = required_height + 100
            self.root.geometry(f"{window_width}x{new_height}")
        
        # Ensure the left frame uses available height
        self.left_frame.configure(height=max(required_height, window_height - 50))
    
    def replace_in_nextcloud(self):
        """Replace events in Nextcloud calendar with the generated ICS."""
        self.console_print("\n" + "="*50)
        self.console_print("REPLACE IN NEXTCLOUD OPERATION")
        
        # Check if all Nextcloud fields are filled
        if not self.validate_nextcloud_credentials():
            self.console_print("Error: Please provide Nextcloud credentials in the Settings dialog.")
            messagebox.showwarning("Nextcloud Settings Missing", 
                                  "Please configure your Nextcloud settings first.\n"
                                  "Click the 'Settings' button to open the settings dialog.")
            return
        
        # Check if we have input files
        if not self.input_files:
            self.console_print("Error: Please add at least one input file.")
            return
        
        # Process shifts and generate ICS
        shifts_to_use, success = self._process_shifts()
        if not success:
            return
        
        # Generate ICS file
        try:
            # Generate filename based on first and last shift date
            if shifts_to_use:
                # Sort shifts by date
                sorted_shifts = sorted(shifts_to_use, key=lambda x: x.date)
                self.first_date = sorted_shifts[0].date
                self.last_date = sorted_shifts[-1].date
                
                # Format dates as DD-MM
                first_date_str = self.first_date.strftime('%d-%m')
                last_date_str = self.last_date.strftime('%d-%m')
                
                # Create filename
                filename = f"Shifts_{first_date_str}_{last_date_str}.ics"
                output_dir = self.output_entry.get()
                output_file = os.path.join(output_dir, filename)
                
                verbose = self.verbose_var.get()
                if verbose:
                    self.console_print(f"Using automatically generated filename: {filename}")
                    self.console_print(f"Generating ICS file '{output_file}'...")
            else:
                self.console_print("Error: No shifts to process.")
                return
            
            # Call ICS generator with stdout captured to display warnings in the GUI
            reminder_names = self.reminder_frame.get_selected_items()
            captured_output = StringIO()
            with redirect_stdout(captured_output):
                output_file = generate_ics(shifts_to_use, output_file, reminder_names)
            
            # Display any captured output (warnings, etc.)
            captured_text = captured_output.getvalue()
            if captured_text.strip():
                self.console_print(captured_text.strip())
                
            self.console_print(f"Successfully created calendar file: {output_file}")
            self.last_generated_ics = output_file
            
            # Now sync with Nextcloud
            nextcloud_settings = {
                'url': self.nextcloud_url,
                'username': self.nextcloud_username,
                'password': self.nextcloud_password,
                'calendar': self.nextcloud_calendar
            }
            
            result = sync_with_nextcloud(
                self.last_generated_ics,
                nextcloud_settings,
                (self.first_date, self.last_date),
                self.console_print
            )
            
            if result.get('success'):
                messagebox.showinfo(
                    "Success", 
                    f"Successfully replaced events in Nextcloud calendar '{result['calendar']}'\n"
                    f"Date range: {result['date_range'][0]} to {result['date_range'][1]}"
                )
            else:
                messagebox.showerror("Nextcloud Error", f"Error syncing with Nextcloud:\n{result['error']}")
            
        except Exception as e:
            self.console_print(f"Error generating ICS file: {e}")
            messagebox.showerror("Error", f"Error generating ICS file:\n{str(e)}")
    
    def open_settings(self):
        """Open the settings dialog and update application settings."""
        try:
            # Open the settings dialog with current settings
            settings_dialog = SettingsDialog(self.root)
            
            # If the dialog was closed with the Save button, update the settings
            if hasattr(settings_dialog, 'result'):
                # Update Nextcloud settings from the dialog result
                nextcloud_settings = settings_dialog.result['nextcloud']
                self.nextcloud_url = nextcloud_settings['url']
                self.nextcloud_username = nextcloud_settings['username']
                self.nextcloud_password = nextcloud_settings['password']
                self.nextcloud_calendar = nextcloud_settings['calendar']
                
                # Update the theme setting
                appearance_settings = settings_dialog.result['appearance']
                theme_changed = self.theme_name != appearance_settings['theme_name']
                self.theme_name = appearance_settings['theme_name']
                
                # Update button state
                self.validate_nextcloud_credentials()
                
                # Show message about theme change requiring restart
                if theme_changed:
                    messagebox.showinfo(
                        "Theme Changed", 
                        "The theme setting has been changed. "
                        "Please restart the application for the change to take full effect."
                    )
        except Exception as e:
            self.console_print(f"Error opening settings dialog: {e}")
            messagebox.showerror("Settings Error", f"Could not open settings dialog: {e}")
    
    def validate_nextcloud_credentials(self):
        """Validate Nextcloud credentials and enable/disable the Nextcloud button accordingly."""
        if self.nextcloud_url and self.nextcloud_username and self.nextcloud_password and self.nextcloud_calendar:
            self.nextcloud_button.config(state='normal')
            return True
        else:
            self.nextcloud_button.config(state='disabled')
            return False


def create_gui():
    """Create and run the GUI for the ShiftPlan to ICS converter."""
    root = tk.Tk()
    app = ShiftPlanGUI(root)
    
    # Update after a short delay to ensure proper sizing
    root.after(100, app.update_frame_sizes)
    
    root.mainloop()


if __name__ == '__main__':
    create_gui() 