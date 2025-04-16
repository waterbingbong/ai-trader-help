# AI Trading Assistant - Discord & Google Drive Integration Guide

## Overview

This guide explains how to set up and use the Discord authentication and Google Drive integration features in your AI Trading Assistant. These features allow users to:

1. Authenticate using their Discord accounts
2. Verify their roles from a specific Discord server
3. Connect their Google Drive accounts for data storage
4. Automatically synchronize trading data, models, and history between the local application and Google Drive
5. Create and restore backups of user data

## Prerequisites

Before setting up these integrations, you'll need:

1. A Discord account and a Discord application with OAuth2 configured
2. A Google Cloud Platform account with the Google Drive API enabled
3. The updated dependencies installed (see `requirements.txt.updated`)

## Setup Instructions

### 1. Discord Application Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select an existing one
3. Navigate to the "OAuth2" section
4. Add a redirect URL: `https://your-app-url.onrender.com/auth/discord/callback`
5. Save changes
6. Note your Client ID and Client Secret
7. In the "Bot" section, create a bot if you don't have one already
8. Enable the "Server Members Intent" under Privileged Gateway Intents
9. Copy your bot token

### 2. Google Drive API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Configure the OAuth consent screen
   - Set the application type to "External"
   - Add the necessary scopes (`https://www.googleapis.com/auth/drive.file`)
5. Create OAuth 2.0 credentials
   - Application type: Web application
   - Add authorized redirect URI: `https://your-app-url.onrender.com/auth/google/callback`
6. Note your Client ID and Client Secret

### 3. Environment Configuration

1. Copy the `.env.example.updated` file to `.env`
2. Fill in the following values:
   ```
   DISCORD_CLIENT_ID=your_discord_client_id_here
   DISCORD_CLIENT_SECRET=your_discord_client_secret_here
   DISCORD_REDIRECT_URI=https://your-app-url.onrender.com/auth/discord/callback
   DISCORD_SERVER_ID=your_discord_server_id_here
   DISCORD_BOT_TOKEN=your_discord_bot_token_here
   
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   GOOGLE_REDIRECT_URI=https://your-app-url.onrender.com/auth/google/callback
   
   SECRET_KEY=your_secret_key_here_use_a_strong_random_value
   ```

### 4. Update Dependencies

1. Rename `requirements.txt.updated` to `requirements.txt` or merge the new dependencies
2. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Implementation Details

### File Structure

The integration consists of the following key files:

- `user_management/discord_auth_enhanced.py`: Enhanced Discord authentication with role verification
- `user_management/google_drive_integration.py`: Google Drive API integration for file storage and synchronization
- `dashboard/components/google_drive_component.py`: Dashboard UI component for Google Drive integration

### Using the Integration

#### 1. Update your main application

Replace the existing authentication initialization in your main application file with:

```python
# Import enhanced authentication
from user_management.discord_auth_enhanced import EnhancedAuthManager, init_enhanced_auth_routes

# Initialize enhanced authentication routes
init_enhanced_auth_routes(server)
```

#### 2. Add Google Drive component to your dashboard

Add the Google Drive component to your dashboard layout:

```python
# Import Google Drive component
from dashboard.components.google_drive_component import get_google_drive_component

# Initialize Google Drive component
google_drive_component = get_google_drive_component(app)

# Add to your layout
app.layout = html.Div([
    # Existing components
    ...,
    
    # Google Drive component
    google_drive_component.layout()
])
```

## User Flow

1. **Discord Authentication**:
   - User clicks "Login with Discord"
   - User authorizes the application on Discord
   - Application verifies user's server membership and roles
   - User is logged in and redirected to the dashboard

2. **Google Drive Connection**:
   - Authenticated user clicks "Connect Google Drive"
   - User authorizes the application on Google
   - Application creates a root folder in the user's Google Drive
   - User can now sync data between local storage and Google Drive

3. **Data Synchronization**:
   - User enters a local directory path
   - User clicks "Sync to Drive" to upload data
   - User clicks "Download from Drive" to download data
   - Changes are tracked to minimize data transfer

4. **Backup Management**:
   - User can create named backups of their data
   - User can view a list of available backups
   - User can restore backups to a local directory

## Security Considerations

1. **Token Storage**: Authentication tokens are securely stored and automatically refreshed when needed
2. **Role Verification**: User roles are verified against a specific Discord server
3. **Scoped Access**: Google Drive access is limited to application-created files only
4. **Session Management**: User sessions are securely managed with Flask-Login

## Troubleshooting

### Discord Authentication Issues

- Ensure your Discord redirect URI exactly matches what's configured in the Discord Developer Portal
- Check that your bot has the correct permissions and is in your server
- Verify that the Server Members Intent is enabled for your bot

### Google Drive Integration Issues

- Ensure your Google redirect URI exactly matches what's configured in Google Cloud Console
- Check that the Google Drive API is enabled for your project
- Verify that your OAuth consent screen is properly configured

## Next Steps

1. **Custom Role-Based Access**: Implement different features based on Discord roles
2. **Enhanced Backup Scheduling**: Add automatic scheduled backups
3. **Multi-Device Sync**: Implement real-time synchronization across multiple devices
4. **Collaborative Features**: Allow sharing specific data with other users

---

For more information, refer to the documentation in the code files or contact the development team.