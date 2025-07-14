#!/usr/bin/env python3
"""
PDF AI Processing Tool
Extracts first page content from PDFs and optionally processes with AI.
"""

import sys
import base64
import os
import json
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

# Import utilities
from image_utils import compress_image_with_fitz
from cli_handler import create_cli_handler


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


def process_pdf_document(pdf_path, options=None):
    """
    Core PDF processing function without CLI dependencies.
    
    Args:
        pdf_path: Path to PDF file
        options: dict with processing options
            - include_images: bool (default True)
            - format_type: str "markdown" or "json" (default "markdown")
            - ai_provider: str "openrouter", "backup", or "none" (default "none")
            - custom_prompt: str (optional)
    
    Returns:
        dict: {
            "success": bool,
            "result": dict,           # Raw extraction result
            "formatted_content": str, # Formatted content
            "final_content": str,     # Final content (after AI if applicable)
            "metadata": dict,         # Processing metadata
            "error": str              # Error message if success=False
        }
    """
    options = options or {}
    
    try:
        # Extract content from PDF
        result = extract_first_page(
            pdf_path, 
            include_images=options.get('include_images', True)
        )
        
        # Format content
        format_type = options.get('format_type', 'markdown')
        formatted_content = format_for_ai(result, format_type)
        
        # Process with AI if requested
        ai_provider = options.get('ai_provider', 'none')
        final_content = formatted_content
        
        if ai_provider and ai_provider != 'none':
            final_content = process_with_ai(
                formatted_content, 
                ai_provider, 
                options.get('custom_prompt')
            )
        
        return {
            "success": True,
            "result": result,
            "formatted_content": formatted_content,
            "final_content": final_content,
            "metadata": {
                "file_name": result["filename"],
                "text_length": len(result["text"]),
                "image_count": result["image_count"],
                "ai_processed": ai_provider != 'none',
                "format_type": format_type
            },
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "formatted_content": None,
            "final_content": None,
            "metadata": {"file_name": os.path.basename(pdf_path) if pdf_path else "unknown"},
            "error": str(e)
        }


def main():
    """Main CLI entry point."""
    # Create CLI handler (combines argument parsing + output formatting)
    cli = create_cli_handler()
    
    # You can add custom arguments here if needed:
    # cli.add_argument('--custom-flag', action='store_true', help='Custom flag')
    
    # Parse arguments
    args = cli.parse_args()
    
    # Validate PDF file
    cli.validate_file(args.pdf_file)
    
    # Start processing
    cli.print_processing_start(args.pdf_file)
    
    # Prepare processing options
    options = {
        'include_images': not args.no_images,
        'format_type': 'json' if args.json else 'markdown',
        'ai_provider': args.ai,
        'custom_prompt': args.ai_prompt
    }
    
    # Process the PDF
    processing_result = process_pdf_document(args.pdf_file, options)
    
    if not processing_result["success"]:
        cli.print_error(processing_result["error"])
        sys.exit(1)
    
    # Print extraction stats
    cli.print_extraction_stats(processing_result["result"])
    
    # Print AI processing message
    if args.ai and args.ai != 'none':
        cli.print_ai_processing(args.ai)
    
    # Handle output
    output_file = cli.get_output_file(args)
    
    if output_file:
        cli.save_to_file(
            processing_result["final_content"],
            output_file, 
            processing_result["result"], 
            processing_result["metadata"]["ai_processed"]
        )
    else:
        cli.print_content(processing_result["final_content"])


if __name__ == "__main__":
    main()
