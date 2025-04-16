"""
Settings Dialog for ShiftPlan to ICS Converter

This module provides the settings dialog for the application.
"""

import tkinter as tk
from tkinter import ttk

from src.config import (
    get_nextcloud_settings, save_nextcloud_settings,
    get_appearance_settings, save_appearance_settings
)


class SettingsDialog(tk.Toplevel):
    """Dialog window for application settings, including Nextcloud integration."""
    
    def __init__(self, parent, nextcloud_settings=None):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("450x300")
        self.resizable(False, False)
        
        # Get appearance settings
        appearance_settings = get_appearance_settings()
        self.theme_name = tk.StringVar(value=appearance_settings.get('theme_name', 'pink'))
        
        # Define color palettes
        # Pink theme colors
        self.pink_bg = "#FFEBEE"  # Light pink background
        self.pink_accent = "#F48FB1"  # Medium pink accent
        self.pink_text = "#880E4F"  # Dark pink for text
        
        # Rainbow theme colors (unicorn puke)
        self.rainbow_bg = "#E3F2FD"  # Light blue background
        self.rainbow_accent = "#64FFDA"  # Teal/mint accent 
        self.rainbow_highlight = "#FF4081"  # Bright pink highlight
        self.rainbow_text = "#7C4DFF"  # Purple text
        
        # Default system colors
        self.default_bg = self.parent.cget('bg')
        self.default_fg = 'black'
        self.default_accent = '#d9d9d9'  # Standard button color in most systems
        
        # Create a custom style for this dialog - this needs to be created BEFORE apply_current_theme()
        self.style = ttk.Style()
        
        # Now set theme colors based on preference
        self.apply_current_theme()
        
        # Make the dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Create a notebook for different settings categories
        self.notebook = ttk.Notebook(self, style="Settings.TNotebook")
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Nextcloud settings frame
        self.nextcloud_frame = ttk.Frame(self.notebook, padding=10, style="Settings.TFrame")
        self.notebook.add(self.nextcloud_frame, text="Nextcloud Integration")
        
        # Appearance settings frame
        self.appearance_frame = ttk.Frame(self.notebook, padding=10, style="Settings.TFrame")
        self.notebook.add(self.appearance_frame, text="Appearance")
        
        # If no settings provided, load from config
        if nextcloud_settings is None:
            nextcloud_settings = get_nextcloud_settings()
        
        # Initialize values from passed settings
        self.nextcloud_url = tk.StringVar(value=nextcloud_settings.get('url', ''))
        self.nextcloud_username = tk.StringVar(value=nextcloud_settings.get('username', ''))
        self.nextcloud_password = tk.StringVar(value=nextcloud_settings.get('password', ''))
        self.nextcloud_calendar = tk.StringVar(value=nextcloud_settings.get('calendar', ''))
        
        # Create Nextcloud settings widgets
        self.create_nextcloud_widgets()
        
        # Create Appearance settings widgets
        self.create_appearance_widgets()
        
        # Buttons frame
        self.button_frame = ttk.Frame(self, style="Settings.TFrame")
        self.button_frame.pack(fill='x', pady=(0, 10), padx=10)
        
        # Save and cancel buttons
        self.save_button = ttk.Button(self.button_frame, text="Save", command=self.save_settings, style="Settings.TButton")
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.destroy, style="Settings.TButton")
        
        self.save_button.pack(side='right', padx=5)
        self.cancel_button.pack(side='right', padx=5)
        
        # Center the dialog on the parent window
        self.center_on_parent()
        
        # Wait for the dialog to be closed
        self.wait_window()
    
    def create_nextcloud_widgets(self):
        """Create widgets for Nextcloud settings."""
        # Nextcloud URL
        self.url_label = ttk.Label(self.nextcloud_frame, text="Nextcloud URL:", style="Settings.TLabel")
        self.url_entry = ttk.Entry(self.nextcloud_frame, width=35, textvariable=self.nextcloud_url, style="Settings.TEntry")
        self.url_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.url_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Nextcloud Username
        self.username_label = ttk.Label(self.nextcloud_frame, text="Username:", style="Settings.TLabel")
        self.username_entry = ttk.Entry(self.nextcloud_frame, width=35, textvariable=self.nextcloud_username, style="Settings.TEntry")
        self.username_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.username_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        # Nextcloud Password
        self.password_label = ttk.Label(self.nextcloud_frame, text="Password:", style="Settings.TLabel")
        self.password_entry = ttk.Entry(self.nextcloud_frame, width=35, show='*', textvariable=self.nextcloud_password, style="Settings.TEntry")
        self.password_label.grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.password_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        
        # Nextcloud Calendar Name
        self.calendar_label = ttk.Label(self.nextcloud_frame, text="Calendar Name:", style="Settings.TLabel")
        self.calendar_entry = ttk.Entry(self.nextcloud_frame, width=35, textvariable=self.nextcloud_calendar, style="Settings.TEntry")
        self.calendar_label.grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.calendar_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
        
        # Help text
        help_text = "Enter your Nextcloud server details to enable calendar integration."
        self.help_label = ttk.Label(self.nextcloud_frame, text=help_text, wraplength=400, style="Settings.TLabel")
        self.help_label.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=(20, 5))
        
        # Configure grid columns to expand properly
        self.nextcloud_frame.columnconfigure(1, weight=1)
    
    def create_appearance_widgets(self):
        """Create widgets for appearance settings."""
        # Theme selection label
        self.theme_label = ttk.Label(
            self.appearance_frame,
            text="Select Theme:",
            style="Settings.TLabel"
        )
        self.theme_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
        
        # Theme dropdown (Combobox)
        self.theme_combobox = ttk.Combobox(
            self.appearance_frame,
            textvariable=self.theme_name,
            values=["default", "pink", "rainbow"],
            state="readonly",
            width=15
        )
        self.theme_combobox.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        self.theme_combobox.bind("<<ComboboxSelected>>", self.on_theme_change)
        
        # Friendly names for the themes
        theme_names = {
            "default": "System Default",
            "pink": "Pink Theme",
            "rainbow": "Unicorn Puke"
        }
        
        # Theme preview
        current_theme_name = theme_names.get(self.theme_name.get(), "Unknown")
        preview_text = f"Current theme: {current_theme_name}"
            
        self.preview_label = ttk.Label(
            self.appearance_frame,
            text=preview_text,
            style="Settings.TLabel"
        )
        self.preview_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Theme requires restart notice
        restart_text = "Theme changes require restart to fully apply"
        self.restart_label = ttk.Label(
            self.appearance_frame,
            text=restart_text,
            style="Settings.TLabel",
            font=("Helvetica", 9, "italic")
        )
        self.restart_label.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        
        # Help text
        help_text = "Select your preferred appearance settings for the application."
        self.appearance_help_label = ttk.Label(
            self.appearance_frame, 
            text=help_text, 
            wraplength=400, 
            style="Settings.TLabel"
        )
        self.appearance_help_label.grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=(20, 5))
        
        # Configure grid columns to expand properly
        self.appearance_frame.columnconfigure(1, weight=1)
    
    def on_theme_change(self, event=None):
        """Handle theme change in real time to preview the change."""
        try:
            self.apply_current_theme()
            
            # Friendly names for the themes
            theme_names = {
                "default": "System Default",
                "pink": "Pink Theme",
                "rainbow": "Unicorn Puke"
            }
            
            # Update the preview text
            current_theme_name = theme_names.get(self.theme_name.get(), "Unknown")
            preview_text = f"Current theme: {current_theme_name}"
            self.preview_label.config(text=preview_text)
        except Exception as e:
            print(f"Error updating theme preview: {e}")
    
    def apply_current_theme(self):
        """Apply the current theme colors based on the theme setting."""
        try:
            # Set current theme colors based on preference
            theme = self.theme_name.get()
            
            if theme == 'pink':
                self.bg_color = self.pink_bg
                self.accent_color = self.pink_accent
                self.text_color = self.pink_text
            elif theme == 'rainbow':
                self.bg_color = self.rainbow_bg
                self.accent_color = self.rainbow_accent
                self.text_color = self.rainbow_text
            else:  # default
                self.bg_color = self.default_bg
                self.accent_color = self.default_accent
                self.text_color = self.default_fg
            
            # Apply colors to the dialog
            self.configure(bg=self.bg_color)
            
            # Configure styles
            self.style.configure("Settings.TFrame", background=self.bg_color)
            self.style.configure("Settings.TLabel", background=self.bg_color, foreground=self.text_color)
            self.style.configure("Settings.TButton", background=self.accent_color, foreground=self.text_color)
            self.style.configure("Settings.TEntry", fieldbackground=self.bg_color)
            self.style.configure("Settings.TNotebook", background=self.bg_color)
            self.style.configure("Settings.TCheckbutton", background=self.bg_color, foreground=self.text_color)
            self.style.configure("Settings.TCombobox", fieldbackground=self.bg_color)
            
            # Apply rainbow-specific highlights if applicable
            if theme == 'rainbow':
                self.style.map("Settings.TButton", 
                               background=[("active", self.rainbow_highlight), ("pressed", self.rainbow_highlight)])
            elif theme == 'pink':
                self.style.map("Settings.TButton", 
                               background=[("active", self.pink_dark), ("pressed", self.pink_dark)])
        except Exception as e:
            print(f"Error applying theme: {e}")
            # Fallback to system defaults if there's an error
            self.configure(bg=self.default_bg)
    
    def save_settings(self):
        """Save the settings and close the dialog."""
        # Create dictionary with Nextcloud settings
        nextcloud_settings = {
            'url': self.nextcloud_url.get().strip(),
            'username': self.nextcloud_username.get().strip(),
            'password': self.nextcloud_password.get().strip(),
            'calendar': self.nextcloud_calendar.get().strip()
        }
        
        # Create dictionary with appearance settings
        appearance_settings = {
            'theme_name': self.theme_name.get()
        }
        
        # Save to config files
        save_nextcloud_settings(nextcloud_settings)
        save_appearance_settings(appearance_settings)
        
        # Store in result for the caller
        self.result = {
            'nextcloud': nextcloud_settings,
            'appearance': appearance_settings
        }
        
        self.destroy()
    
    def center_on_parent(self):
        """Center this dialog on the parent window."""
        self.update_idletasks()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}") 