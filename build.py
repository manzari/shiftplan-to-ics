#!/usr/bin/env python3
"""
Build script for ShiftPlan to ICS Converter

This script uses PyInstaller to build standalone executables for Windows, 
macOS, and Linux platforms.
"""

import os
import sys
import platform
import shutil
import subprocess
import argparse
from pathlib import Path


def clear_build_directories():
    """Clear the build and dist directories"""
    for directory in ['build', 'dist']:
        if os.path.exists(directory):
            print(f"Removing {directory} directory...")
            shutil.rmtree(directory)
    
    # Also remove spec file if it exists
    spec_file = "shiftplan_to_ics.spec"
    if os.path.exists(spec_file):
        print(f"Removing {spec_file}...")
        os.remove(spec_file)


def get_data_files():
    """Get data files to include in the build"""
    data_files = [
        # Add any additional data files here
        # Example: ('source_file_or_dir', 'destination_directory_in_bundle')
    ]
    
    # Consider adding example files or resources
    if os.path.exists('examples'):
        data_files.append(('examples', 'examples'))
    
    return data_files


def get_platform_options(target_platform=None):
    """Get platform-specific options for PyInstaller
    
    Args:
        target_platform: Optional target platform to override current platform
    """
    # Use current platform if not specified
    system = target_platform or platform.system().lower()
    
    if system == 'windows':
        return {
            'icon': 'resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
            'console': False,  # Set to False for GUI-only app
            'ext': '.exe',
            'name': 'Windows executable (.exe)'
        }
    elif system == 'darwin':  # macOS
        return {
            'icon': 'resources/icon.icns' if os.path.exists('resources/icon.icns') else None,
            'console': False,
            'ext': '.app',
            'name': 'macOS app bundle (.app)'
        }
    else:  # Linux
        return {
            'icon': 'resources/icon.png' if os.path.exists('resources/icon.png') else None,
            'console': False,
            'ext': '',
            'name': 'Linux executable'
        }


def build_executable(target_platform=None):
    """Build executable using PyInstaller
    
    Args:
        target_platform: Optional target platform to build for (windows, darwin, linux)
                        This is for display only, as PyInstaller can only build for the current platform
    """
    # Get current platform
    current_platform = platform.system().lower()
    
    # If target is specified and doesn't match current, show warning
    if target_platform and target_platform != current_platform:
        print(f"\nWARNING: You requested to build for {target_platform}, but PyInstaller can only build for")
        print(f"the current platform ({current_platform}). Cross-compilation is not supported.")
        print("You must run this script on each target platform to build for that platform.\n")
        print("Would you like to continue building for the current platform?")
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("Build canceled.")
            return
    
    # Clear previous build files
    clear_build_directories()
    
    # Get data files and platform options for current platform
    data_files = get_data_files()
    platform_options = get_platform_options()
    
    # Set output name based on platform
    output_name = 'shiftplan_to_ics'
    if current_platform == 'windows':
        output_name += '.exe'
    
    # Construct PyInstaller command
    cmd = [
        'pyinstaller',
        f'--name={output_name}',
        '--clean',
        '--windowed',  # Create a windowed app without console
        '--onefile',   # Create a single executable file
        '--noupx',     # Don't use UPX (can cause problems on some systems)
    ]
    
    # Add data files
    for src, dst in data_files:
        cmd.append(f'--add-data={src}{os.pathsep}{dst}')
    
    # Add platform-specific options
    if platform_options.get('icon'):
        cmd.append(f'--icon={platform_options["icon"]}')
    
    # Add hidden imports for all the modules we use
    hidden_imports = [
        'caldav', 'icalendar', 'PIL', 'pytesseract',
        'pytz', 'dateutil', 'urllib3', 'requests', 'tkinter'
    ]
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # Add entry point
    cmd.append('src/main.py')
    
    # Run the command
    print("Running PyInstaller with the following command:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def create_resources_directory():
    """Create resources directory with placeholder icon files"""
    if not os.path.exists('resources'):
        os.makedirs('resources')
        print("Created resources directory")
        
        # Add placeholder message
        with open('resources/README.txt', 'w') as f:
            f.write("Place your icon files in this directory:\n")
            f.write("- icon.ico for Windows\n")
            f.write("- icon.icns for macOS\n")
            f.write("- icon.png for Linux\n")


def show_platform_info():
    """Show information about building for different platforms"""
    current_platform = platform.system().lower()
    
    print("\n==== ShiftPlan to ICS Builder - Platform Information ====\n")
    print("PyInstaller can only build executables for the platform it's running on.")
    print("To create executables for all platforms, you need to run this script on each target platform.")
    print("\nCurrent platform:", platform.system(), platform.machine())
    
    print("\nTo build for all platforms:")
    print("  1. Run 'python build.py' on Windows to create a Windows .exe")
    print("  2. Run 'python build.py' on macOS to create a macOS .app bundle")
    print("  3. Run 'python build.py' on Linux to create a Linux executable")
    
    platforms = [
        ('windows', 'Windows executable (.exe)'),
        ('darwin', 'macOS app bundle (.app)'),
        ('linux', 'Linux executable')
    ]
    
    print("\nPlatform-specific information:")
    for platform_key, platform_name in platforms:
        options = get_platform_options(platform_key)
        icon_path = options.get('icon') or "Not found"
        icon_status = "✓ Found" if os.path.exists(icon_path) else "✗ Missing"
        
        if platform_key == current_platform:
            print(f"  → {platform_name} (current platform)")
            print(f"    - Icon: {icon_path} ({icon_status})")
            print(f"    - Output: dist/{output_name_for_platform(platform_key)}")
        else:
            print(f"  • {platform_name}")
            print(f"    - Icon: {icon_path} ({icon_status})")
            print(f"    - Build on a {platform_name} system to create this executable")


def output_name_for_platform(platform_key):
    """Get the output executable name for a specific platform"""
    base_name = "shiftplan_to_ics"
    if platform_key == 'windows':
        return f"{base_name}.exe"
    elif platform_key == 'darwin':
        return f"ShiftPlan to ICS.app"
    else:  # Linux
        return base_name


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Build ShiftPlan to ICS Converter executable")
    parser.add_argument('--info', action='store_true', help='Show information about building for different platforms')
    parser.add_argument('--platform', choices=['windows', 'darwin', 'linux'], 
                      help='Platform to build for (for information only, builds for current platform)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    
    # Create resources directory if it doesn't exist
    create_resources_directory()
    
    if args.info:
        show_platform_info()
        sys.exit(0)
    
    print("Building ShiftPlan to ICS Converter...")
    
    try:
        build_executable(args.platform)
        print("\nBuild completed successfully!")
        print(f"Executable created in 'dist' directory: {os.path.abspath('dist')}")
    except Exception as e:
        print(f"Error building executable: {e}")
        sys.exit(1) 