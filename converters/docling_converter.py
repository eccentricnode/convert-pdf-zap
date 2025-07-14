"""
Docling-based PDF converter.
Extracted from main.py - provides AI-powered PDF to Markdown conversion.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

from .base_converter import BaseConverter

# Docling imports
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.document_converter import DocumentConverter
from docling_core.types.doc.base import ImageRefMode
import docling.utils.model_downloader

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption


class DoclingConverter(BaseConverter):
    """
    Docling-based PDF converter with AI-powered document understanding.
    
    Features:
    - AI model-based text extraction
    - Image extraction and embedding
    - Layout preservation
    - Table detection
    """
    
    def __init__(self, **config):
        # Set default configuration
        self.image_resolution_scale = config.get('image_resolution_scale', 0.2)
        self.num_threads = config.get('num_threads', 8)
        self.models_path = config.get('models_path', os.path.expanduser("~/.cache/docling/models"))
        self.do_ocr = config.get('do_ocr', False)
        self.generate_page_images = config.get('generate_page_images', True)
        self.generate_picture_images = config.get('generate_picture_images', True)
        
        self.converter = None
        self.logger = logging.getLogger(__name__)
        
        super().__init__(**config)
    
    def _setup(self):
        """Setup Docling converter - download models and initialize converter."""
        print("Setting up Docling converter...")
        
        # Step 1: Download models
        self._download_models()
        
        # Step 2: Create pipeline options
        pipeline_options = self._create_pipeline_options()
        
        # Step 3: Create converter
        self.converter = self._create_document_converter(pipeline_options)
        
        print("✓ Docling converter ready!")
    
    def _download_models(self) -> bool:
        """Download required AI models."""
        print("Downloading required models...")
        try:
            docling.utils.model_downloader.download_models()
            print("✓ Models downloaded successfully!")
            return True
        except Exception as e:
            print(f"✗ Error downloading models: {e}")
            print("Trying to continue anyway...")
            return False
    
    def _create_pipeline_options(self) -> PdfPipelineOptions:
        """Create pipeline options with current configuration."""
        accelerator_options = AcceleratorOptions(
            num_threads=self.num_threads, 
            device=AcceleratorDevice.CPU
        )
        
        pipeline_options = PdfPipelineOptions()
        pipeline_options.accelerator_options = accelerator_options
        pipeline_options.do_ocr = self.do_ocr
        pipeline_options.images_scale = self.image_resolution_scale
        pipeline_options.generate_page_images = self.generate_page_images
        pipeline_options.generate_picture_images = self.generate_picture_images
        
        # Use prefetched models if path exists
        if self.models_path and os.path.exists(self.models_path):
            pipeline_options.artifacts_path = self.models_path
            print(f"✓ Using prefetched models from: {self.models_path}")
        
        return pipeline_options
    
    def _create_document_converter(self, pipeline_options: PdfPipelineOptions) -> DocumentConverter:
        """Create the Docling DocumentConverter."""
        try:
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            print("✓ DocumentConverter initialized successfully!")
            return converter
        except Exception as e:
            print(f"✗ Error creating DocumentConverter: {e}")
            raise
    
    def convert(self, pdf_path: str) -> str:
        """
        Convert PDF to Markdown using Docling.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Markdown content with embedded images
        """
        if not self.converter:
            raise RuntimeError("Converter not initialized. Call _setup() first.")
        
        self.validate_pdf(pdf_path)
        
        # Get file info for logging
        from utils.file_handler import get_file_info
        file_info = get_file_info(pdf_path)
        
        self.logger.info(f"Starting Docling conversion of {pdf_path} ({file_info['size_mb']:.2f} MB)")
        
        # Convert PDF
        result = self.converter.convert(pdf_path)
        self.logger.info("✓ PDF converted to document object")
        
        # Export to markdown
        markdown_content = result.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)
        self.logger.info("✓ Document exported to markdown")
        
        return markdown_content
    
    def get_converter_info(self) -> Dict[str, Any]:
        """Get information about the Docling converter."""
        return {
            'name': 'Docling Converter',
            'type': 'ai_powered',
            'features': [
                'AI-based text extraction',
                'Image extraction and embedding',
                'Layout preservation', 
                'Table detection',
                'OCR support (optional)'
            ],
            'config': {
                'image_resolution_scale': self.image_resolution_scale,
                'num_threads': self.num_threads,
                'models_path': self.models_path,
                'do_ocr': self.do_ocr,
                'generate_page_images': self.generate_page_images,
                'generate_picture_images': self.generate_picture_images
            },
            'output_format': 'markdown_with_embedded_images',
            'speed': 'slow_but_thorough'
        }
