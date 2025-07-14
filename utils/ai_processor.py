#!/usr/bin/env python3
"""
AI Processing Module
Handles OpenRouter API integration for PDF content analysis.
"""

import os


class AIProcessor:
    """Handles AI processing via OpenRouter API."""
    
    def __init__(self):
        """Initialize AI processor with environment configuration."""
        self.api_key = os.getenv("OPENROUTER_KEY")
        self.main_model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")
        self.backup_model = os.getenv("OPENROUTER_BACKUP_MODEL", "google/gemma-2-9b-it:free")
        self.timeout = int(os.getenv("OPENROUTER_TIMEOUT", "30000")) / 1000  # Convert to seconds
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "1000"))
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        if not self.api_key:
            raise ValueError("OPENROUTER_KEY not found in environment variables")
    
    def is_available(self):
        """Check if AI processing is available."""
        return bool(self.api_key)
    
    def process_content(self, content, use_backup=False, custom_prompt=None):
        """
        Process content with OpenRouter AI.
        
        Args:
            content: Content to process (markdown or json)
            use_backup: Whether to use backup model instead of main model
            custom_prompt: Optional custom prompt to use
            
        Returns:
            str: AI-processed response with original content appended
            
        Raises:
            ImportError: If openai library not installed
            Exception: If API call fails
        """
        try:
            # Import OpenAI client for OpenRouter
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai library not installed. Run: pip install openai>=1.0.0")
        
        # Select model
        model = self.backup_model if use_backup else self.main_model
        
        # Initialize OpenRouter client
        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Prepare the prompt
        if custom_prompt:
            prompt = f"{custom_prompt}\n\n{content}"
        else:
            prompt = f"Analyze this PDF content and provide insights:\n\n{content}"
        
        # Make API call to OpenRouter
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )
        
        # Extract and return the response
        ai_response = response.choices[0].message.content
        return f"# AI Analysis ({model})\n\n{ai_response}\n\n---\n\n{content}"
    
    def process_with_fallback(self, content, custom_prompt=None):
        """
        Process content with automatic fallback to backup model on failure.
        
        Args:
            content: Content to process
            custom_prompt: Optional custom prompt
            
        Returns:
            str: AI-processed response or original content if all models fail
        """
        if not self.is_available():
            print("❌ Error: OPENROUTER_KEY not found in environment variables")
            return content
        
        try:
            # Try main model first
            return self.process_content(content, use_backup=False, custom_prompt=custom_prompt)
            
        except ImportError as e:
            print(f"❌ Error: {e}")
            return content
            
        except Exception as e:
            print(f"❌ AI processing failed with main model: {e}")
            
            try:
                # Try backup model
                print("🔄 Trying backup model...")
                return self.process_content(content, use_backup=True, custom_prompt=custom_prompt)
                
            except Exception as backup_e:
                print(f"❌ Backup model also failed: {backup_e}")
                return content
    
    def get_model_info(self, use_backup=False):
        """Get information about the current model configuration."""
        model = self.backup_model if use_backup else self.main_model
        return {
            "model": model,
            "type": "backup" if use_backup else "main",
            "timeout": self.timeout,
            "max_tokens": self.max_tokens,
            "available": self.is_available()
        }


def create_ai_processor():
    """Factory function to create and return an AIProcessor instance."""
    try:
        return AIProcessor()
    except ValueError as e:
        print(f"Warning: AI processor not available - {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    # Test the AI processor
    processor = create_ai_processor()
    
    if processor and processor.is_available():
        print("✅ AI Processor initialized successfully")
        print(f"📊 Main model: {processor.main_model}")
        print(f"🔄 Backup model: {processor.backup_model}")
        print(f"⏱️  Timeout: {processor.timeout}s")
        print(f"🎯 Max tokens: {processor.max_tokens}")
        
        # Test with sample content
        test_content = """
        # PDF Extraction: test.pdf
        
        ## Extracted Text
        Sample PDF content for testing AI processing.
        """
        
        print("\n🧪 Testing AI processing...")
        result = processor.process_with_fallback(test_content, "Provide a brief summary:")
        print("✅ AI processing test completed")
        
    else:
        print("❌ AI Processor not available - check environment variables")
