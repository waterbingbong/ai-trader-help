# Dashboard Application with Authentication
# This module implements a web dashboard for the AI Trading Assistant with user authentication

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
from flask import request
from flask_login import login_required, current_user

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import project modules
from dashboard.components.performance_dashboard import PerformanceDashboard, TradeAnalyzer
from dashboard.components.trade_monitor import TradeMonitor, AlertSystem
from dashboard.components.api_integration_hub import get_api_integration_hub
from trading_agent.utils.metrics import PerformanceMetrics, RiskManagement, PortfolioAnalytics
from data_processing.connectors.market_data import get_data_connector
from user_management.auth import AuthManager, User
from ai_integration.gemini_integration_manager import gemini_manager

# Initialize the Dash app with Flask server for authentication
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    meta_tags=[
        # Responsive viewport meta tag
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0, maximum-scale=5.0"},
        # PWA related meta tags
        {"name": "theme-color", "content": "#2c3e50"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "apple-mobile-web-app-status-bar-style", "content": "black-translucent"},
        {"name": "apple-mobile-web-app-title", "content": "AI Trader"},
        # Web app manifest
        {"name": "manifest", "content": "/assets/manifest.json"},
        # SEO and accessibility
        {"name": "description", "content": "AI Trading Assistant Dashboard with real-time monitoring and alerts"},
        {"property": "og:title", "content": "AI Trading Assistant"},
        {"property": "og:description", "content": "Intelligent trading dashboard with real-time data and alerts"},
        {"http-equiv": "X-UA-Compatible", "content": "IE=edge"}
    ],
    external_stylesheets=[
        "/assets/styles.css",
        "/assets/responsive.css",
        "/assets/modern-ui.css"
    ]
)
server = app.server

# Initialize Flask-Login
login_manager = AuthManager.init_login_manager(server)

# Initialize authentication routes
from user_management.auth import init_auth_routes
init_auth_routes(server)

# Configure server for sessions
server.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key'),
    SESSION_TYPE='filesystem'
)

# Register service worker for PWA support
app.clientside_callback(
    """
    function(n) {
        if (!n) return;
        
        // Initialize notification handler
        if (window.notificationHandler) {
            window.notificationHandler.init().then(supported => {
                if (supported) {
                    console.log('Notification system initialized');
                }
            });
        }
        
        // Register service worker for PWA
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/assets/service-worker.js')
                .then(registration => {
                    console.log('Service Worker registered with scope:', registration.scope);
                })
                .catch(error => {
                    console.error('Service Worker registration failed:', error);
                });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('pwa-initialized-store', 'data'),
    [Input('interval-component', 'n_intervals')]
)

# Connect Risk Management to AI System
@app.callback(
    Output('risk-ai-connection-status', 'children'),
    [Input('trading-pair-select', 'value')],
    [State('auth-store', 'data')]
)
def update_ai_risk_connection(trading_pair, auth_data):
    if not trading_pair:
        return html.Div("No trading pair selected", className="warning-message")
    
    # Get user ID from auth data
    user_id = auth_data.get('user_id', 'default') if auth_data else 'default'
    
    # Update trading context in Gemini manager
    success = gemini_manager.update_trading_context(user_id, trading_pair)
    
    if success:
        return html.Div(f"AI system connected to risk management for {trading_pair}", className="success-message")
    else:
        return html.Div("Failed to connect AI to risk management", className="error-message")

# Authentication status store
auth_store = dcc.Store(id='auth-store', storage_type='session')

# Initialize API Integration Hub
api_hub = get_api_integration_hub(app)

# Login form component
login_form = html.Div([
    html.H2("Login to AI Trading Assistant", className="login-title"),
    html.P("Please log in with your Discord account to access the dashboard", className="login-subtitle"),
    html.A(
        html.Button("Login with Discord", className="discord-login-button"),
        href="/auth/login",
        className="login-link"
    ),
    html.Div(id="login-error-message", className="login-error")
], className="login-container")

# User profile component
user_profile = html.Div([
    html.Div([
        html.Img(id="user-avatar", className="user-avatar"),
        html.Div([
            html.H3(id="user-name", className="user-name"),
            html.P(id="license-type", className="license-type")
        ], className="user-info")
    ], className="user-header"),
    html.A(
        html.Button("Logout", className="logout-button"),
        href="/auth/logout",
        className="logout-link"
    )
], id="user-profile", className="user-profile-container")

# Define the app layout with authentication components
app.layout = html.Div([
    # Authentication store
    auth_store,
    
    # Authentication status check interval
    dcc.Interval(
        id='auth-check-interval',
        interval=60*1000,  # Check auth status every minute
        n_intervals=0
    ),
    
    # Main content that switches between login and dashboard
    html.Div(id="main-content"),
    
    # Original app components (will be shown only when authenticated)
    html.Div(id="app-content", style={"display": "none"}, children=[
        html.Span("AI Trading Assistant", className="visually-hidden", id="app-title"),
        # Add notification permission request
        html.Div([
            html.Button(
                "Enable Notifications", 
                id="enable-notifications-button",
                className="notification-button",
                **{'aria-label': 'Enable push notifications'}
            ),
            html.Div(id="notification-status", className="notification-status")
        ], className="notification-container", style={"display": "none"}, id="notification-permission-container"),
        
        # Original dashboard content would go here
        # This is a placeholder for the original app.layout content
    ]),
    
    # Hidden components for storing data and PWA initialization
    html.Div(id="portfolio-data-store", **{'data-pwa-initialized': None}, style={"display": "none"}),
    dcc.Store(id="pwa-initialized-store", storage_type="memory"),
    
    # Interval for auto-refresh
    dcc.Interval(
        id="interval-component",
        interval=60*1000,  # in milliseconds (1 minute)
        n_intervals=0
    ),
    
    # Risk management components
    html.Div(id="risk-ai-connection-status", style={"display": "none"}),
    html.Div(id="trading-pair-select-container", style={"display": "none"})
])

# Authentication callbacks
@app.callback(
    Output('auth-store', 'data'),
    Input('auth-check-interval', 'n_intervals')
)
def check_auth_status(n):
    """Check authentication status and update store"""
    # Make request to auth status endpoint
    import requests
    response = requests.get('/auth/status', cookies=dict(request.cookies))
    
    if response.status_code == 200:
        return response.json()
    return {'authenticated': False}

@app.callback(
    Output('main-content', 'children'),
    Output('app-content', 'style'),
    Input('auth-store', 'data')
)
def update_auth_ui(auth_data):
    """Update UI based on authentication status"""
    if auth_data and auth_data.get('authenticated'):
        # User is authenticated, show dashboard and user profile
        return user_profile, {'display': 'block'}
    else:
        # User is not authenticated, show login form
        return login_form, {'display': 'none'}

@app.callback(
    Output('user-avatar', 'src'),
    Output('user-name', 'children'),
    Output('license-type', 'children'),
    Input('auth-store', 'data')
)
def update_user_profile(auth_data):
    """Update user profile information"""
    if auth_data and auth_data.get('authenticated') and 'user' in auth_data:
        user = auth_data['user']
        avatar_url = f"https://cdn.discordapp.com/avatars/{user.get('discord_id')}/{user.get('avatar')}.png" \
            if user.get('avatar') else '/assets/default-avatar.png'
        
        license_text = f"License: {user.get('license_type', 'Free')}"
        if not user.get('license_valid', True):
            license_text += " (Invalid)"
        
        return avatar_url, user.get('username', 'User'), license_text
    
    return '/assets/default-avatar.png', 'Guest', 'Not logged in'

# Main server entry point
if __name__ == '__main__':
    app.run_server(debug=True)