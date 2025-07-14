#!/usr/bin/env python3
"""
Command Line Interface Handler
Handles argument parsing and output formatting for the PDF AI Processing Tool.
"""

import sys
import argparse
import os
import traceback


class CLIHandler:
    """Handles command-line argument parsing and output formatting."""
    
    def __init__(self):
        self.verbose = False
        self.parser = self._create_parser()
    
    def _create_parser(self):
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Extract PDF content and optionally process with AI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py document.pdf                        # Extract to markdown
  python main.py document.pdf --json                 # Extract to JSON
  python main.py document.pdf --no-images            # Text only
  python main.py document.pdf --save                 # Save to file
  python main.py document.pdf --ai openrouter        # Process with AI (main model)
  python main.py document.pdf --ai backup            # Process with AI (backup model)
  python main.py document.pdf --ai openrouter --ai-prompt "Summarize this document"
  python main.py document.pdf --output result.md     # Custom output file
            """
        )
        
        parser.add_argument('pdf_file', help='PDF file to process')
        
        # Output options
        parser.add_argument('--json', action='store_true',
                           help='Output as JSON instead of Markdown')
        parser.add_argument('--no-images', action='store_true',
                           help='Skip image extraction (text only)')
        parser.add_argument('--output', '-o',
                           help='Output file path')
        parser.add_argument('--save', action='store_true',
                           help='Save to default filename (pdf_name.md or .json)')
        
        # AI options
        parser.add_argument('--ai', choices=['openrouter', 'backup', 'none'], 
                           default='none',
                           help='AI processing: openrouter (main model), backup (fallback model), or none')
        parser.add_argument('--ai-prompt',
                           help='Custom prompt for AI processing')
        
        # Utility
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
        
        return parser
    
    def parse_args(self):
        """Parse command line arguments and set internal state."""
        args = self.parser.parse_args()
        self.verbose = args.verbose
        return args
    
    def add_argument(self, *args, **kwargs):
        """Add custom argument to the parser."""
        self.parser.add_argument(*args, **kwargs)
    
    # Output formatting methods
    def print_processing_start(self, pdf_file):
        """Print processing start message."""
        if self.verbose:
            print(f"📄 Processing: {pdf_file}")
    
    def print_extraction_stats(self, result):
        """Print extraction statistics."""
        if self.verbose:
            print(f"✅ Extracted {len(result['text'])} characters of text")
            print(f"✅ Found {result['image_count']} images")
    
    def print_ai_processing(self, ai_provider):
        """Print AI processing message."""
        if self.verbose:
            model_type = "backup model" if ai_provider == "backup" else "main model"
            print(f"🤖 Processing with OpenRouter ({model_type})...")
    
    def print_save_success(self, output_file, result=None, ai_processed=False):
        """Print successful save message with optional stats."""
        print(f"✅ Content saved to: {output_file}")
        if not ai_processed and result:  # Don't show stats if AI processed
            print(f"📊 Found {result['image_count']} images from first page")
    
    def print_content(self, content):
        """Print content to console."""
        print(content)
    
    def print_error(self, error, show_traceback=None):
        """Print error message with optional traceback."""
        print(f"❌ Error: {error}")
        show_tb = show_traceback if show_traceback is not None else self.verbose
        if show_tb:
            traceback.print_exc()
    
    def print_file_not_found(self, pdf_file):
        """Print file not found error."""
        print(f"❌ Error: File not found: {pdf_file}")
    
    def print_warning(self, message):
        """Print warning message."""
        print(f"Warning: {message}")
    
    def validate_file(self, pdf_file):
        """Validate PDF file exists."""
        if not os.path.exists(pdf_file):
            self.print_file_not_found(pdf_file)
            sys.exit(1)
    
    def get_output_file(self, args):
        """Determine output file based on arguments."""
        if args.output:
            return args.output
        elif args.save:
            pdf_name = os.path.splitext(os.path.basename(args.pdf_file))[0]
            extension = "json" if args.json else "md"
            return f"{pdf_name}_extracted.{extension}"
        return None
    
    def save_to_file(self, content, output_file, result=None, ai_processed=False):
        """Save content to file with error handling."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            self.print_save_success(output_file, result, ai_processed)
        except Exception as e:
            self.print_error(f"Could not save to file: {e}")
            sys.exit(1)


def create_cli_handler():
    """Factory function to create CLI handler."""
    return CLIHandler()


# Testing function
if __name__ == "__main__":
    # Test the CLI handler
    cli = create_cli_handler()
    
    # Test adding custom arguments
    cli.add_argument('--test-flag', action='store_true', help='Test flag')
    cli.add_argument('--custom-option', help='Custom option')
    
    print("Testing CLI Handler...")
    print("-" * 40)
    
    # Mock test (would normally parse real args)
    print("✅ CLI Handler can be extended with custom arguments")
    print("✅ Combines argument parsing + output formatting")
    print("✅ Ready for integration!")
