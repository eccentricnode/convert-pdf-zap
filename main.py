#!/usr/bin/env python3
"""
PDF AI Processing Tool
Extracts first page content from PDFs and optionally processes with AI.
"""

import sys
import base64
import os
import json
import argparse
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)

# Import image utilities
from image_utils import compress_image_with_fitz


def extract_first_page(pdf_path, include_images=True):
    """
    Extract text and all images from first page of PDF.
    
    Args:
        pdf_path: Path to PDF file
        include_images: Whether to extract all images from page
        
    Returns:
        dict: {
            "text": str,
            "images": [{"data": base64_str, "format": str, "index": int, "size_bytes": int}],
            "image_count": int,
            "filename": str
        }
    """
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("File must be a PDF")
    
    if not os.path.exists(pdf_path):
        raise ValueError(f"File not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        doc.close()
        raise ValueError("PDF has no pages")
    
    page = doc[0]  # First page only
    
    # Extract text
    text = page.get_text().strip()
    
    # Extract all images if requested
    image_data = []
    if include_images:
        try:
            images = page.get_images()
            if images:
                # Get all images from the page
                for img_index, img_info in enumerate(images):
                    try:
                        xref = img_info[0]
                        img_dict = doc.extract_image(xref)
                        img_bytes = img_dict["image"]
                        img_ext = img_dict["ext"]
                        
                        # Skip very small images (likely icons/artifacts)
                        if len(img_bytes) > 1000:  # Minimum 1KB
                            # Compress image to 150x150 max using PyMuPDF
                            compressed_bytes = compress_image_with_fitz(img_bytes)
                            compressed_b64 = base64.b64encode(compressed_bytes).decode()
                            
                            image_data.append({
                                "data": compressed_b64,
                                "format": "jpeg",  # Always JPEG after compression
                                "index": img_index + 1,
                                "size_bytes": len(compressed_bytes),
                                "original_size_bytes": len(img_bytes),
                                "original_format": img_ext
                            })
                    except Exception as e:
                        print(f"Warning: Could not extract image {img_index + 1}: {e}")
                        continue
        except Exception as e:
            # Skip if image extraction fails, don't crash
            print(f"Warning: Could not extract images: {e}")
    
    doc.close()
    
    return {
        "text": text,
        "images": image_data,
        "image_count": len(image_data) if image_data else 0,
        "filename": os.path.basename(pdf_path)
    }


def format_for_ai(result, format_type="markdown"):
    """Format extraction result for AI consumption."""
    if format_type == "json":
        return json.dumps(result, indent=2)
    
    # Markdown format
    output = []
    
    output.append(f"# PDF Extraction: {result['filename']}")
    output.append("")
    
    if result["text"]:
        output.append("## Extracted Text")
        output.append("")
        # Split text into paragraphs for better markdown formatting
        paragraphs = result["text"].split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Clean up line breaks within paragraphs
                clean_paragraph = ' '.join(line.strip() for line in paragraph.split('\n') if line.strip())
                output.append(clean_paragraph)
                output.append("")
    else:
        output.append("## No Text Found")
        output.append("")
    
    if result["images"] and len(result["images"]) > 0:
        output.append(f"## Images ({result['image_count']} found)")
        output.append("")
        
        for i, img in enumerate(result["images"]):
            output.append(f"### Image {img['index']}")
            output.append("")
            output.append(f"- **Format**: {img['format'].upper()}")
            output.append(f"- **Size**: {img['size_bytes']:,} bytes")
            if 'original_size_bytes' in img:
                compression_ratio = (1 - img['size_bytes'] / img['original_size_bytes']) * 100
                output.append(f"- **Original Size**: {img['original_size_bytes']:,} bytes ({compression_ratio:.1f}% compressed)")
                output.append(f"- **Original Format**: {img.get('original_format', 'unknown').upper()}")
            output.append(f"- **Base64 length**: {len(img['data']):,} characters")
            output.append("")
            
            # Embed image as markdown
            output.append(f"![Image {img['index']}](data:image/{img['format']};base64,{img['data']})")
            output.append("")
    else:
        output.append("## No Images Found")
        output.append("")
    
    return "\n".join(output)


def process_with_ai(content, ai_provider="none", custom_prompt=None):
    """
    Process extracted content with OpenRouter AI.
    
    Args:
        content: Extracted content (markdown or json)
        ai_provider: AI service to use ("openrouter", "backup", "none")
        custom_prompt: Optional custom prompt to use
    
    Returns:
        str: AI-processed response or original content if no AI
    """
    if ai_provider == "none":
        return content
    
    # Import and initialize AI processor
    try:
        from ai_processor import create_ai_processor
        processor = create_ai_processor()
        
        if not processor or not processor.is_available():
            return content
        
        # Process based on provider type
        if ai_provider == "backup":
            return processor.process_content(content, use_backup=True, custom_prompt=custom_prompt)
        else:  # "openrouter" or default
            return processor.process_with_fallback(content, custom_prompt=custom_prompt)
            
    except ImportError as e:
        print(f"❌ Error importing AI processor: {e}")
        return content
    except Exception as e:
        print(f"❌ AI processing failed: {e}")
        return content


def create_parser():
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

def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate PDF file
    if not os.path.exists(args.pdf_file):
        print(f"❌ Error: File not found: {args.pdf_file}")
        sys.exit(1)
    
    if args.verbose:
        print(f"📄 Processing: {args.pdf_file}")
    
    try:
        # Extract content from PDF
        result = extract_first_page(args.pdf_file, include_images=not args.no_images)
        
        if args.verbose:
            print(f"✅ Extracted {len(result['text'])} characters of text")
            print(f"✅ Found {result['image_count']} images")
        
        # Format content
        format_type = "json" if args.json else "markdown"
        content = format_for_ai(result, format_type)
        
        # Process with AI if requested
        if args.ai and args.ai != 'none':
            if args.verbose:
                model_type = "backup model" if args.ai == "backup" else "main model"
                print(f"🤖 Processing with OpenRouter ({model_type})...")
            content = process_with_ai(content, args.ai, args.ai_prompt)
        
        # Determine output file
        output_file = None
        if args.output:
            output_file = args.output
        elif args.save:
            pdf_name = os.path.splitext(os.path.basename(args.pdf_file))[0]
            extension = "json" if args.json else "md"
            output_file = f"{pdf_name}_extracted.{extension}"
        
        # Save or print output
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Content saved to: {output_file}")
            if not args.ai:  # Don't show stats if AI processed
                print(f"📊 Found {result['image_count']} images from first page")
        else:
            print(content)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
