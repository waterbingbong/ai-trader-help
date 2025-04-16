# API Integration Hub Component
# This module provides a UI for managing API keys and integration settings

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import project modules
from ai_integration import GeminiIntegration
from user_management.auth import User
from trading_agent.utils.metrics import RiskManagement

class APIIntegrationHub:
    """Component for managing API integrations and settings."""
    
    def __init__(self, app):
        """Initialize the API Integration Hub.
        
        Args:
            app: The Dash app instance
        """
        self.app = app
        self.register_callbacks()
        
        # Path for storing API keys (per user)
        self.api_keys_dir = Path(__file__).parent.parent.parent / 'user_management' / 'api_keys'
        self.api_keys_dir.mkdir(exist_ok=True)
    
    def get_layout(self):
        """Get the layout for the API Integration Hub.
        
        Returns:
            Dash layout object
        """
        return html.Div([
            html.Div([
                html.H2("API Integration Hub", className="section-title"),
                html.P(
                    "Manage your API keys and integration settings for AI services.",
                    className="section-description"
                ),
            ], className="section-header"),
            
            # Gemini API Integration
            html.Div([
                html.H3("Gemini 2.5 API", className="integration-title"),
                html.P(
                    "Connect your own Gemini 2.5 API key to use Google's advanced AI model for trading insights.",
                    className="integration-description"
                ),
                html.Div([
                    html.Label("API Key", htmlFor="gemini-api-key", className="form-label"),
                    dcc.Input(
                        id="gemini-api-key",
                        type="password",
                        placeholder="Enter your Gemini API key",
                        className="api-key-input"
                    ),
                    html.Button(
                        "Save", 
                        id="save-gemini-key-button", 
                        className="save-button"
                    ),
                    html.Div(id="gemini-key-status", className="key-status"),
                ], className="api-key-form"),
                
                # API Status
                html.Div([
                    html.H4("API Status", className="status-title"),
                    html.Div(id="gemini-api-status", className="api-status"),
                    html.Button(
                        "Test Connection", 
                        id="test-gemini-api-button", 
                        className="test-button"
                    ),
                ], className="api-status-container"),
            ], className="integration-section"),
            
            # Trading Pair Selection for AI Context
            html.Div([
                html.H3("AI Trading Context", className="integration-title"),
                html.P(
                    "Connect your risk management settings to the AI system for context-aware trading insights.",
                    className="integration-description"
                ),
                html.Div([
                    html.Label("Selected Trading Pair", htmlFor="trading-pair-select", className="form-label"),
                    dcc.Dropdown(
                        id="trading-pair-select",
                        options=[
                            {"label": "BTC/USD", "value": "BTC-USD"},
                            {"label": "ETH/USD", "value": "ETH-USD"},
                            {"label": "SOL/USD", "value": "SOL-USD"},
                            {"label": "XRP/USD", "value": "XRP-USD"},
                            {"label": "ADA/USD", "value": "ADA-USD"},
                        ],
                        placeholder="Select a trading pair",
                        className="trading-pair-dropdown"
                    ),
                    html.Button(
                        "Update AI Context", 
                        id="update-ai-context-button", 
                        className="update-button"
                    ),
                    html.Div(id="ai-context-status", className="context-status"),
                ], className="trading-context-form"),
            ], className="integration-section"),
            
            # Hidden div for storing state
            dcc.Store(id="api-integration-store"),
            
        ], className="api-integration-hub")
    
    def register_callbacks(self):
        """Register callbacks for the API Integration Hub."""
        
        # Callback for saving Gemini API key
        @self.app.callback(
            Output("gemini-key-status", "children"),
            Output("api-integration-store", "data"),
            Input("save-gemini-key-button", "n_clicks"),
            State("gemini-api-key", "value"),
            State("api-integration-store", "data"),
            prevent_initial_call=True
        )
        def save_gemini_api_key(n_clicks, api_key, stored_data):
            if not n_clicks or not api_key:
                return dash.no_update, dash.no_update
            
            # Get current user ID (if authenticated)
            user_id = "default"
            try:
                from flask_login import current_user
                if current_user.is_authenticated:
                    user_id = current_user.id
            except ImportError:
                pass
            
            # Save API key to user-specific file
            api_key_file = self.api_keys_dir / f"{user_id}_gemini.json"
            with open(api_key_file, 'w') as f:
                json.dump({"gemini_api_key": api_key}, f)
            
            # Update the Gemini integration with the new API key
            try:
                gemini_integration = GeminiIntegration(api_key=api_key)
                # Test the API key with a simple request
                test_result = gemini_integration.analyze_text("Test connection")
                if "error" in test_result:
                    return html.Div("API key saved but validation failed. Please check the key.", className="error-message"), stored_data
                
                # Update stored data
                if stored_data is None:
                    stored_data = {}
                stored_data["gemini_api_key"] = api_key
                
                return html.Div("API key saved successfully!", className="success-message"), stored_data
            except Exception as e:
                return html.Div(f"Error saving API key: {str(e)}", className="error-message"), stored_data
        
        # Callback for testing Gemini API connection
        @self.app.callback(
            Output("gemini-api-status", "children"),
            Input("test-gemini-api-button", "n_clicks"),
            State("api-integration-store", "data"),
            prevent_initial_call=True
        )
        def test_gemini_api(n_clicks, stored_data):
            if not n_clicks:
                return dash.no_update
            
            # Get API key from stored data or user file
            api_key = None
            if stored_data and "gemini_api_key" in stored_data:
                api_key = stored_data["gemini_api_key"]
            else:
                # Try to load from user file
                user_id = "default"
                try:
                    from flask_login import current_user
                    if current_user.is_authenticated:
                        user_id = current_user.id
                except ImportError:
                    pass
                
                api_key_file = self.api_keys_dir / f"{user_id}_gemini.json"
                if api_key_file.exists():
                    with open(api_key_file, 'r') as f:
                        try:
                            data = json.load(f)
                            api_key = data.get("gemini_api_key")
                        except json.JSONDecodeError:
                            pass
            
            if not api_key:
                return html.Div("No API key found. Please save your API key first.", className="warning-message")
            
            # Test the API key
            try:
                gemini_integration = GeminiIntegration(api_key=api_key)
                test_result = gemini_integration.analyze_text("Test connection")
                if "error" in test_result:
                    return html.Div("API connection failed. Please check your API key.", className="error-message")
                return html.Div("API connection successful!", className="success-message")
            except Exception as e:
                return html.Div(f"Error testing API connection: {str(e)}", className="error-message")
        
        # Callback for updating AI context with trading pair
        @self.app.callback(
            Output("ai-context-status", "children"),
            Input("update-ai-context-button", "n_clicks"),
            State("trading-pair-select", "value"),
            prevent_initial_call=True
        )
        def update_ai_context(n_clicks, trading_pair):
            if not n_clicks or not trading_pair:
                return dash.no_update
            
            # Get current user ID (if authenticated)
            user_id = "default"
            try:
                from flask_login import current_user
                if current_user.is_authenticated:
                    user_id = current_user.id
            except ImportError:
                pass
            
            # Save trading pair context to user-specific file
            context_file = self.api_keys_dir / f"{user_id}_context.json"
            with open(context_file, 'w') as f:
                json.dump({"trading_pair": trading_pair}, f)
            
            # Update the risk management system with the selected trading pair
            try:
                # This would typically connect to the risk management system
                # For now, we'll just save the context
                return html.Div(f"AI context updated with trading pair: {trading_pair}", className="success-message")
            except Exception as e:
                return html.Div(f"Error updating AI context: {str(e)}", className="error-message")


def get_api_integration_hub(app):
    """Factory function to create an API Integration Hub instance.
    
    Args:
        app: The Dash app instance
        
    Returns:
        APIIntegrationHub instance
    """
    return APIIntegrationHub(app)