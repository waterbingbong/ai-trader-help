# AI Trading Assistant - Render.com Deployment Guide with Discord Authentication

This guide provides detailed, step-by-step instructions for deploying the AI Trading Assistant application on Render.com with Discord authentication integration.

## Prerequisites

Before you begin, make sure you have:

1. A GitHub account with your AI Trading Assistant repository
2. A Discord account to create an OAuth application
3. A Render.com account (free tier is sufficient)
4. A Google API key for Gemini AI integration

## Step 1: Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name (e.g., "AI Trading Assistant")
3. Navigate to the "OAuth2" section in the left sidebar
4. Under the "General" tab, note your **Client ID** and **Client Secret** (you'll need these later)
5. Click on "Add Redirect" and enter a temporary URL: `https://your-app-name.onrender.com/auth/discord/callback`
   - Replace `your-app-name` with what you plan to name your Render application (e.g., `ai-trading-assistant`)
   - You'll update this URL with the actual Render URL after deployment

## Step 2: Deploy on Render.com

### Option 1: Deploy with render.yaml (Recommended)

1. Log in to [Render.com](https://render.com/)
2. Click on "Blueprints" in the left sidebar
3. Click "New Blueprint Instance"
4. Connect your GitHub repository containing the AI Trading Assistant code
5. Render will automatically detect the `render.yaml` file in your repository
6. Review the configuration and click "Apply"
7. Set the required environment variables (see Step 3)
8. Click "Create Resources" to start the deployment

### Option 2: Manual Deployment

**Important:** Render.com's build environment is read-only for system-level directories, so commands like `apt-get` and manual compilation of libraries will fail. Use only Python package installations supported by pip. If TA-Lib is required, install it using pip only, as shown below.

1. Log in to [Render.com](https://render.com/)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure your service:
   - **Name**: ai-trading-assistant (or your preferred name)
   - **Environment**: Python
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your default branch)
   - **Build Command**:
     ```
     pip install numpy && \
     pip install -r requirements.txt && \
     pip install ta-lib || pip install git+https://github.com/mrjbq7/ta-lib.git@master
     ```
     - If you encounter errors with `ta-lib`, try the GitHub fallback as shown above.
   - **Start Command**: `gunicorn dashboard.app_with_auth:server`
   - **Plan**: Free

## Step 3: Configure Environment Variables

After creating your web service, you need to set up the required environment variables:

1. In your Render dashboard, select your newly created web service
2. Go to the "Environment" tab
3. Add the following environment variables:
   - `DISCORD_CLIENT_ID`: Your Discord application client ID (from Step 1)
   - `DISCORD_CLIENT_SECRET`: Your Discord application client secret (from Step 1)
   - `DISCORD_REDIRECT_URI`: The full callback URL (e.g., `https://your-app-name.onrender.com/auth/discord/callback`)
     - Replace `your-app-name.onrender.com` with your actual Render.com URL
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SECRET_KEY`: Render will automatically generate this for you if you used the Blueprint method
     - If manually deploying, create a secure random string or let Render generate one
4. Click "Save Changes"

## Step 4: Update Discord Redirect URL

After your application is deployed, you need to update the Discord redirect URL with the actual Render.com URL:

1. Copy your application's URL from the Render dashboard (e.g., `https://ai-trading-assistant.onrender.com`)
2. Go back to the [Discord Developer Portal](https://discord.com/developers/applications)
3. Select your application
4. Navigate to the "OAuth2" section
5. Update the redirect URL to: `https://your-actual-render-url.onrender.com/auth/discord/callback`
6. Click "Save Changes"

## Step 5: Test the Deployment

1. Visit your application's URL (e.g., `https://ai-trading-assistant.onrender.com`)
2. You should be redirected to the login page
3. Click "Login with Discord"
4. Authorize the application when prompted by Discord
5. After successful authentication, you should be redirected to the dashboard

## Troubleshooting

### Common Issues

1. **TA-Lib Installation Failures**
   - The build command in the `render.yaml` file includes fallback methods for installing TA-Lib
   - If you're still having issues, check the build logs in Render for specific errors

2. **Discord Authentication Errors**
   - Verify that your Discord application's redirect URL exactly matches the `DISCORD_REDIRECT_URI` environment variable
   - Check that your `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` are correct
   - Ensure your Discord application has the correct permissions

3. **Application Crashes on Startup**
   - Check the Render logs for specific error messages
   - Verify that all required environment variables are set correctly
   - Make sure the `gunicorn` command is pointing to the correct module

### Checking Logs

1. In your Render dashboard, select your web service
2. Click on the "Logs" tab to view real-time logs
3. Look for error messages that might indicate what's wrong

## Maintenance and Updates

### Updating Your Application

1. Push changes to your GitHub repository
2. Render will automatically detect the changes and rebuild your application

### Monitoring Usage

1. Render provides basic metrics in the "Metrics" tab
2. Monitor your usage to ensure you stay within the free tier limits

## Security Considerations

- The Discord client secret should never be exposed in client-side code
- All authentication is handled server-side for security
- User data is stored securely and passwords are never stored (OAuth only)
- The application uses HTTPS by default on Render.com

## Next Steps

After successful deployment, consider:

1. Adding custom domain name (available on paid Render plans)
2. Setting up monitoring and alerts
3. Implementing premium license tiers
4. Adding more authentication methods

---

Congratulations! Your AI Trading Assistant with Discord authentication is now deployed on Render.com and ready to use.