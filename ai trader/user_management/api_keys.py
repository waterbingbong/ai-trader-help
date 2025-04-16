# API Keys Management Module
# This module handles storage and retrieval of user API keys

import json
import os
from pathlib import Path
import logging
from typing import Dict, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory for storing API keys
API_KEYS_DIR = Path(__file__).parent / 'api_keys'
API_KEYS_DIR.mkdir(exist_ok=True)


class APIKeyManager:
    """Manages API keys for users."""
    
    @staticmethod
    def save_api_key(user_id: str, service: str, api_key: str) -> bool:
        """Save an API key for a user.
        
        Args:
            user_id: The user ID
            service: The service name (e.g., 'gemini')
            api_key: The API key to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create user-specific API keys file
            api_key_file = API_KEYS_DIR / f"{user_id}_{service}.json"
            
            # Save the API key
            with open(api_key_file, 'w') as f:
                json.dump({f"{service}_api_key": api_key}, f)
            
            logger.info(f"API key for {service} saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return False
    
    @staticmethod
    def get_api_key(user_id: str, service: str) -> Optional[str]:
        """Get an API key for a user.
        
        Args:
            user_id: The user ID
            service: The service name (e.g., 'gemini')
            
        Returns:
            The API key if found, None otherwise
        """
        try:
            # Get user-specific API keys file
            api_key_file = API_KEYS_DIR / f"{user_id}_{service}.json"
            
            # Check if file exists
            if not api_key_file.exists():
                return None
            
            # Load the API key
            with open(api_key_file, 'r') as f:
                data = json.load(f)
                return data.get(f"{service}_api_key")
        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None
    
    @staticmethod
    def delete_api_key(user_id: str, service: str) -> bool:
        """Delete an API key for a user.
        
        Args:
            user_id: The user ID
            service: The service name (e.g., 'gemini')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get user-specific API keys file
            api_key_file = API_KEYS_DIR / f"{user_id}_{service}.json"
            
            # Check if file exists
            if not api_key_file.exists():
                return True
            
            # Delete the file
            api_key_file.unlink()
            
            logger.info(f"API key for {service} deleted for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False
    
    @staticmethod
    def save_trading_context(user_id: str, context_data: Dict[str, Any]) -> bool:
        """Save trading context data for a user.
        
        Args:
            user_id: The user ID
            context_data: Dictionary with context data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create user-specific context file
            context_file = API_KEYS_DIR / f"{user_id}_context.json"
            
            # Save the context data
            with open(context_file, 'w') as f:
                json.dump(context_data, f)
            
            logger.info(f"Trading context saved for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving trading context: {e}")
            return False
    
    @staticmethod
    def get_trading_context(user_id: str) -> Optional[Dict[str, Any]]:
        """Get trading context data for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with context data if found, None otherwise
        """
        try:
            # Get user-specific context file
            context_file = API_KEYS_DIR / f"{user_id}_context.json"
            
            # Check if file exists
            if not context_file.exists():
                return None
            
            # Load the context data
            with open(context_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting trading context: {e}")
            return None