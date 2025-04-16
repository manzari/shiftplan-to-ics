"""
Custom Widgets for ShiftPlan to ICS Converter

This module provides custom widgets used in the application.
"""

import tkinter as tk
from tkinter import ttk


class MultiSelectFrame(ttk.Frame):
    """A frame containing a listbox for multiple selection."""
    
    def __init__(self, parent, title, *args, bg_color="#FFEBEE", fg_color="#880E4F", 
                select_bg_color="#F48FB1", **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        # Store the theme colors
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.select_bg_color = select_bg_color
        
        # Create a style for this widget
        style = ttk.Style()
        style.configure("MultiSelect.TLabel", background=bg_color, foreground=fg_color)
        
        # Create widgets
        self.title_label = ttk.Label(self, text=title, style="MultiSelect.TLabel")
        
        # Create listbox with scrollbar
        self.listbox_frame = ttk.Frame(self)
        self.listbox = tk.Listbox(self.listbox_frame, selectmode=tk.MULTIPLE, height=5, width=25,
                                  bg=bg_color, fg=fg_color, selectbackground=select_bg_color,
                                  selectforeground="#FFFFFF", activestyle="dotbox")
        self.scrollbar = ttk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        
        # Add button frame for Select All and Clear buttons
        self.button_frame = ttk.Frame(self)
        self.select_all_button = ttk.Button(self.button_frame, text="Select All", 
                                           command=self.select_all, width=10)
        self.clear_button = ttk.Button(self.button_frame, text="Clear", 
                                     command=self.clear_selection, width=10)
        
        # Set up layout
        self.title_label.pack(anchor='w', pady=(5, 0))
        self.listbox_frame.pack(fill='both', expand=True, pady=(0, 5))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill='both', expand=True)
        
        # Set up button layout
        self.button_frame.pack(fill='x', pady=(0, 5))
        self.select_all_button.pack(side=tk.LEFT, padx=2)
        self.clear_button.pack(side=tk.LEFT, padx=2)
    
    def set_items(self, items):
        """Set the items in the listbox."""
        # Save current selections if any
        current_selections = self.get_selected_items()
        
        # Clear and repopulate
        self.listbox.delete(0, tk.END)
        sorted_items = sorted(items)
        for item in sorted_items:
            self.listbox.insert(tk.END, item)
            
        # Restore selections if possible
        if current_selections:
            for i, item in enumerate(sorted_items):
                if item in current_selections:
                    self.listbox.selection_set(i)
    
    def get_selected_items(self):
        """Get the selected items from the listbox."""
        selected_indices = self.listbox.curselection()
        return [self.listbox.get(i) for i in selected_indices]
    
    def select_all(self):
        """Select all items in the listbox."""
        self.listbox.selection_set(0, tk.END)
    
    def clear_selection(self):
        """Clear all selections in the listbox."""
        self.listbox.selection_clear(0, tk.END) 