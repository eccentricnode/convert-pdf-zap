"""
File handling utilities for PDF conversion.
Extracted from main.py to enable reusability and testing.
"""

import os
import sys
from pathlib import Path


def validate_pdf_file(file_path):
    """
    Validate that the provided file is a valid PDF file.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        bool: True if valid PDF file
        
    Raises:
        SystemExit: If file doesn't exist or isn't a PDF
    """
    if not os.path.exists(file_path):
        print(f"Error: File does not exist: {file_path}")
        sys.exit(1)
    
    if not file_path.lower().endswith('.pdf'):
        print(f"Error: File must be a PDF: {file_path}")
        sys.exit(1)
    
    return True


def get_file_info(file_path):
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        dict: File information including size in MB
    """
    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    return {
        'path': file_path,
        'size_bytes': file_size_bytes,
        'size_mb': file_size_mb,
        'exists': True
    }


def validpdf(submitted_file):
    """
    Legacy function for PDF validation (from original main.py).
    Kept for backward compatibility.
    
    Args:
        submitted_file: File path to validate
        
    Returns:
        bool: True if valid PDF
        
    Raises:
        SystemExit: If not a valid PDF
    """
    if submitted_file.endswith('pdf'):
        return True
    else:
        print("not a valid pdf")
        sys.exit(1)
