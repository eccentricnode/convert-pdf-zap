"""
PDF to Markdown Converter
Supports multiple conversion methods with configurable options.
"""

import sys
import argparse
import time
import logging
from pathlib import Path

from converters import DoclingConverter, PyMuPDFConverter, SimplePyMuPDFConverter
from utils import run_with_timeout
from utils.file_handler import validate_pdf_file, get_file_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
_log = logging.getLogger(__name__)



def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py document.pdf              # Default conversion with PyMuPDF
  python3 main.py document.pdf --mupdf      # Advanced conversion with PyMuPDF
  python3 main.py document.pdf --simple     # Simple PyMuPDF converter (faster)
  python3 main.py document.pdf --ai         # Force AI-powered conversion
  python3 main.py document.pdf --no-images  # Text only, no images
  python3 main.py document.pdf --timeout 600 # 10 minute timeout
        """
    )
    
    parser.add_argument('pdf_file', help='PDF file to convert')
    
    # Converter selection
    converter_group = parser.add_mutually_exclusive_group()
    converter_group.add_argument('--mupdf', action='store_true',
                               help='Use PyMuPDF converter (better layout preservation)')
    converter_group.add_argument('--simple', action='store_true',
                               help='Use Simple PyMuPDF converter (faster, less error handling)')
    converter_group.add_argument('--ai', action='store_true',
                               help='Force AI-powered Docling converter')
    
    # Options
    parser.add_argument('--no-images', action='store_true',
                       help='Extract text only, no images')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Conversion timeout in seconds (default: 300)')
    parser.add_argument('--output', '-o', default='text.md',
                       help='Output file name (default: text.md)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    return parser


def select_converter(args):
    """Select appropriate converter based on arguments."""
    if args.mupdf:
        _log.info("Using PyMuPDF converter (advanced features)")
        config = {}
        if args.no_images:
            config['extract_images'] = False
        return PyMuPDFConverter(**config)
    elif args.simple:
        _log.info("Using Simple PyMuPDF converter (faster, streamlined)")
        config = {}
        if args.no_images:
            config['extract_images'] = False
        return SimplePyMuPDFConverter(**config)
    elif args.ai:
        _log.info("Using Docling converter (AI-powered)")
        config = {}
        if args.no_images:
            config['generate_page_images'] = False
            config['generate_picture_images'] = False
        return DoclingConverter(**config)
    else:
        # Default: Use PyMuPDF as the new default converter
        if args.no_images:
            _log.info("Using PyMuPDF converter (default, text-only)")
            return PyMuPDFConverter(extract_images=False)
        else:
            _log.info("Using PyMuPDF converter (default, with images)")
            return PyMuPDFConverter()


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    try:
        validate_pdf_file(args.pdf_file)
    except SystemExit:
        print(f"✗ Error: Invalid or missing PDF file: {args.pdf_file}")
        sys.exit(1)
    
    # Show file info
    file_info = get_file_info(args.pdf_file)
    print(f"Processing: {args.pdf_file} ({file_info['size_mb']:.1f} MB)")
    
    print("============ Converting PDF ============")
    start_time = time.time()
    
    try:
        # Select and initialize converter
        converter = select_converter(args)
        converter_info = converter.get_converter_info()
        _log.info(f"Using {converter_info['name']}")
        
        # Convert PDF to Markdown with timeout
        def do_conversion():
            _log.info("Starting PDF conversion...")
            return converter.convert(args.pdf_file)
        
        markdown_content = run_with_timeout(do_conversion, timeout_seconds=args.timeout)
        
        # Write output
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Success
        total_time = time.time() - start_time
        _log.info(f"Conversion completed in {total_time:.2f} seconds")
        print(f"✓ Conversion completed successfully in {total_time:.2f} seconds!")
        print(f"✓ Output saved to: {output_path.absolute()}")
        
    except Exception as e:
        _log.error(f"Conversion failed: {e}")
        print(f"✗ Error during conversion: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
