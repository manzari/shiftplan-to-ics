"""
ShiftPlan to ICS Converter

A tool to convert text-based shift plans into ICS calendar files.
"""

__version__ = "1.0.0"

from src.gui import create_gui
from src.parser import parse_shifts
from src.ics_generator import generate_ics
from src.cli import run_cli
from src.main import main 