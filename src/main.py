#!/usr/bin/env python3
"""
ShiftPlan to ICS Converter - Main Module

This is the main entry point for the application.
"""

import os
import sys
import argparse
from pathlib import Path
import pytesseract
from pytesseract import TesseractError
from PIL import Image


def get_text_from_file(file_path, verbose=False):
    """Extract text from file, which can be a text file or an image.
    
    Args:
        file_path: Path to the file.
        verbose: Whether to print verbose output.
        
    Returns:
        str: The extracted text.
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Determine file type by extension
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext in ['.txt', '.text']:
        # Text file
        if verbose:
            print(f"Reading text file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        # Image file
        if verbose:
            print(f"Processing image file using OCR: {file_path}")
        
        # Check if pytesseract is installed
        try:
            original_image = Image.open(file_path)
            
            # Convert to RGB mode if not already (some images might be in RGBA or other modes)
            if original_image.mode != 'RGB':
                image = original_image.convert('RGB')
            else:
                image = original_image
                
            # No advanced preprocessing available
            preprocessed_image = image
            
            if verbose:
                print("No advanced preprocessing available. Using original image.")
            
            # Set up better Tesseract configuration for improved accuracy
            # These settings can be adjusted based on your specific needs
            custom_config = r'--oem 3 --psm 6'
            
            # Try OCR with English first (more commonly available)
            try:
                if verbose:
                    print("Attempting OCR with English language...")
                
                # Try with preprocessed image first
                text = pytesseract.image_to_string(preprocessed_image, lang='eng', config=custom_config)
                
                # If no text is found, try with original image
                if not text.strip():
                    if verbose:
                        print("No text found with preprocessed image, trying original image...")
                    text = pytesseract.image_to_string(original_image, lang='eng', config=custom_config)
                
                if text.strip():
                    if verbose:
                        print("Successfully processed with English language.")
                        print(f"Detected text length: {len(text)} characters")
                    return text
                else:
                    if verbose:
                        print("No text detected with English language.")
                        
                    # Try with different PSM modes
                    psm_modes = [3, 4, 1, 11, 12]  # Different page segmentation modes to try
                    for psm in psm_modes:
                        if verbose:
                            print(f"Trying with PSM mode {psm}...")
                        config = f'--oem 3 --psm {psm}'
                        text = pytesseract.image_to_string(preprocessed_image, lang='eng', config=config)
                        if text.strip():
                            if verbose:
                                print(f"Text detected with PSM mode {psm}!")
                                print(f"Detected text length: {len(text)} characters")
                            return text
                    
                    if verbose:
                        print("No text detected with any PSM mode.")
                    
                    # Try without specifying language as last resort
                    text = pytesseract.image_to_string(preprocessed_image, config=custom_config)
                    if text.strip():
                        if verbose:
                            print("Text detected with default language!")
                            print(f"Detected text length: {len(text)} characters")
                        return text
                    else:
                        raise Exception("No text could be detected in the image.")
                        
            except pytesseract.TesseractError as e:
                if verbose:
                    print(f"English language data not available: {e}")
                    print("Falling back to default language...")
                
                # Try without specifying language as last resort
                text = pytesseract.image_to_string(preprocessed_image, config=custom_config)
                if text.strip():
                    if verbose:
                        print("Successfully processed with default language.")
                        print(f"Detected text length: {len(text)} characters")
                    return text
                else:
                    raise Exception("No text could be detected in the image.")
                    
        except ImportError:
            raise ImportError("pytesseract module is required for OCR. Install with 'pip install pytesseract'")
        except Exception as e:
            tesseract_install_message = (
                "Error processing image file: {0}\n\n"
                "To process images, please ensure Tesseract OCR is properly installed:\n"
                "1. Install Tesseract OCR on your system:\n"
                "   - On Ubuntu/Debian: sudo apt-get install tesseract-ocr\n"
                "   - On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. Install language data (if needed):\n"
                "   - On Ubuntu/Debian: sudo apt-get install tesseract-ocr-eng (for English)\n"
                "\nIf Tesseract is installed but no text is detected, try:\n"
                "- Ensure the image has sufficient resolution and contrast\n"
                "- Try preprocessing the image with an image editor to increase contrast\n"
                "- Make sure the text in the image is not rotated or distorted\n"
            ).format(str(e))
            raise Exception(tesseract_install_message)
    
    else:
        # Try to read as text file
        try:
            if verbose:
                print(f"Unknown file type, trying to read as text: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            raise ValueError(f"Unsupported file type: {file_ext}")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="ShiftPlan to ICS Converter")
    parser.add_argument("--cli", action="store_true", help="Run in command-line mode")
    
    # Parse only the --cli argument first
    args, remaining_args = parser.parse_known_args()
    
    if args.cli:
        # Set remaining_args as sys.argv for the CLI module
        sys.argv = [sys.argv[0]] + remaining_args
        from src.cli import run_cli
        run_cli()
    else:
        # Start GUI mode
        from src.gui import create_gui
        create_gui()


if __name__ == "__main__":
    main() 