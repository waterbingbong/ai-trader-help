# Google Drive Integration Component for AI Trading Assistant Dashboard
# Provides UI elements for Google Drive connection and data management

import dash
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask_login import current_user
import requests
import os
from pathlib import Path

# Import user management modules
from user_management.discord_auth_enhanced import EnhancedUser
from user_management.google_drive_integration import GoogleDriveManager, DataSynchronizer, BackupManager

class GoogleDriveComponent:
    """Component for Google Drive integration in the dashboard"""
    
    def __init__(self, app):
        self.app = app
        self.register_callbacks()
    
    def layout(self):
        """Return the component layout"""
        return html.Div([
            html.Div(id="google-drive-status"),
            
            # Google Drive connection section
            html.Div([
                html.H3("Google Drive Integration", className="section-title"),
                html.P(
                    "Connect your Google Drive account to store your trading data, models, and history.",
                    className="section-description"
                ),
                html.Div([
                    html.A(
                        html.Button("Connect Google Drive", id="connect-drive-button", className="action-button"),
                        href="/auth/google/connect",
                        id="connect-drive-link",
                        style={"display": "block"}
                    ),
                    html.Div(id="drive-connection-status", className="status-message")
                ], id="drive-connection-container")
            ], className="integration-section"),
            
            # Data synchronization section
            html.Div([
                html.H3("Data Synchronization", className="section-title"),
                html.P(
                    "Synchronize your local data with Google Drive for backup and access across devices.",
                    className="section-description"
                ),
                
                # Local directory input
                html.Div([
                    html.Label("Local Directory:", className="input-label"),
                    dcc.Input(
                        id="local-dir-input",
                        type="text",
                        placeholder="Enter local directory path",
                        className="text-input"
                    )
                ], className="input-group"),
                
                # Sync buttons
                html.Div([
                    html.Button(
                        "Sync to Drive", 
                        id="sync-to-drive-button",
                        className="action-button",
                        disabled=True
                    ),
                    html.Button(
                        "Download from Drive", 
                        id="download-from-drive-button",
                        className="action-button",
                        disabled=True
                    )
                ], className="button-group"),
                
                # Sync status message
                html.Div(id="sync-status-message", className="status-message")
            ], id="sync-section", className="integration-section", style={"display": "none"}),
            
            # Backup section
            html.Div([
                html.H3("Backup Management", className="section-title"),
                html.P(
                    "Create and restore backups of your trading data.",
                    className="section-description"
                ),
                
                # Backup name input
                html.Div([
                    html.Label("Backup Name (optional):", className="input-label"),
                    dcc.Input(
                        id="backup-name-input",
                        type="text",
                        placeholder="Enter backup name",
                        className="text-input"
                    )
                ], className="input-group"),
                
                # Backup buttons
                html.Div([
                    html.Button(
                        "Create Backup", 
                        id="create-backup-button",
                        className="action-button",
                        disabled=True
                    ),
                    html.Button(
                        "Refresh Backup List", 
                        id="refresh-backups-button",
                        className="action-button",
                        disabled=True
                    )
                ], className="button-group"),
                
                # Backup list
                html.Div([
                    html.H4("Available Backups", className="subsection-title"),
                    html.Div(id="backup-list", className="list-container")
                ], className="backup-list-section"),
                
                # Backup status message
                html.Div(id="backup-status-message", className="status-message")
            ], id="backup-section", className="integration-section", style={"display": "none"}),
            
            # Hidden storage
            dcc.Store(id="drive-data-store", storage_type="session")
        ], id="google-drive-component", className="dashboard-component")
    
    def register_callbacks(self):
        """Register component callbacks"""
        
        # Update Google Drive connection status
        @self.app.callback(
            Output("drive-connection-status", "children"),
            Output("connect-drive-link", "style"),
            Output("sync-section", "style"),
            Output("backup-section", "style"),
            Output("sync-to-drive-button", "disabled"),
            Output("download-from-drive-button", "disabled"),
            Output("create-backup-button", "disabled"),
            Output("refresh-backups-button", "disabled"),
            [Input("interval-component", "n_intervals")]
        )
        def update_drive_connection_status(n):
            """Update Google Drive connection status"""
            if not current_user.is_authenticated:
                return (
                    "Please log in to connect Google Drive",
                    {"display": "none"},
                    {"display": "none"},
                    {"display": "none"},
                    True, True, True, True
                )
            
            # Check if user has Google Drive connected
            if hasattr(current_user, 'google_drive_connected') and current_user.google_drive_connected:
                return (
                    html.Div([
                        html.I(className="fas fa-check-circle"),
                        " Google Drive connected"
                    ], className="success-message"),
                    {"display": "none"},
                    {"display": "block"},
                    {"display": "block"},
                    False, False, False, False
                )
            else:
                return (
                    "Not connected",
                    {"display": "block"},
                    {"display": "none"},
                    {"display": "none"},
                    True, True, True, True
                )
        
        # Sync to Drive callback
        @self.app.callback(
            Output("sync-status-message", "children"),
            [Input("sync-to-drive-button", "n_clicks")],
            [State("local-dir-input", "value")]
        )
        def sync_to_drive(n_clicks, local_dir):
            """Sync local directory to Google Drive"""
            if not n_clicks or not local_dir:
                return ""
            
            # Make API request to sync endpoint
            response = requests.post(
                "/api/drive/sync",
                json={"local_dir": local_dir},
                cookies=dict(request.cookies)
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return html.Div([
                        html.I(className="fas fa-check-circle"),
                        f" {data.get('message', 'Sync successful')}"
                    ], className="success-message")
                else:
                    return html.Div([
                        html.I(className="fas fa-exclamation-circle"),
                        f" {data.get('message', 'Sync failed')}"
                    ], className="error-message")
            else:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle"),
                    " Error: Failed to sync data"
                ], className="error-message")
        
        # Download from Drive callback
        @self.app.callback(
            Output("sync-status-message", "children", allow_duplicate=True),
            [Input("download-from-drive-button", "n_clicks")],
            [State("local-dir-input", "value")],
            prevent_initial_call=True
        )
        def download_from_drive(n_clicks, local_dir):
            """Download data from Google Drive"""
            if not n_clicks or not local_dir:
                return ""
            
            # Get user's root folder ID
            root_folder_id = GoogleDriveManager.create_user_folder(current_user.id)
            if not root_folder_id:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle"),
                    " Error: Failed to access Google Drive folder"
                ], className="error-message")
            
            # Make API request to download endpoint
            response = requests.post(
                "/api/drive/download",
                json={
                    "folder_id": root_folder_id,
                    "local_dir": local_dir
                },
                cookies=dict(request.cookies)
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return html.Div([
                        html.I(className="fas fa-check-circle"),
                        f" {data.get('message', 'Download successful')}"
                    ], className="success-message")
                else:
                    return html.Div([
                        html.I(className="fas fa-exclamation-circle"),
                        f" {data.get('message', 'Download failed')}"
                    ], className="error-message")
            else:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle"),
                    " Error: Failed to download data"
                ], className="error-message")
        
        # Create backup callback
        @self.app.callback(
            Output("backup-status-message", "children"),
            [Input("create-backup-button", "n_clicks")],
            [State("local-dir-input", "value"),
             State("backup-name-input", "value")]
        )
        def create_backup(n_clicks, local_dir, backup_name):
            """Create backup of local directory"""
            if not n_clicks or not local_dir:
                return ""
            
            # Make API request to backup endpoint
            response = requests.post(
                "/api/drive/backup",
                json={
                    "local_dirs": [local_dir],
                    "backup_name": backup_name
                },
                cookies=dict(request.cookies)
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return html.Div([
                        html.I(className="fas fa-check-circle"),
                        f" {data.get('message', 'Backup created successfully')}"
                    ], className="success-message")
                else:
                    return html.Div([
                        html.I(className="fas fa-exclamation-circle"),
                        f" {data.get('message', 'Backup failed')}"
                    ], className="error-message")
            else:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle"),
                    " Error: Failed to create backup"
                ], className="error-message")
        
        # Refresh backup list callback
        @self.app.callback(
            Output("backup-list", "children"),
            [Input("refresh-backups-button", "n_clicks")]
        )
        def refresh_backup_list(n_clicks):
            """Refresh list of available backups"""
            if not n_clicks:
                return html.P("Click 'Refresh Backup List' to view available backups.")
            
            # Make API request to list backups endpoint
            response = requests.get(
                "/api/drive/backups",
                cookies=dict(request.cookies)
            )
            
            if response.status_code == 200:
                data = response.json()
                backups = data.get('backups', [])
                
                if not backups:
                    return html.P("No backups found.")
                
                # Create list of backup items
                backup_items = []
                for backup in backups:
                    created_time = backup.get('createdTime', '').replace('T', ' ').split('.')[0]
                    backup_items.append(
                        html.Div([
                            html.Div([
                                html.H5(backup.get('name', 'Unnamed Backup'), className="backup-name"),
                                html.P(f"Created: {created_time}", className="backup-date")
                            ], className="backup-info"),
                            html.Button(
                                "Restore",
                                id={"type": "restore-backup-button", "index": backup.get('id')},
                                className="restore-button"
                            )
                        ], className="backup-item")
                    )
                
                return backup_items
            else:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle"),
                    " Error: Failed to retrieve backups"
                ], className="error-message")
        
        # Restore backup callback
        @self.app.callback(
            Output("backup-status-message", "children", allow_duplicate=True),
            [Input({"type": "restore-backup-button", "index": dash.ALL}, "n_clicks")],
            [State("local-dir-input", "value")],
            prevent_initial_call=True
        )
        def restore_backup(n_clicks_list, local_dir):
            """Restore selected backup"""
            ctx = dash.callback_context
            if not ctx.triggered or not local_dir:
                return ""
            
            # Get the ID of the clicked button
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            backup_id = eval(button_id)["index"]
            
            # Make API request to restore backup endpoint
            response = requests.post(
                "/api/drive/restore",
                json={
                    "backup_folder_id": backup_id,
                    "local_dir": local_dir
                },
                cookies=dict(request.cookies)
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return html.Div([
                        html.I(className="fas fa-check-circle"),
                        f" {data.get('message', 'Backup restored successfully')}"
                    ], className="success-message")
                else:
                    return html.Div([
                        html.I(className="fas fa-exclamation-circle"),
                        f" {data.get('message', 'Restore failed')}"
                    ], className="error-message")
            else:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle"),
                    " Error: Failed to restore backup"
                ], className="error-message")


# Function to create and return the component
def get_google_drive_component(app):
    """Create and return Google Drive component"""
    return GoogleDriveComponent(app)