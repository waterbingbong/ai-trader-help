# Gemini Integration Manager Module
# This module manages Gemini API integration with user-specific API keys

import os
import sys
from pathlib import Path
import logging
from typing import Optional, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import project modules
from ai_integration.gemini_integration import GeminiIntegration
from user_management.api_keys import APIKeyManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeminiIntegrationManager:
    """Manager for Gemini API integration with user-specific API keys."""
    
    def __init__(self):
        """Initialize the Gemini integration manager."""
        self.default_api_key = os.environ.get("GEMINI_API_KEY")
        self.integrations = {}
        self.trading_contexts = {}
    
    def get_integration(self, user_id: str) -> GeminiIntegration:
        """Get a Gemini integration instance for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            GeminiIntegration instance with the user's API key
        """
        # Check if we already have an integration for this user
        if user_id in self.integrations:
            return self.integrations[user_id]
        
        # Get the user's API key
        api_key = APIKeyManager.get_api_key(user_id, "gemini")
        
        # If no user-specific API key, use the default
        if not api_key:
            api_key = self.default_api_key
            logger.info(f"Using default API key for user {user_id}")
        else:
            logger.info(f"Using user-specific API key for user {user_id}")
        
        # Create a new integration instance
        integration = GeminiIntegration(api_key=api_key)
        
        # Cache the integration
        self.integrations[user_id] = integration
        
        return integration
    
    def update_trading_context(self, user_id: str, trading_pair: str) -> bool:
        """Update the trading context for a user.
        
        Args:
            user_id: The user ID
            trading_pair: The trading pair (e.g., 'BTC-USD')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save the trading context
            context_data = {"trading_pair": trading_pair}
            success = APIKeyManager.save_trading_context(user_id, context_data)
            
            if success:
                # Update the cached context
                self.trading_contexts[user_id] = context_data
                logger.info(f"Trading context updated for user {user_id}: {trading_pair}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating trading context: {e}")
            return False
    
    def get_trading_context(self, user_id: str) -> Dict[str, Any]:
        """Get the trading context for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Dictionary with trading context data
        """
        # Check if we have cached context
        if user_id in self.trading_contexts:
            return self.trading_contexts[user_id]
        
        # Get the context from storage
        context = APIKeyManager.get_trading_context(user_id)
        
        # If no context, return empty dict
        if not context:
            return {}
        
        # Cache the context
        self.trading_contexts[user_id] = context
        
        return context
    
    def analyze_with_context(self, user_id: str, text: str) -> Dict[str, Any]:
        """Analyze text with user's trading context.
        
        Args:
            user_id: The user ID
            text: The text to analyze
            
        Returns:
            Analysis results
        """
        # Get the user's integration
        integration = self.get_integration(user_id)
        
        # Get the user's trading context
        context = self.get_trading_context(user_id)
        trading_pair = context.get("trading_pair", "")
        
        # Create context string
        context_str = ""
        if trading_pair:
            context_str = f"Trading Pair: {trading_pair}\n"
        
        # Analyze with context
        return integration.analyze_text(text, context=context_str)


# Singleton instance
gemini_manager = GeminiIntegrationManager()