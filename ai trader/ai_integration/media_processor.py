# Media Processor Module
# This module handles processing of different media types for AI analysis

import os
import base64
import logging
from typing import Dict, Any, Optional, List, Union
from PIL import Image
import io

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediaProcessor:
    """Process different types of media for AI analysis.
    
    This class provides methods to process images, videos, and other files
    for use with AI models like Gemini 2.5.
    """
    
    def __init__(self, temp_dir: str = './data/temp'):
        """Initialize the media processor.
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process an image for AI analysis.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with processed image data
        """
        try:
            # Validate image file
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return {"error": f"Image file not found: {image_path}"}
            
            # Open and validate image
            try:
                img = Image.open(image_path)
                img_format = img.format
                width, height = img.size
            except Exception as e:
                logger.error(f"Error opening image: {e}")
                return {"error": f"Error opening image: {e}"}
            
            # Get file size
            file_size = os.path.getsize(image_path)
            
            # Encode image to base64 for API transmission
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Return processed data
            return {
                "file_path": image_path,
                "format": img_format,
                "width": width,
                "height": height,
                "size_bytes": file_size,
                "encoded_data": encoded_image,
                "mime_type": f"image/{img_format.lower() if img_format else 'jpeg'}"
            }
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {"error": str(e)}
    
    def process_video(self, video_path: str, extract_frames: bool = True, frame_count: int = 5) -> Dict[str, Any]:
        """Process a video for AI analysis.
        
        Args:
            video_path: Path to the video file
            extract_frames: Whether to extract frames from the video
            frame_count: Number of frames to extract
            
        Returns:
            Dictionary with processed video data
        """
        try:
            # Validate video file
            if not os.path.exists(video_path):
                logger.error(f"Video file not found: {video_path}")
                return {"error": f"Video file not found: {video_path}"}
            
            # Get file size
            file_size = os.path.getsize(video_path)
            
            # Get file extension
            _, ext = os.path.splitext(video_path)
            ext = ext.lstrip('.')
            
            result = {
                "file_path": video_path,
                "format": ext,
                "size_bytes": file_size,
                "mime_type": f"video/{ext}"
            }
            
            # Extract frames if requested
            # Note: This requires additional libraries like OpenCV
            # This is a placeholder for future implementation
            if extract_frames:
                result["frames_extracted"] = False
                result["frames"] = []
                logger.warning("Video frame extraction not implemented yet")
            
            return result
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            return {"error": str(e)}
    
    def process_text_file(self, file_path: str, max_size: int = 1000000) -> Dict[str, Any]:
        """Process a text file for AI analysis.
        
        Args:
            file_path: Path to the text file
            max_size: Maximum file size to process (in bytes)
            
        Returns:
            Dictionary with processed text data
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {"error": f"File not found: {file_path}"}
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                logger.warning(f"File too large: {file_path} ({file_size} bytes)")
                return {"error": f"File too large: {file_size} bytes (max {max_size} bytes)"}
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"Error reading file: {e}")
                    return {"error": f"Error reading file: {e}"}
            
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lstrip('.')
            
            # Return processed data
            return {
                "file_path": file_path,
                "format": ext,
                "size_bytes": file_size,
                "content": content,
                "mime_type": f"text/{ext if ext else 'plain'}"
            }
        except Exception as e:
            logger.error(f"Error processing text file: {e}")
            return {"error": str(e)}
    
    def process_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """Process a file for AI analysis based on its type.
        
        Args:
            file_path: Path to the file
            file_type: Type of file ('image', 'video', 'text'). If None, will try to infer from extension.
            
        Returns:
            Dictionary with processed file data
        """
        if not file_type:
            # Try to infer file type from extension
            extension = os.path.splitext(file_path)[1].lower()
            if extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                file_type = "image"
            elif extension in [".mp4", ".avi", ".mov", ".mkv"]:
                file_type = "video"
            elif extension in [".txt", ".csv", ".json", ".md", ".py", ".js", ".html", ".css"]:
                file_type = "text"
            else:
                logger.warning(f"Could not determine file type for {file_path}. Treating as text.")
                file_type = "text"
        
        if file_type == "image":
            return self.process_image(file_path)
        elif file_type == "video":
            return self.process_video(file_path)
        elif file_type == "text":
            return self.process_text_file(file_path)
        else:
            return {"error": f"Unsupported file type: {file_type}"}
    
    def batch_process(self, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Process multiple files in batch.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary with processed results grouped by file type
        """
        results = {
            "images": [],
            "videos": [],
            "text_files": [],
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                processed = self.process_file(file_path)
                
                if "error" in processed:
                    results["errors"].append({
                        "file_path": file_path,
                        "error": processed["error"]
                    })
                    continue
                
                # Add to appropriate category
                if processed.get("mime_type", "").startswith("image/"):
                    results["images"].append(processed)
                elif processed.get("mime_type", "").startswith("video/"):
                    results["videos"].append(processed)
                else:
                    results["text_files"].append(processed)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                results["errors"].append({
                    "file_path": file_path,
                    "error": str(e)
                })
        
        return results