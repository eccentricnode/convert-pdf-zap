import sys
import os
sys.path.append('.')
from converters import SimplePyMuPDFConverter, PyMuPDFConverter

def test_conversion(pdf_path):
    """Test PDF conversion with both converters."""
    print(f"Testing conversion of: {pdf_path}")
    
    # Exit if file doesn't exist
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        return
    
    print("\n=== Testing SimplePyMuPDFConverter ===")
    simple_converter = SimplePyMuPDFConverter()
    try:
        result = simple_converter.convert(pdf_path)
        print(f"✓ SimplePyMuPDFConverter successfully converted the PDF")
        print(f"Result length: {len(result)} characters")
    except Exception as e:
        print(f"✗ SimplePyMuPDFConverter failed: {e}")
    
    print("\n=== Testing original PyMuPDFConverter for comparison ===")
    original_converter = PyMuPDFConverter()
    try:
        result = original_converter.convert(pdf_path)
        print(f"✓ Original PyMuPDFConverter successfully converted the PDF")
        print(f"Result length: {len(result)} characters")
    except Exception as e:
        print(f"✗ Original PyMuPDFConverter failed: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 test_conversion.py <pdf_file_path>")
        sys.exit(1)
    
    test_conversion(sys.argv[1])
