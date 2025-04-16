# Knowledge Base Module
# This module manages the knowledge base for AI-enhanced trading insights

import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeBase:
    """Knowledge base for storing and retrieving trading-related information.
    
    This class provides methods to manage a knowledge base of trading information,
    including market data, news, analysis, and user-provided insights.
    """
    
    def __init__(self, storage_dir: str = './data/knowledge_base'):
        """Initialize the knowledge base.
        
        Args:
            storage_dir: Directory to store knowledge base files
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize knowledge categories
        self.categories = {
            'market_data': [],
            'news': [],
            'analysis': [],
            'user_insights': [],
            'images': [],
            'videos': [],
            'documents': []
        }
        
        # Load existing knowledge base if available
        self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> None:
        """Load knowledge base from storage."""
        index_path = os.path.join(self.storage_dir, 'index.json')
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    self.categories = json.load(f)
                logger.info(f"Loaded knowledge base with {sum(len(items) for items in self.categories.values())} items")
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")
    
    def _save_knowledge_base(self) -> None:
        """Save knowledge base to storage."""
        index_path = os.path.join(self.storage_dir, 'index.json')
        try:
            with open(index_path, 'w') as f:
                json.dump(self.categories, f, indent=2)
            logger.info(f"Saved knowledge base with {sum(len(items) for items in self.categories.values())} items")
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
    
    def add_item(self, content: Any, category: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add an item to the knowledge base.
        
        Args:
            content: The content to add (text, file path, or structured data)
            category: Category of the content ('market_data', 'news', 'analysis', 'user_insights', etc.)
            metadata: Additional metadata about the content
            
        Returns:
            ID of the added item
        """
        if category not in self.categories:
            logger.warning(f"Unknown category: {category}. Creating new category.")
            self.categories[category] = []
        
        # Generate a unique ID for the item
        item_id = f"{category}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.categories[category])}"
        
        # Create item with metadata
        item = {
            'id': item_id,
            'content': content,
            'added_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Add to appropriate category
        self.categories[category].append(item)
        
        # Save knowledge base
        self._save_knowledge_base()
        
        logger.info(f"Added item {item_id} to category {category}")
        return item_id
    
    def add_file(self, file_path: str, category: str = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a file to the knowledge base.
        
        Args:
            file_path: Path to the file
            category: Category to add the file to. If None, will infer from file extension.
            metadata: Additional metadata about the file
            
        Returns:
            ID of the added item
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        # Infer category from file extension if not provided
        if category is None:
            extension = os.path.splitext(file_path)[1].lower()
            if extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
                category = "images"
            elif extension in [".mp4", ".avi", ".mov", ".mkv"]:
                category = "videos"
            elif extension in [".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx"]:
                category = "documents"
            else:
                category = "documents"  # Default category
        
        # Copy file to knowledge base storage
        filename = os.path.basename(file_path)
        storage_path = os.path.join(self.storage_dir, category, filename)
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        try:
            # Copy file content
            with open(file_path, 'rb') as src, open(storage_path, 'wb') as dst:
                dst.write(src.read())
            
            # Add metadata
            if metadata is None:
                metadata = {}
            
            metadata['original_path'] = file_path
            metadata['filename'] = filename
            metadata['storage_path'] = storage_path
            
            # Add to knowledge base
            return self.add_item(storage_path, category, metadata)
        except Exception as e:
            logger.error(f"Error adding file to knowledge base: {e}")
            return None
    
    def add_text(self, text: str, category: str = "user_insights", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add text content to the knowledge base.
        
        Args:
            text: The text content to add
            category: Category to add the text to
            metadata: Additional metadata about the text
            
        Returns:
            ID of the added item
        """
        return self.add_item(text, category, metadata)
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an item from the knowledge base by ID.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Item dictionary or None if not found
        """
        # Extract category from item_id
        if '_' not in item_id:
            logger.error(f"Invalid item ID format: {item_id}")
            return None
        
        category = item_id.split('_')[0]
        
        if category not in self.categories:
            logger.error(f"Category not found: {category}")
            return None
        
        # Find item by ID
        for item in self.categories[category]:
            if item['id'] == item_id:
                return item
        
        logger.error(f"Item not found: {item_id}")
        return None
    
    def get_items_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all items in a category.
        
        Args:
            category: Category to retrieve items from
            
        Returns:
            List of items in the category
        """
        if category not in self.categories:
            logger.warning(f"Category not found: {category}")
            return []
        
        return self.categories[category]
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge base for items matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching items
        """
        results = []
        query = query.lower()
        
        # Simple search implementation - in a real system, you'd use a proper search engine
        for category, items in self.categories.items():
            for item in items:
                # Search in content if it's a string
                if isinstance(item['content'], str) and query in item['content'].lower():
                    results.append(item)
                    continue
                
                # Search in metadata
                if any(query in str(v).lower() for v in item['metadata'].values()):
                    results.append(item)
        
        return results
    
    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the knowledge base.
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # Extract category from item_id
        if '_' not in item_id:
            logger.error(f"Invalid item ID format: {item_id}")
            return False
        
        category = item_id.split('_')[0]
        
        if category not in self.categories:
            logger.error(f"Category not found: {category}")
            return False
        
        # Find and remove item
        for i, item in enumerate(self.categories[category]):
            if item['id'] == item_id:
                # If item is a file, delete the file too
                if category in ['images', 'videos', 'documents'] and os.path.exists(item['content']):
                    try:
                        os.remove(item['content'])
                    except Exception as e:
                        logger.error(f"Error deleting file: {e}")
                
                # Remove from list
                self.categories[category].pop(i)
                self._save_knowledge_base()
                logger.info(f"Deleted item {item_id}")
                return True
        
        logger.error(f"Item not found: {item_id}")
        return False
    
    def clear_category(self, category: str) -> bool:
        """Clear all items in a category.
        
        Args:
            category: Category to clear
            
        Returns:
            True if cleared successfully, False otherwise
        """
        if category not in self.categories:
            logger.error(f"Category not found: {category}")
            return False
        
        # Delete files if category contains files
        if category in ['images', 'videos', 'documents']:
            for item in self.categories[category]:
                if os.path.exists(item['content']):
                    try:
                        os.remove(item['content'])
                    except Exception as e:
                        logger.error(f"Error deleting file: {e}")
        
        # Clear category
        self.categories[category] = []
        self._save_knowledge_base()
        logger.info(f"Cleared category {category}")
        return True
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names
        """
        return list(self.categories.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_items': sum(len(items) for items in self.categories.values()),
            'categories': {category: len(items) for category, items in self.categories.items()},
            'last_updated': datetime.now().isoformat()
        }
        return stats