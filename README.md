# Simple PDF First-Page Extractor

A minimal, fast PDF extractor that gets just the first page text and optionally the first image - perfect for AI processing.

## Features

- Extract text from first page only (fast!)
- Extract ALL images from first page as base64 (not just the first one!)
- Simple command-line interface
- JSON output option for programmatic use
- Only ~100 lines of code
- Single dependency (PyMuPDF)
- Filters out tiny images (likely icons/artifacts)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Extract text and image from first page
python main.py document.pdf

# Extract only text (faster)
python main.py document.pdf --no-image

# Get JSON output for programmatic use
python main.py document.pdf --json
```

### Example Output

```
=== PDF: document.pdf ===

=== EXTRACTED TEXT ===
This is the text content from the first page...

=== 3 IMAGES FOUND ===
--- Image 1 ---
Format: jpeg
Size: 15,420 bytes
Base64 data: 15420 characters

=== IMAGE 1 DATA (BASE64) ===
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...

--- Image 2 ---
Format: png
Size: 8,234 bytes
Base64 data: 8234 characters

=== IMAGE 2 DATA (BASE64) ===
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...

--- Image 3 ---
Format: jpeg
Size: 12,567 bytes
Base64 data: 12567 characters

=== IMAGE 3 DATA (BASE64) ===
data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...
```

### JSON Output
```json
{
  "text": "This is the text content...",
  "images": [
    {
      "data": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
      "format": "jpeg",
      "index": 1,
      "size_bytes": 15420
    },
    {
      "data": "iVBORw0KGgoAAAANSUhEUgAAA...",
      "format": "png", 
      "index": 2,
      "size_bytes": 8234
    }
  ],
  "image_count": 2,
  "filename": "document.pdf"
}
```
## For AI Processing

This tool is designed specifically for AI workflows where you need:

- Quick text extraction from document previews
- Base64 image data for ALL images on first page (great for vision models)
- Simple, predictable output format
- Fast processing for large document batches

The output format is optimized for feeding directly into AI models or processing pipelines.
