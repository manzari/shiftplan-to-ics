# ShiftPlan to ICS Converter

A Python tool to convert text-based schedules (shift plans) in German format into ICS (iCalendar) files that can be imported into calendar applications like Google Calendar, Apple Calendar, Outlook, etc.

## Notes

- OCR error handling has been removed from this version. Input files should use standard formatting without OCR errors.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/shiftplan-to-ics.git
cd shiftplan-to-ics
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. For OCR functionality (optional):
   - Install Tesseract OCR on your system:
     - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
     - macOS: `brew install tesseract`
     - Windows: Download and install from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Make sure the additional Python dependencies are installed:
```bash
```
   - The tool uses Tesseract's page segmentation mode 6 (--psm 6) which works best for shift plan images by treating them as a single block of text

5. For drag and drop functionality in the GUI (optional):
   - Install the TkDnD extension:
     - Ubuntu/Debian: `sudo apt-get install python3-tk tk-tktreectrl`
     - macOS: `brew install tkdnd`
     - Windows: Download and install from [GitHub](https://github.com/petasis/tkdnd)
   - For Python binding, install the package:
```bash
```

## Usage

The tool can be used in three ways:

### Graphical User Interface (GUI)

The easiest way to use the tool is through the GUI:

```bash
# Launch the GUI
python run_gui.py
```

The GUI provides an intuitive interface with:
- File selection dialogs for input and output files
- Drag and drop support for input files
- Multi-select dropdown lists for including/excluding shifts and adding reminders
- Checkboxes for special shifts and verbose output
- A "Dry Run" button to preview shifts that would be included without creating a file
- A console area showing detailed processing information
- Automatic filename generation in the format "Shifts_DD-MM_DD-MM.ics" based on the date range of shifts

After loading a file, the application automatically extracts all names from the shift plan and populates the multi-select lists, making it easy to choose which shifts to include in your calendar.

### Command line

Basic usage:
```bash
python -m src.main input_file.txt output.ics
```

Using an image of a shift plan:
```bash
python -m src.main shift_plan.jpg output.ics
```

With verbose output:
```bash
python -m src.main input_file.txt output.ics -v
```

Including specific names:
```bash
python -m src.main input_file.txt output.ics -i "Thomas,Julia"
```

Excluding specific names:
```bash
python -m src.main input_file.txt output.ics -e "Thomas,Julia"
```

Including special shifts (marked with *) even when filtering:
```bash
python -m src.main input_file.txt output.ics -i "Thomas" -s
```

Adding reminders for specific people:
```bash
python -m src.main input_file.txt output.ics -r "Thomas"
```

Performing a dry run (preview shifts without creating an ICS file):
```bash
python -m src.main input_file.txt output.ics --dry-run -v
```

Options:
- `-v, --verbose`: Show detailed output
- `-i, --include`: Include shifts by names (comma-separated list)
- `-e, --exclude`: Exclude shifts by names (comma-separated list)
- `-r, --reminder`: Only add reminders to events for specific people (comma-separated list)
- `-s, --add-special-shift`: Include special shifts (marked with *) even when filtering
- `-d, --dry-run`: Show shifts that would be included without creating an ICS file

When using the `--dry-run` option with `--verbose`, the tool will also show shifts that were excluded due to filtering options.

### As a module

```python
from src.parser import parse_shifts
from src.ics_generator import generate_ics

# Parse shift data from text
shifts = parse_shifts("Mi. 30.04 17:00 01:00 Night Shift")

# Filter shifts if needed
shifts = [shift for shift in shifts if shift.description.rstrip('*').strip() in ["Thomas", "Julia"]]

# Generate ICS file (with reminders only for Thomas)
generate_ics(shifts, "my_shifts.ics", reminder_names=["Thomas"])
```

## Building Standalone Executables

The application can be packaged as a standalone executable for Windows, macOS, and Linux using PyInstaller:

### Prerequisites

1. Ensure PyInstaller is installed:
```bash
pip install pyinstaller
```

2. For customized icons, place the appropriate files in the `resources` directory:
   - Windows: `icon.ico`
   - macOS: `icon.icns`
   - Linux: `icon.png`
   
### Building the Application

PyInstaller can only build executables for the platform you're currently running on (cross-compilation is not supported). To build for all platforms, you need to run the build process on each target platform.

#### Using the build script

The easiest way to build the application:

```bash
python build.py
```

This will build a standalone executable for your current platform and place it in the `dist` directory.

To see information about building for all platforms:

```bash
python build.py --info
```

#### Automated builds with GitHub Actions

This repository includes GitHub Actions workflows to automatically build packages for Windows, macOS, and Linux when:
- A tag is pushed (e.g., `v1.0.0`)
- Code is pushed to the main branch
- A pull request is made to the main branch
- The workflow is manually triggered

To create a new release with pre-built packages:

1. Tag your release with a version number:
```bash
git tag v1.0.0
git push origin v1.0.0
```

2. GitHub Actions will automatically:
   - Build packages for all three platforms
   - Create a new GitHub Release with the tagged version
   - Attach the built executables to the release

You can also manually trigger a build through the GitHub Actions tab in your repository.

#### Building on Multiple Platforms

To create executables for all platforms, you need to:

1. **Windows**: Run `python build.py` on a Windows system
2. **macOS**: Run `python build.py` on a macOS system
3. **Linux**: Run `python build.py` on a Linux system

For each platform, collect the generated executable from the `dist` directory.

#### Using the spec file directly

For more control over the build process, you can use the provided spec file:

```bash
pyinstaller shiftplan_to_ics.spec
```

The spec file is configured to detect the current platform and build accordingly.

### Distribution

After building, you can distribute:

- **Windows**: The `shiftplan_to_ics.exe` file in the `dist` directory
- **macOS**: The `ShiftPlan to ICS.app` bundle in the `dist` directory
- **Linux**: The `shiftplan_to_ics` executable in the `dist` directory

### Notes on Platform Compatibility

- PyInstaller only builds for the platform it's running on - it doesn't support cross-compilation
- For iOS compatibility, consider using a cross-platform framework like Kivy or BeeWare's Briefcase
- Always test your builds on each target platform

## Input Format

The parser supports the German format commonly used in shift plans:

```
Mi. 30.04 17:00 01:00 Thomas
18:00 02:00 Julia *
Do. 01.05 00:00 08:00 Sarah
```

- First line includes day abbreviation (Mi. = Wednesday) and date (DD.MM)
- Subsequent lines without date/day refer to the same day
- Times are in 24-hour format (HH:MM)
- End time can be on the next day (e.g., 17:00 01:00 means 5pm to 1am next day)
- Asterisk (*) at the end of the description marks a special shift

## Handling of shifts that span midnight

The tool automatically detects shifts that span across midnight (when end time is earlier than start time) and creates calendar events that span to the next day.

## License

MIT