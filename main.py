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

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)


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
                            image_data.append({
                                "data": base64.b64encode(img_bytes).decode(),
                                "format": img_ext,
                                "index": img_index + 1,
                                "size_bytes": len(img_bytes)
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
            output.append(f"- **Base64 length**: {len(img['data']):,} characters")
            output.append("")
            
            # Embed image as markdown
            output.append(f"![Image {img['index']}](data:image/{img['format']};base64,{img['data']})")
            output.append("")
    else:
        output.append("## No Images Found")
        output.append("")
    
    return "\n".join(output)


def process_with_ai(content, ai_provider="none"):
    """
    Process extracted content with AI.
    
    Args:
        content: Extracted content (markdown or json)
        ai_provider: AI service to use ("openai", "anthropic", "local", "none")
    
    Returns:
        str: AI-processed response or original content if no AI
    """
    if ai_provider == "none":
        return content
    
    # Placeholder for AI integration
    # You can add your preferred AI service here
    
    if ai_provider == "openai":
        # TODO: Add OpenAI integration
        # import openai
        # response = openai.chat.completions.create(...)
        print("🤖 OpenAI integration coming soon...")
        return content
    
    elif ai_provider == "anthropic":
        # TODO: Add Anthropic integration
        # import anthropic
        # response = anthropic.messages.create(...)
        print("🤖 Anthropic integration coming soon...")
        return content
    
    elif ai_provider == "local":
        # TODO: Add local model integration (ollama, etc.)
        print("🤖 Local AI integration coming soon...")
        return content
    
    else:
        print(f"Unknown AI provider: {ai_provider}")
        return content


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract PDF content and optionally process with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py document.pdf                     # Extract to markdown
  python main.py document.pdf --json              # Extract to JSON
  python main.py document.pdf --no-images         # Text only
  python main.py document.pdf --save              # Save to file
  python main.py document.pdf --ai openai         # Process with OpenAI
  python main.py document.pdf --output result.md  # Custom output file
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
    parser.add_argument('--ai', choices=['openai', 'anthropic', 'local'],
                       help='Process with AI service')
    parser.add_argument('--ai-prompt',
                       help='Custom prompt for AI processing')
    
    # Utility
    parser.add_argument('--demo', action='store_true',
                       help='Show demo output')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    return parser


def show_demo():
    """Show a demo of the extraction capabilities."""
    print("=== PDF AI Processing Tool Demo ===")
    print()
    print("This tool extracts content from the first page of PDFs for AI processing.")
    print()
    
    sample_result = {
        "text": "Document Header\nImportant content for AI analysis...",
        "images": [
            {
                "data": "base64_encoded_image_data...",
                "format": "jpeg",
                "index": 1,
                "size_bytes": 15420
            }
        ],
        "image_count": 1,
        "filename": "sample.pdf"
    }
    
    print("Example Markdown output:")
    print("```markdown")
    print(format_for_ai(sample_result, "markdown"))
    print("```")
    print()
    print("Usage examples:")
    print("  python main.py document.pdf                    # Basic extraction")
    print("  python main.py document.pdf --save             # Save to file")
    print("  python main.py document.pdf --ai openai        # Process with AI")
    print("  python main.py document.pdf --json --save      # JSON output")


def main():
    """Main entry point."""
    parser = create_parser()
    
    # Handle demo mode first (before requiring PDF file)
    if len(sys.argv) > 1 and '--demo' in sys.argv:
        show_demo()
        return
    
    args = parser.parse_args()
    
    # Handle demo mode
    if args.demo:
        show_demo()
        return
    
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
        if args.ai:
            if args.verbose:
                print(f"🤖 Processing with {args.ai}...")
            content = process_with_ai(content, args.ai)
        
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
