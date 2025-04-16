# AI Trading Assistant - License System Guide

## Overview

The AI Trading Assistant now includes a free cloud-based license system with Discord authentication. This system allows users to log in using their Discord accounts to access the trading dashboard. This guide explains how to set up and deploy the system.

## Features

- **Discord OAuth Integration**: Users can log in with their Discord accounts
- **Free License Tier**: All users receive a free license
- **Cloud-Based Authentication**: User data is stored securely in the cloud
- **Session Management**: User sessions are maintained across visits

## Setup Instructions

### 1. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "AI Trading Assistant")
3. Navigate to the "OAuth2" section in the left sidebar
4. Add a redirect URL: `https://your-app-url.onrender.com/auth/discord/callback`
   - Replace `your-app-url.onrender.com` with your actual Render.com URL
5. Copy the "Client ID" and "Client Secret" - you'll need these for deployment

### 2. Configure Environment Variables

You'll need to set the following environment variables in your deployment:

- `DISCORD_CLIENT_ID`: Your Discord application client ID
- `DISCORD_CLIENT_SECRET`: Your Discord application client secret
- `DISCORD_REDIRECT_URI`: The full callback URL (e.g., `https://your-app-url.onrender.com/auth/discord/callback`)
- `SECRET_KEY`: A secure random string for session encryption (Render will generate this automatically)

## Deployment Guide

### Deploy on Render.com (Recommended)

1. Sign up for a free account at [Render](https://render.com/)
2. Click 'New +' and select 'Web Service'
3. Connect your GitHub repository
4. Configure your service:
   - Name: ai-trading-assistant
   - Environment: Python
   - Build Command: (The build command is already configured in render.yaml)
   - Start Command: `gunicorn dashboard.app_with_auth:server`
   - Select the free plan
5. Add environment variables:
   - Click 'Environment' tab
   - Add `GEMINI_API_KEY` with your API key value
   - Add `DISCORD_CLIENT_ID` with your Discord client ID
   - Add `DISCORD_CLIENT_SECRET` with your Discord client secret
   - Add `DISCORD_REDIRECT_URI` with your callback URL
   - Render will automatically generate a `SECRET_KEY`
6. Click 'Create Web Service'

### Alternative: Deploy with render.yaml

If your repository includes the updated `render.yaml` file, you can use Render's Blueprint feature:

1. Go to the Render Dashboard
2. Click "Blueprints" in the sidebar
3. Connect your repository
4. Render will automatically detect the `render.yaml` file and configure the service
5. You'll still need to add the environment variables manually

## User Experience

1. Users visit your deployed application
2. They are presented with a login screen
3. Users click "Login with Discord"
4. They authorize the application on Discord
5. After successful authentication, they are redirected to the dashboard

## License Management

The current implementation provides a free license to all users. The system is designed to be extensible for future premium tiers if needed.

## Troubleshooting

### Common Issues

1. **Discord Login Not Working**
   - Verify that your Discord application's redirect URL exactly matches the `DISCORD_REDIRECT_URI` environment variable
   - Check that your `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` are correct

2. **Session Errors**
   - Ensure the `SECRET_KEY` environment variable is set
   - Clear browser cookies and try again

3. **Deployment Failures**
   - Check the Render logs for specific error messages
   - Verify that all required environment variables are set

## Security Considerations

- The Discord client secret should never be exposed in client-side code
- All authentication is handled server-side for security
- User data is stored securely and passwords are never stored (OAuth only)

## Next Steps

Future enhancements could include:

- Premium license tiers with additional features
- User profile management
- Usage analytics and tracking
- Additional authentication methods