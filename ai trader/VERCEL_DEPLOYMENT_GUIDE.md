# AI Trading Assistant - Vercel Deployment Guide 🚀

This beginner-friendly guide will help you deploy the AI Trading Assistant on Vercel, step by step. No prior experience needed!

## Before You Start ✨

Let's get everything ready! Follow these simple steps:

### 1. Create a GitHub Account 📝
- Visit [github.com](https://github.com) and click "Sign Up"
- Choose a username and password
- Verify your email address
- ✅ Success: You can log into GitHub

### 2. Get the Trading Assistant Code
- While logged into GitHub, visit the AI Trading Assistant repository URL
  - If you don't have the URL, search for "AI Trading Assistant" on GitHub
  - Make sure you're looking at the main repository (not a fork)
- Look for the "Fork" button in the top-right corner and click it
- On the fork page, keep the default settings and click "Create fork"
- Wait for the fork to complete (usually takes less than a minute)
- ✅ Success: You now have your own copy of the code at github.com/YOUR-USERNAME/ai-trading-assistant

### 3. Set Up Vercel Account 🌐
- Go to [vercel.com](https://vercel.com)
- Click "Sign Up"
- Choose "Continue with GitHub" (use the account you just created)
- Select the free "Hobby" plan
- ✅ Success: You can access the Vercel dashboard

### 4. Create Discord Application 🎮
- Visit [Discord Developer Portal](https://discord.com/developers/applications)
- Click "New Application" (top-right)
- Name: "AI Trading Assistant" (or any name you prefer)
- Accept the terms and click "Create"
- Go to "OAuth2" in the left menu, then select the "General" tab
- Under "Redirects", click "Add Redirect"
- Enter: `https://your-project-name.vercel.app/callback`
  (Replace "your-project-name" with what you'll name your project on Vercel)
- Click "Save Changes" at the bottom of the page
- Stay on the same page and find these values:
  - Client ID: Copy the string under "Client ID" (it's a long number)
  - Client Secret: Click "Reset Secret" to generate a new one, then copy it immediately
  - ⚠️ Important: Save these values securely - you'll need them for Vercel setup
- ✅ Success: You have your Discord credentials

### 5. Get Google Gemini API Key 🔑
- Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- Click "Create API Key"
- Copy your API key (you'll need it later)
- ✅ Success: You have your Gemini API key

### 6. Set Up Google Drive API (New!) 📁
- Visit [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project (or select an existing one)
- Go to "APIs & Services" > "Library"
- Search for "Google Drive API" and enable it
- Go to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "OAuth client ID"
- Application type: "Web application"
- Name: "AI Trading Assistant"
- Authorized JavaScript origins: Add `https://your-project-name.vercel.app`
- Authorized redirect URIs: Add `https://your-project-name.vercel.app/auth/google/callback`
- Click "Create"
- Copy the Client ID and Client Secret (you'll need these for Vercel setup)
- ✅ Success: You have your Google Drive API credentials

## Deployment Steps 🛠️

### Step 1: Connect Your Code
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Find your forked repository in the list
4. Click "Import"

### Step 2: Configure Project Settings
1. Project Name:
   - Type a unique name (this will be your site's URL)
   - Example: "my-trading-assistant"

2. Framework Settings:
   - Framework: Select "Other"
   - Root Directory: Leave as is
   - Build Command: Leave empty

3. Add Environment Variables (Click "Environment Variables"):
   ```
   GEMINI_API_KEY=your-gemini-api-key
   SECRET_KEY=make-up-a-random-32-character-string
   DISCORD_CLIENT_ID=your-discord-client-id
   DISCORD_CLIENT_SECRET=your-discord-client-secret
   DISCORD_REDIRECT_URI=https://your-project-name.vercel.app/callback
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=https://your-project-name.vercel.app/auth/google/callback
   DISCORD_SERVER_ID=your-discord-server-id (optional)
   ```
   
   Important notes about these variables:
   - For GEMINI_API_KEY: Paste the key you copied from Google AI Studio
   - For SECRET_KEY: Create a random string (e.g., "abcdef1234567890abcdef1234567890")
   - For DISCORD values: Copy exactly from your Discord Developer Portal
   - For GOOGLE values: Copy exactly from your Google Cloud Console
   - For DISCORD_REDIRECT_URI and GOOGLE_REDIRECT_URI: Replace "your-project-name" with the exact name you chose above
   - For DISCORD_SERVER_ID: If you want to verify user roles, enter your Discord server ID (optional)
   - Double-check for typos or extra spaces (common error source)

4. Click "Deploy"
- Wait for the build to complete (this may take a few minutes)
- ✅ Success: You'll see "Congratulations!" and a link to your site

## Testing Your Site 🧪

1. Click the link to your site (or visit https://your-project-name.vercel.app)
2. Click "Login with Discord"
3. If asked, authorize the application
4. You should see the trading dashboard
   - If the dashboard loads but shows errors, check your Gemini API key
   - If login fails, verify your Discord configuration
5. Try the AI chat feature to confirm Gemini integration is working
6. Test the Google Drive integration:
   - Go to the Google Drive section in the dashboard
   - Click "Connect Google Drive"
   - Authorize the application when prompted
   - Try creating a backup of your data
- ✅ Success: You're logged in and ready to use the assistant with all features!

## Common Problems & Solutions 🔧

### "Build Failed" Message
- Check that all environment variables are set correctly
- Make sure there are no spaces before/after your API keys
- Try deploying again
- Check Vercel logs for specific error messages (click "View Logs" in your project)

### Discord Login Not Working
- Verify your DISCORD_REDIRECT_URI matches your site's URL exactly
- Check that you copied the Client ID and Secret correctly
- Make sure you saved the redirect URL in Discord developer portal
- Common error: Discord redirect URL must match EXACTLY (including https:// and no trailing slash)

### Google Drive Integration Not Working
- Verify your GOOGLE_REDIRECT_URI matches your site's URL exactly
- Check that you copied the Google Client ID and Secret correctly
- Make sure you enabled the Google Drive API in your Google Cloud project
- Verify that you added the correct redirect URI in the Google Cloud Console

### Site Shows Error Page
- Wait 5 minutes and refresh (sometimes it takes time to start up)
- Check the Vercel deployment logs for red error messages
- If needed, click "Redeploy" in Vercel dashboard
- Error 500: Usually means environment variables are incorrect
- Error 404: Check that your deployment completed successfully

## Need More Help? 💡

- Check Vercel's deployment logs (click "View Logs" in your project)
- Visit [Vercel Support](https://vercel.com/support)
- Review [Discord Developer Docs](https://discord.com/developers/docs)
- Check [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)

Congratulations on deploying your AI Trading Assistant! 🎉