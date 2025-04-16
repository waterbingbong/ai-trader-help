# Gemini Integration Module
# This module integrates Google's Gemini 2.5 AI model into the trading assistant

import os
import base64
import requests
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiIntegration:
    """Integration with Google's Gemini 2.5 AI model.
    
    This class provides methods to interact with the Gemini API for enhancing
    trading signals and analysis through AI-powered insights.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize the Gemini integration.
        
        Args:
            api_key: The Gemini API key. If None, will try to load from environment variable.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("No Gemini API key provided. Please set it using set_api_key() method or GEMINI_API_KEY environment variable.")
        
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.vision_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"
        self.knowledge_base = []
    
    def set_api_key(self, api_key: str) -> None:
        """Set the Gemini API key.
        
        Args:
            api_key: The Gemini API key
        """
        self.api_key = api_key
        logger.info("API key has been set successfully.")
    
    def _encode_image(self, image_path: str) -> str:
        """Encode an image to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_text(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Analyze text using Gemini model.
        
        Args:
            text: The text to analyze
            context: Optional context to provide additional information
            
        Returns:
            Dictionary containing the analysis results
        """
        if not self.api_key:
            logger.error("API key is not set. Please set it using set_api_key() method.")
            return {"error": "API key not set"}
        
        prompt = text
        if context:
            prompt = f"Context: {context}\n\nAnalyze the following: {text}"
        
        # Add knowledge base information if available
        if self.knowledge_base:
            kb_context = "\n\n".join([f"Knowledge item {i+1}: {item}" for i, item in enumerate(self.knowledge_base)])
            prompt = f"{prompt}\n\nAdditional knowledge: {kb_context}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        params = {"key": self.api_key}
        
        try:
            response = requests.post(self.base_url, json=payload, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {"error": str(e)}
    
    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Analyze an image using Gemini Vision model.
        
        Args:
            image_path: Path to the image file
            prompt: Text prompt describing what to analyze in the image
            
        Returns:
            Dictionary containing the analysis results
        """
        if not self.api_key:
            logger.error("API key is not set. Please set it using set_api_key() method.")
            return {"error": "API key not set"}
        
        try:
            image_data = self._encode_image(image_path)
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }]
            }
            
            params = {"key": self.api_key}
            
            response = requests.post(self.vision_url, json=payload, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {"error": str(e)}
    
    def analyze_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """Analyze a file using the appropriate Gemini model.
        
        Args:
            file_path: Path to the file
            file_type: Type of file ('image', 'text', 'video'). If None, will try to infer from extension.
            
        Returns:
            Dictionary containing the analysis results
        """
        if not file_type:
            # Try to infer file type from extension
            extension = os.path.splitext(file_path)[1].lower()
            if extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                file_type = "image"
            elif extension in [".txt", ".csv", ".json", ".md"]:
                file_type = "text"
            elif extension in [".mp4", ".avi", ".mov", ".mkv"]:
                file_type = "video"
            else:
                logger.warning(f"Could not determine file type for {file_path}. Treating as text.")
                file_type = "text"
        
        if file_type == "image":
            return self.analyze_image(file_path, "Analyze this chart or image for trading insights and patterns.")
        elif file_type == "text":
            with open(file_path, "r") as f:
                content = f.read()
            return self.analyze_text(content, "This is a file with trading-related information.")
        elif file_type == "video":
            # For videos, we'd need to extract frames or use a different approach
            # This is a placeholder for future implementation
            return {"error": "Video analysis not yet implemented"}
        else:
            return {"error": f"Unsupported file type: {file_type}"}
    
    def add_to_knowledge_base(self, content: str) -> None:
        """Add content to the knowledge base for future reference.
        
        Args:
            content: The content to add to the knowledge base
        """
        self.knowledge_base.append(content)
        logger.info(f"Added content to knowledge base. Current size: {len(self.knowledge_base)} items")
    
    def clear_knowledge_base(self) -> None:
        """Clear the knowledge base."""
        self.knowledge_base = []
        logger.info("Knowledge base cleared")
    
    def get_trading_insights(self, symbol: str, data: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """Get AI-powered trading insights for a specific symbol.
        
        Args:
            symbol: The trading symbol (e.g., 'AAPL')
            data: Dictionary containing relevant trading data
            context: Optional context information
            
        Returns:
            Dictionary containing trading insights
        """
        # Prepare the prompt with symbol and data
        prompt = f"Provide trading insights for {symbol} based on the following data:\n"
        prompt += json.dumps(data, indent=2)
        
        if context:
            prompt += f"\n\nAdditional context: {context}"
        
        # Get analysis from Gemini
        analysis = self.analyze_text(prompt)
        
        # Process the response to extract structured insights
        # This is a simplified version - in a real implementation, you'd parse the response more carefully
        try:
            if "error" in analysis:
                return {"error": analysis["error"]}
            
            # Extract the text from the response
            if "candidates" in analysis and len(analysis["candidates"]) > 0:
                content = analysis["candidates"][0]["content"]
                if "parts" in content and len(content["parts"]) > 0:
                    text = content["parts"][0]["text"]
                    
                    # Return structured insights
                    return {
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat(),
                        "insights": text,
                        "source": "gemini-2.5"
                    }
            
            return {"error": "Could not extract insights from Gemini response", "raw_response": analysis}
        except Exception as e:
            logger.error(f"Error processing Gemini response: {e}")
            return {"error": str(e), "raw_response": analysis}