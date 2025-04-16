# Integration Example for AI Trading Assistant
# Demonstrates how to use Discord authentication and Google Drive integration

import os
import sys
from pathlib import Path
from flask import Flask, redirect, url_for
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
from flask_login import login_required, current_user

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import project modules
from user_management.discord_auth_enhanced import EnhancedAuthManager, init_enhanced_auth_routes, EnhancedUser
from user_management.google_drive_integration import GoogleDriveManager, DataSynchronizer, BackupManager
from dashboard.components.google_drive_component import get_google_drive_component

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Flask server
server = Flask(__name__)
server.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key'),
    SESSION_TYPE='filesystem'
)

# Initialize Dash app
app = Dash(
    __name__,
    server=server,
    suppress_callback_exceptions=True,
    url_base_pathname='/'
)

# Initialize enhanced authentication
login_manager = EnhancedAuthManager.init_login_manager(server)
init_enhanced_auth_routes(server)

# Initialize Google Drive component
google_drive_component = get_google_drive_component(app)

# Define app layout
app.layout = html.Div([
    # Authentication status store
    dcc.Store(id='auth-store', storage_type='session'),
    
    # Authentication status check interval
    dcc.Interval(
        id='auth-check-interval',
        interval=60*1000,  # Check auth status every minute
        n_intervals=0
    ),
    
    # Header
    html.Div([
        html.H1("AI Trading Assistant", className="app-title"),
        html.Div(id="user-profile-container")
    ], className="app-header"),
    
    # Main content
    html.Div([
        # Login form (shown when not authenticated)
        html.Div([
            html.H2("Login to AI Trading Assistant", className="login-title"),
            html.P("Please log in with your Discord account to access the dashboard", className="login-subtitle"),
            html.A(
                html.Button("Login with Discord", className="discord-login-button"),
                href="/auth/login",
                className="login-link"
            )
        ], id="login-container", className="login-container"),
        
        # Dashboard content (shown when authenticated)
        html.Div([
            # Tabs for different sections
            dcc.Tabs([
                # Trading Dashboard Tab
                dcc.Tab(label="Trading Dashboard", children=[
                    html.Div([
                        html.H2("Trading Dashboard"),
                        html.P("Your trading dashboard content would go here.")
                    ], className="tab-content")
                ]),
                
                # Google Drive Integration Tab
                dcc.Tab(label="Google Drive Integration", children=[
                    html.Div([
                        # Google Drive component
                        google_drive_component.layout()
                    ], className="tab-content")
                ]),
                
                # Settings Tab
                dcc.Tab(label="Settings", children=[
                    html.Div([
                        html.H2("Settings"),
                        html.P("Your settings content would go here.")
                    ], className="tab-content")
                ])
            ], id="dashboard-tabs", className="dashboard-tabs")
        ], id="dashboard-container", style={"display": "none"})
    ], id="main-content", className="main-content"),
    
    # Footer
    html.Div([
        html.P("AI Trading Assistant - Discord & Google Drive Integration")
    ], className="app-footer"),
    
    # Interval for auto-refresh
    dcc.Interval(
        id="interval-component",
        interval=60*1000,  # in milliseconds (1 minute)
        n_intervals=0
    )
])

# User profile component
user_profile = html.Div([
    html.Div([
        html.Img(id="user-avatar", className="user-avatar"),
        html.Div([
            html.H3(id="user-name", className="user-name"),
            html.P(id="license-type", className="license-type"),
            html.P(id="google-drive-status", className="google-drive-status")
        ], className="user-info")
    ], className="user-header"),
    html.A(
        html.Button("Logout", className="logout-button"),
        href="/auth/logout",
        className="logout-link"
    )
], id="user-profile", className="user-profile-container")

# Authentication callbacks
@app.callback(
    Output('auth-store', 'data'),
    Input('auth-check-interval', 'n_intervals')
)
def check_auth_status(n):
    """Check authentication status and update store"""
    import requests
    from flask import request
    
    # Make request to auth status endpoint
    response = requests.get('/auth/status', cookies=dict(request.cookies))
    
    if response.status_code == 200:
        return response.json()
    return {'authenticated': False}

@app.callback(
    Output('user-profile-container', 'children'),
    Output('login-container', 'style'),
    Output('dashboard-container', 'style'),
    Input('auth-store', 'data')
)
def update_auth_ui(auth_data):
    """Update UI based on authentication status"""
    if auth_data and auth_data.get('authenticated'):
        # User is authenticated, show dashboard and user profile
        return user_profile, {'display': 'none'}, {'display': 'block'}
    else:
        # User is not authenticated, show login form
        return "", {'display': 'block'}, {'display': 'none'}

@app.callback(
    Output('user-avatar', 'src'),
    Output('user-name', 'children'),
    Output('license-type', 'children'),
    Output('google-drive-status', 'children'),
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
        
        drive_status = "Google Drive: Connected" if user.get('google_drive_connected') else "Google Drive: Not Connected"
        drive_class = "success-text" if user.get('google_drive_connected') else "warning-text"
        
        return avatar_url, user.get('username', 'User'), license_text, html.Span(drive_status, className=drive_class)
    
    return '/assets/default-avatar.png', 'Guest', 'Not logged in', ''

# Add route to redirect root to dashboard
@server.route('/')
def index():
    return redirect('/dashboard')

# Protected dashboard route
@server.route('/dashboard')
@login_required
def dashboard():
    return app.index()

# Main entry point
if __name__ == '__main__':
    # Create necessary directories
    Path(os.path.join(os.path.dirname(__file__), 'user_management', 'db')).mkdir(exist_ok=True)
    Path(os.path.join(os.path.dirname(__file__), 'user_management', 'tokens')).mkdir(exist_ok=True)
    
    # Run the application
    app.run_server(debug=True, port=int(os.environ.get('PORT', 8050)))