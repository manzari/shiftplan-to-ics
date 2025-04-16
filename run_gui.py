#!/usr/bin/env python3
"""
ShiftPlan to ICS Converter - Launcher

This script launches the ShiftPlan to ICS converter in either GUI or CLI mode.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the current directory to the path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up default output directory info
default_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
print(f"Default output directory: {default_output_dir}")

try:
    # Import and run the appropriate mode
    from src.main import main
    main()
except ImportError as e:
    tk.Tk().withdraw()  # Hide the root window
    messagebox.showerror("Import Error", f"Error importing modules: {str(e)}\nPlease make sure all dependencies are installed:\npip install -r requirements.txt")
except Exception as e:
    tk.Tk().withdraw()  # Hide the root window
    messagebox.showerror("Error", f"An error occurred: {str(e)}") 