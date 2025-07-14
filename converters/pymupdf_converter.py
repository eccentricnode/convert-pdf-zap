"""
PyMuPDF-based PDF converter.
Fast, feature-rich alternative with advanced image extraction support.
"""

import logging
import os
import base64
from typing import Dict, Any, List, Tuple, Optional
from io import BytesIO

from .base_converter import BaseConverter

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PyMuPDFConverter(BaseConverter):
    """
    PyMuPDF-based converter for fast text and image extraction.
    
    Features:
    - Fast text extraction with better layout preservation
    - Advanced image extraction with native format support
    - Table structure recognition
    - Lightweight and efficient processing
    - Page-by-page processing with layout analysis
    """
    
    def __init__(self, **config):
        self.extract_metadata = config.get('extract_metadata', True)
        self.extract_images = config.get('extract_images', True)
        self.save_images_separately = config.get('save_images_separately', False)
        self.embed_images_as_base64 = config.get('embed_images_as_base64', True)
        self.max_image_size = config.get('max_image_size', (400, 300))
        self.extract_tables = config.get('extract_tables', True)
        self.image_quality = config.get('image_quality', 85)
        self.logger = logging.getLogger(__name__)
        
        super().__init__(**config)
    
    def _setup(self):
        """Setup PyMuPDF converter."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF not available. Install with: pip install pymupdf"
            )
        
        if self.extract_images and not PIL_AVAILABLE:
            self.logger.warning("PIL/Pillow not available. Some image processing features will be limited.")
        
        print("✓ PyMuPDF converter ready!")
        if self.extract_images:
            print("  ✓ Image extraction enabled")
        if self.extract_tables:
            print("  ✓ Table extraction enabled")
    
    def convert(self, pdf_path: str) -> str:
        """
        Convert PDF to Markdown using PyMuPDF with image support.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Markdown content with text and images
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not available")
        
        self.validate_pdf(pdf_path)
        
        # Get file info for logging
        from utils.file_handler import get_file_info
        file_info = get_file_info(pdf_path)
        
        self.logger.info(f"Starting PyMuPDF conversion of {pdf_path} ({file_info['size_mb']:.2f} MB)")
        
        markdown_content = []
        image_counter = 0
        
        # Add header with file info if metadata extraction is enabled
        if self.extract_metadata:
            markdown_content.append(f"# PDF Conversion: {os.path.basename(pdf_path)}")
            markdown_content.append(f"*File size: {file_info['size_mb']:.2f} MB*")
            markdown_content.append("")
        
        try:
            # Open PDF document using PyMuPDF with enhanced error handling
            # for potentially corrupted files
            doc = fitz.open(pdf_path)
            
            # Add metadata if available and requested
            if self.extract_metadata:
                metadata = doc.metadata
                if metadata:
                    markdown_content.append("## Document Information")
                    if metadata.get('title'):
                        markdown_content.append(f"**Title:** {metadata['title']}")
                    if metadata.get('author'):
                        markdown_content.append(f"**Author:** {metadata['author']}")
                    if metadata.get('subject'):
                        markdown_content.append(f"**Subject:** {metadata['subject']}")
                    if metadata.get('creator'):
                        markdown_content.append(f"**Creator:** {metadata['creator']}")
                    if metadata.get('producer'):
                        markdown_content.append(f"**Producer:** {metadata['producer']}")
                    markdown_content.append("")
            
            # Process each page
            for page_num, page in enumerate(doc, 1):
                self.logger.info(f"Processing page {page_num}/{doc.page_count}")
                
                markdown_content.append(f"## Page {page_num}")
                markdown_content.append("")
                
                # Extract images from page if requested
                if self.extract_images:
                    page_images = self._extract_page_images(page, pdf_path, page_num)
                    for img_data in page_images:
                        image_counter += 1
                        img_markdown = self._create_image_markdown(img_data, image_counter)
                        if img_markdown:
                            markdown_content.append(img_markdown)
                            markdown_content.append("")
                
                # Extract text from page using PyMuPDF's advanced text extraction
                text = page.get_text("text")
                if text.strip():
                    # Clean up the text and add it
                    clean_text = self._clean_text(text)
                    markdown_content.append(clean_text)
                    markdown_content.append("")
                
                # Extract tables if enabled
                if self.extract_tables:
                    tables_markdown = self._extract_tables(page, page_num)
                    if tables_markdown:
                        markdown_content.append(tables_markdown)
                        markdown_content.append("")
            
            # Close the document
            doc.close()
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            raise
        
        result = "\n".join(markdown_content)
        
        if image_counter > 0:
            self.logger.info(f"✓ PyMuPDF conversion completed ({image_counter} images extracted)")
        else:
            self.logger.info("✓ PyMuPDF conversion completed")
        
        return result
    
    def _extract_page_images(self, page, pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """Extract images from a PDF page using PyMuPDF's image extraction with enhanced error handling."""
        images = []
        
        try:
            # Check if page is valid
            if not page or not hasattr(page, 'get_images'):
                self.logger.warning(f"Invalid page object on page {page_num}")
                return images
            
            # Try to get images directly using PyMuPDF's image extraction
            try:
                img_list = page.get_images(full=True)
                if not img_list:
                    self.logger.info(f"No images found on page {page_num}")
                    return images
            except Exception as e:
                self.logger.warning(f"Error getting image list on page {page_num}: {e}")
                return images
            
            # Track success rate for diagnostics
            total_images = len(img_list)
            successful_images = 0
            
            for img_index, img_info in enumerate(img_list):
                try:
                    # Validate image info
                    if not img_info or len(img_info) < 1:
                        self.logger.warning(f"Invalid image info for image {img_index} on page {page_num}")
                        continue
                    
                    # Extract image info from the tuple
                    xref = img_info[0]  # image reference number
                    
                    # Get the image data from the PDF
                    base_image = self._get_image_from_xref(page.parent, xref)
                    if base_image:
                        img_data = self._process_image(base_image, pdf_path, page_num, img_index + 1)
                        if img_data:
                            images.append(img_data)
                            successful_images += 1
                
                except Exception as e:
                    self.logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                    continue
            
            # Log extraction statistics
            if total_images > 0:
                success_rate = (successful_images / total_images) * 100
                self.logger.info(f"Page {page_num} image extraction: {successful_images}/{total_images} ({success_rate:.1f}%)")
                    
        except Exception as e:
            self.logger.warning(f"Error processing images on page {page_num}: {e}")
        
        return images
    
    def _get_image_from_xref(self, doc, xref):
        """Get image data from document by reference number with enhanced error handling."""
        if doc is None or xref is None:
            self.logger.warning("Invalid document or xref reference")
            return None
            
        try:
            # Before trying to get the pixmap, validate that the xref points to an image
            if not doc.xref_is_image(xref):
                self.logger.warning(f"XRef {xref} does not point to a valid image")
                return None
                
            # PyMuPDF provides a direct way to get image data by xref
            pix = fitz.Pixmap(doc, xref)
            
            # Validate pixmap before proceeding
            if pix is None or not hasattr(pix, 'n'):
                self.logger.warning(f"Failed to create valid pixmap from xref {xref}")
                return None
                
            # If the pixmap has alpha and is CMYK, we need to convert it
            if pix.n > 4:  # CMYK + alpha
                try:
                    pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                    result = pix_rgb
                    pix = None  # Free the original pixmap
                except Exception as e:
                    self.logger.warning(f"Failed to convert CMYK+alpha pixmap: {e}")
                    # Return original pixmap if conversion fails
                    return pix
                    
            elif pix.n == 4 and hasattr(pix, 'colorspace') and pix.colorspace and pix.colorspace.name != "DeviceRGB":  # CMYK without alpha
                try:
                    pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                    result = pix_rgb
                    pix = None  # Free the original pixmap
                except Exception as e:
                    self.logger.warning(f"Failed to convert CMYK pixmap: {e}")
                    # Return original pixmap if conversion fails
                    return pix
            else:
                result = pix
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Failed to extract image with xref {xref}: {e}")
            return None
    
    def _process_image(self, pixmap, pdf_path: str, page_num: int, img_num: int) -> Optional[Dict[str, Any]]:
        """Process a PyMuPDF pixmap to either PIL Image or bytes with enhanced error handling."""
        try:
            # Comprehensive verification of pixmap validity
            if not pixmap:
                self.logger.warning(f"Null pixmap on page {page_num}")
                return None
                
            # Check for pixmap properties
            if not hasattr(pixmap, 'width') or not hasattr(pixmap, 'height') or not hasattr(pixmap, 'samples_ptr'):
                self.logger.warning(f"Pixmap missing required attributes on page {page_num}")
                return None
                
            # Check for valid dimensions and data
            if pixmap.width <= 0 or pixmap.height <= 0:
                self.logger.warning(f"Invalid pixmap dimensions on page {page_num}: {pixmap.width}x{pixmap.height}")
                return None
                
            if pixmap.samples_ptr == 0:
                self.logger.warning(f"Pixmap has no data pointer on page {page_num}")
                return None
                
            # Check if image is too small to be useful (likely corrupted)
            if pixmap.width < 5 or pixmap.height < 5:
                self.logger.warning(f"Image too small, likely corrupted: {pixmap.width}x{pixmap.height} on page {page_num}")
                return None
                
            # Check if image is unreasonably large (likely corrupted metadata)
            if pixmap.width > 10000 or pixmap.height > 10000:
                self.logger.warning(f"Image unreasonably large, likely corrupted: {pixmap.width}x{pixmap.height} on page {page_num}")
                return None
                
            # Get image properties
            width = pixmap.width
            height = pixmap.height
            
            # Check if we need to resize the image
            needs_resize = self.max_image_size and (width > self.max_image_size[0] or height > self.max_image_size[1])
            
            # Try getting the sample data before processing further
            try:
                # Just check if we can access the sample data - don't store it yet
                test_bytes = pixmap.samples
                if not test_bytes or len(test_bytes) == 0:
                    self.logger.warning(f"Pixmap has empty sample data on page {page_num}")
                    return None
                    
                expected_length = width * height * pixmap.n
                actual_length = len(test_bytes)
                
                # Basic sanity check on data size
                if actual_length < (expected_length * 0.5):  # Allow some compression differences
                    self.logger.warning(f"Pixmap data too small on page {page_num}: expected ~{expected_length} bytes, got {actual_length}")
                    return None
                    
            except Exception as e:
                self.logger.warning(f"Failed to access pixmap sample data on page {page_num}: {e}")
                return None
            
            if needs_resize and PIL_AVAILABLE:
                try:
                    # Convert to PIL Image for resizing
                    img_bytes = pixmap.tobytes()
                    img_format = "png" if pixmap.alpha else "jpeg"
                    
                    from PIL import Image
                    from io import BytesIO
                    
                    # Validate byte data length before creating PIL image
                    expected_bytes = width * height * (4 if pixmap.alpha else 3)
                    if len(img_bytes) < expected_bytes * 0.8:  # Allow some tolerance
                        self.logger.warning(f"Insufficient image data for PIL conversion on page {page_num}")
                        return None
                    
                    try:
                        # Convert pixmap data to PIL Image with error handling
                        if img_format == "png":
                            pil_image = Image.frombytes("RGBA", (width, height), img_bytes)
                        else:
                            pil_image = Image.frombytes("RGB", (width, height), img_bytes)
                    except Exception as pil_error:
                        self.logger.warning(f"Failed to create PIL image on page {page_num}: {pil_error}")
                        # Try the non-PIL path instead
                        needs_resize = False
                        raise Exception("Falling back to direct pixmap")
                    
                    # Resize the image
                    pil_image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                    
                    # Save to buffer
                    img_buffer = BytesIO()
                    # Only apply quality to JPEG images
                    if img_format.upper() == "JPEG":
                        pil_image.save(img_buffer, format=img_format.upper(), quality=self.image_quality)
                    else:
                        pil_image.save(img_buffer, format=img_format.upper())
                    img_buffer.seek(0)
                    
                    # Create result data
                    return self._create_image_result(img_buffer.getvalue(), img_format, pdf_path, 
                                                  page_num, img_num, width, height, 
                                                  pil_image.width, pil_image.height)
                except Exception as e:
                    self.logger.info(f"PIL processing failed, falling back to direct method: {e}")
                    # Continue with non-PIL path
                    needs_resize = False
            
            # Direct pixmap path (no PIL or PIL failed)
            if not needs_resize or not PIL_AVAILABLE:
                # Use pixmap directly without resizing
                img_format = "png" if pixmap.alpha else "jpeg"
                
                # Try different approaches to get image data safely
                try:
                    # First try: Use the appropriate format with quality parameter
                    if img_format == "jpeg":
                        try:
                            # Try with quality parameter first
                            img_data = pixmap.tobytes("jpeg", quality=self.image_quality)
                        except (TypeError, AttributeError):
                            # Older versions of PyMuPDF don't support the quality parameter
                            self.logger.info("Using older PyMuPDF version without quality support")
                            img_data = pixmap.tobytes("jpeg")
                    else:
                        img_data = pixmap.tobytes("png")
                        
                    # Verify we got actual data
                    if not img_data or len(img_data) < 100:  # Minimum viable image size
                        raise ValueError("Generated image data is too small")
                        
                except Exception as e:
                    # Second try: Use format without parameters
                    self.logger.warning(f"First tobytes attempt failed: {e}, trying without format")
                    try:
                        img_data = pixmap.tobytes(img_format)
                        
                        # Verify we got actual data
                        if not img_data or len(img_data) < 100:
                            raise ValueError("Generated image data is too small")
                            
                    except Exception as e2:
                        # Last resort: raw bytes
                        self.logger.warning(f"Second tobytes attempt failed: {e2}, using raw samples")
                        try:
                            # Last resort: Use raw samples as PNG
                            img_data = pixmap.tobytes()
                            img_format = "png"  # Default to PNG for raw data
                            
                            # Final validation
                            if not img_data or len(img_data) < 100:
                                self.logger.warning("All image data extraction methods failed")
                                return None
                                
                        except Exception as e3:
                            self.logger.warning(f"All tobytes attempts failed: {e3}")
                            return None
                
                # Create result data
                return self._create_image_result(img_data, img_format, pdf_path, 
                                              page_num, img_num, width, height, width, height)
                
        except Exception as e:
            self.logger.warning(f"Failed to process image on page {page_num}: {e}")
            return None
    
    def _create_image_result(self, img_data: bytes, img_format: str, pdf_path: str, 
                           page_num: int, img_num: int, orig_width: int, orig_height: int,
                           width: int, height: int) -> Dict[str, Any]:
        """Create image result dictionary from image data."""
        # Create filename
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        filename = f"{pdf_name}_page{page_num}_img{img_num}.{img_format}"
        
        result = {
            'filename': filename,
            'format': img_format.upper(),
            'size': (width, height),
            'original_size': (orig_width, orig_height),
            'page': page_num,
            'number': img_num
        }
        
        # Save separately if requested
        if self.save_images_separately:
            try:
                img_dir = os.path.join(os.path.dirname(pdf_path), 'extracted_images')
                os.makedirs(img_dir, exist_ok=True)
                img_path = os.path.join(img_dir, filename)
                
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                result['file_path'] = img_path
            except Exception as save_error:
                self.logger.warning(f"Failed to save image file: {save_error}")
        
        # Embed as base64 if requested
        if self.embed_images_as_base64:
            try:
                b64_data = base64.b64encode(img_data).decode('utf-8')
                mime_type = f"image/{img_format}"
                result['base64'] = f"data:{mime_type};base64,{b64_data}"
            except Exception as b64_error:
                self.logger.warning(f"Failed to create base64 for image: {b64_error}")
        
        return result
    
    def _extract_tables(self, page, page_num: int) -> str:
        """Extract tables from the page and convert to Markdown format."""
        tables_markdown = []
        
        try:
            # PyMuPDF's table extraction is based on finding rectangular areas that might be tables
            # This is a simplified approach - production code would use more sophisticated detection
            
            # Check if the page has tables (using a simple heuristic based on text structure)
            text_blocks = page.get_text("dict")["blocks"]
            
            for block in text_blocks:
                # Check if this block might be a table (contains multiple lines with similar structure)
                if "lines" in block and len(block.get("lines", [])) > 2:
                    lines = block.get("lines", [])
                    
                    # Simple heuristic: if multiple lines have similar number of spans, it might be a table
                    span_counts = [len(line.get("spans", [])) for line in lines]
                    most_common_count = max(set(span_counts), key=span_counts.count)
                    
                    # If most lines have the same number of spans, and it's more than 1, it could be a table
                    if most_common_count > 1 and span_counts.count(most_common_count) / len(span_counts) > 0.5:
                        # Extract table data
                        table_data = []
                        for line in lines:
                            row = []
                            for span in line.get("spans", []):
                                row.append(span.get("text", "").strip())
                            if row:  # Skip empty rows
                                table_data.append(row)
                        
                        # Convert table to markdown
                        if len(table_data) > 1:  # At least 2 rows (header + data)
                            table_md = self._table_to_markdown(table_data)
                            tables_markdown.append(table_md)
            
            if tables_markdown:
                return "\n\n".join(tables_markdown)
            else:
                return ""
                
        except Exception as e:
            self.logger.warning(f"Failed to extract tables from page {page_num}: {e}")
            return ""
    
    def _table_to_markdown(self, table_data: List[List[str]]) -> str:
        """Convert a table represented as a 2D array to Markdown format."""
        if not table_data or not table_data[0]:
            return ""
        
        # Create header row
        header = table_data[0]
        markdown_lines = ["| " + " | ".join(header) + " |"]
        
        # Create separator row
        separator = ["| " + " | ".join(["---"] * len(header)) + " |"]
        
        # Create data rows
        data_rows = []
        for row in table_data[1:]:
            # Ensure the row has the same number of columns as the header
            padded_row = row + [""] * (len(header) - len(row))
            data_rows.append("| " + " | ".join(padded_row[:len(header)]) + " |")
        
        return "\n".join(markdown_lines + separator + data_rows)
    
    def _create_image_markdown(self, img_data: Dict[str, Any], img_counter: int) -> str:
        """Create markdown for an extracted image."""
        if not img_data:
            return ""
        
        try:
            alt_text = f"Image {img_counter} from page {img_data['page']}"
            size_info = f"{img_data['size'][0]}x{img_data['size'][1]}"
            
            if 'base64' in img_data:
                # Embed as base64 data URL
                markdown = f"![{alt_text}]({img_data['base64']})\n"
                markdown += f"*{alt_text} ({size_info})*"
                return markdown
            elif 'file_path' in img_data:
                # Reference saved file
                rel_path = os.path.relpath(img_data['file_path'])
                markdown = f"![{alt_text}]({rel_path})\n"
                markdown += f"*{alt_text} ({size_info})*"
                return markdown
            else:
                # Just show info about the image
                return f"*[Image {img_counter}: {img_data['filename']} ({size_info})]*"
                
        except Exception as e:
            self.logger.warning(f"Failed to create image markdown: {e}")
            return f"*[Image {img_counter} extraction failed]*"
    
    def _clean_text(self, text: str) -> str:
        """Clean and format extracted text with improved character handling."""
        # Fix common character encoding issues from PDF extraction
        text = self._fix_character_encoding(text)
        
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Improve paragraph detection
        cleaned_lines = []
        for i, line in enumerate(lines):
            # If this line ends with a period, question mark, or exclamation
            # and the next line starts with a capital letter, add extra spacing
            if (i < len(lines) - 1 and 
                line.endswith(('.', '!', '?', ':')) and 
                lines[i + 1] and lines[i + 1][0].isupper()):
                cleaned_lines.append(line)
                cleaned_lines.append("")  # Add paragraph break
            else:
                cleaned_lines.append(line)
        
        # Join lines with proper spacing
        result = '\n'.join(cleaned_lines)
        
        # Clean up excessive newlines
        import re
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result
    
    def _fix_character_encoding(self, text: str) -> str:
        """Fix common character encoding issues from PDF text extraction."""
        # Remove null characters that often appear in PDF text extraction
        text = text.replace('\x00', '')
        
        # Fix common ligature and encoding issues
        ligature_fixes = {
            # Common ligature issues
            'ﬁ': 'fi',  # fi ligature
            'ﬂ': 'fl',  # fl ligature
            'ﬀ': 'ff',  # ff ligature
            'ﬃ': 'ffi', # ffi ligature
            'ﬄ': 'ffl', # ffl ligature
            'ﬆ': 'st',  # st ligature
            
            # Unicode replacements
            '"': '"',  # Left double quotation mark
            '"': '"',  # Right double quotation mark
            ''': "'",  # Left single quotation mark
            ''': "'",  # Right single quotation mark
            '—': '--', # Em dash
            '–': '-',  # En dash
            '…': '...', # Horizontal ellipsis
        }
        
        # Apply fixes
        for broken, fixed in ligature_fixes.items():
            text = text.replace(broken, fixed)
        
        # Fix multiple spaces that might result from character removal
        import re
        text = re.sub(r' +', ' ', text)
        
        return text
    
    def get_converter_info(self) -> Dict[str, Any]:
        """Get information about the PyMuPDF converter."""
        features = [
            'Fast text extraction',
            'Better layout preservation',
            'Advanced image handling',
            'Metadata extraction',
            'Page-by-page processing',
            'Improved text cleaning'
        ]
        
        limitations = [
            'Requires PyMuPDF library',
            'Limited OCR support'
        ]
        
        if self.extract_images:
            features.append('Native image extraction')
            features.append('Image resizing and optimization')
        
        if self.extract_tables:
            features.append('Basic table detection and formatting')
        
        return {
            'name': 'PyMuPDF Converter',
            'type': 'text_and_image_extraction',
            'features': features,
            'limitations': limitations,
            'config': {
                'extract_metadata': self.extract_metadata,
                'extract_images': self.extract_images,
                'save_images_separately': self.save_images_separately,
                'embed_images_as_base64': self.embed_images_as_base64,
                'max_image_size': self.max_image_size,
                'extract_tables': self.extract_tables,
                'image_quality': self.image_quality
            },
            'output_format': 'markdown_with_images_and_tables' if self.extract_images else 'simple_markdown',
            'speed': 'fast',
            'available': PYMUPDF_AVAILABLE,
            'pil_available': PIL_AVAILABLE
        }
