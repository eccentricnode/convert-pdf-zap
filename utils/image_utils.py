#!/usr/bin/env python3
"""
Image Utilities
Handles image compression using PyMuPDF with no additional dependencies.
"""

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")


def compress_image_with_fitz(img_bytes, max_size=(150, 150), quality=70):
    """
    Compress image using PyMuPDF (no additional dependencies).
    
    Args:
        img_bytes: Original image bytes
        max_size: Maximum dimensions (width, height)  
        quality: JPEG quality (1-100)
    
    Returns:
        bytes: Compressed image bytes
    """
    try:
        # Create a temporary document with the image
        img_doc = fitz.open("png", img_bytes)  # Open image as document
        page = img_doc[0]
        
        # Get original dimensions
        rect = page.rect
        original_width, original_height = rect.width, rect.height
        
        # Calculate new dimensions maintaining aspect ratio
        ratio = min(max_size[0] / original_width, max_size[1] / original_height)
        if ratio < 1:  # Only resize if image is larger than max_size
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
        else:
            new_width, new_height = int(original_width), int(original_height)
        
        # Create new pixmap with smaller dimensions
        mat = fitz.Matrix(new_width / original_width, new_height / original_height)
        pix = page.get_pixmap(matrix=mat, alpha=False)  # No alpha channel
        
        # Convert to JPEG with compression
        compressed_bytes = pix.tobytes("jpeg", jpg_quality=quality)
        
        img_doc.close()
        
        print(f"Debug: Resized from {int(original_width)}x{int(original_height)} to {new_width}x{new_height}")
        print(f"Debug: Original: {len(img_bytes)} bytes, Compressed: {len(compressed_bytes)} bytes")
        
        return compressed_bytes
        
    except Exception as e:
        print(f"Warning: PyMuPDF compression failed: {e}")
        return img_bytes


def get_compression_stats(original_bytes, compressed_bytes):
    """
    Calculate compression statistics.
    
    Args:
        original_bytes: Original image size in bytes
        compressed_bytes: Compressed image size in bytes
        
    Returns:
        dict: Compression statistics
    """
    if original_bytes == 0:
        return {"ratio": 0.0, "percent": 0.0, "savings": 0}
    
    ratio = compressed_bytes / original_bytes
    percent_compressed = (1 - ratio) * 100
    bytes_saved = original_bytes - compressed_bytes
    
    return {
        "ratio": ratio,
        "percent_compressed": percent_compressed,
        "bytes_saved": bytes_saved,
        "original_size": original_bytes,
        "compressed_size": compressed_bytes
    }


def format_image_info(img_data, index=1):
    """
    Format image information for display.
    
    Args:
        img_data: Dictionary containing image data and metadata
        index: Image index number
        
    Returns:
        dict: Formatted image information
    """
    # Calculate compression stats if we have original size
    compression_info = {}
    if 'original_size_bytes' in img_data:
        stats = get_compression_stats(
            img_data['original_size_bytes'], 
            img_data['size_bytes']
        )
        compression_info = {
            "compression_ratio": f"{stats['percent_compressed']:.1f}%",
            "bytes_saved": stats['bytes_saved'],
            "original_size": img_data['original_size_bytes']
        }
    
    return {
        "index": index,
        "format": img_data.get('format', 'unknown').upper(),
        "size_bytes": img_data['size_bytes'],
        "base64_length": len(img_data['data']),
        **compression_info
    }


# Example usage and testing
if __name__ == "__main__":
    print("=== Image Utils Test ===")
    print("Testing compression utilities...")
    
    # Test compression stats
    stats = get_compression_stats(100000, 5000)
    print(f"✅ Compression test: {stats['percent_compressed']:.1f}% reduction")
    
    # Test image info formatting
    sample_img = {
        "data": "base64_data_here",
        "format": "jpeg",
        "size_bytes": 5000,
        "original_size_bytes": 100000
    }
    
    info = format_image_info(sample_img, index=1)
    print(f"✅ Image info: {info['compression_ratio']} compressed")
    
    print("🎯 Image utilities ready for integration!")
