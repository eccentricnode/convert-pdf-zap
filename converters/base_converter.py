"""
Abstract base class for PDF converters.
Defines the interface that all converters must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseConverter(ABC):
    """
    Abstract base class for PDF to Markdown converters.
    
    All converters must implement the convert method and provide
    configuration options.
    """
    
    def __init__(self, **config):
        """
        Initialize the converter with configuration options.
        
        Args:
            **config: Configuration options specific to each converter
        """
        self.config = config
        self._setup()
    
    @abstractmethod
    def _setup(self):
        """
        Setup the converter (download models, initialize libraries, etc.).
        This method must be implemented by each converter.
        """
        pass
    
    @abstractmethod
    def convert(self, pdf_path: str) -> str:
        """
        Convert a PDF file to Markdown format.
        
        Args:
            pdf_path: Path to the PDF file to convert
            
        Returns:
            str: Markdown content
            
        Raises:
            Exception: If conversion fails
        """
        pass
    
    @abstractmethod
    def get_converter_info(self) -> Dict[str, Any]:
        """
        Get information about this converter.
        
        Returns:
            dict: Converter information (name, version, capabilities, etc.)
        """
        pass
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Basic PDF validation. Can be overridden by specific converters.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: True if valid
        """
        from utils.file_handler import validate_pdf_file
        return validate_pdf_file(pdf_path)
