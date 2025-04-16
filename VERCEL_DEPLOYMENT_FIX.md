# How to Fix Vercel Deployment Issues

If you're experiencing issues with deploying your AI Trading Assistant to Vercel, follow these step-by-step instructions to resolve them.

## Common Issue: Root Not Found

One of the most common issues is that Vercel can't find the root of your application. This happens when the configuration in your `vercel.json` file doesn't correctly point to your application files.

## Step-by-Step Fix

### 1. Update your vercel.json file

The updated `vercel.json` file should include:
- Proper path references with leading slashes
- A specific Python runtime
- Asset routing configuration
- All required environment variables including Google credentials

Here's how your `vercel.json` should look:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "dashboard/app_with_auth.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "15mb",
        "runtime": "python3.9"
      }
    }
  ],
  "routes": [
    {
      "src": "/assets/(.*)",
      "dest": "/dashboard/assets/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/dashboard/app_with_auth.py"
    }
  ],
  "env": {
    "GEMINI_API_KEY": "@gemini_api_key",
    "DISCORD_CLIENT_ID": "@discord_client_id",
    "DISCORD_CLIENT_SECRET": "@discord_client_secret",
    "DISCORD_REDIRECT_URI": "@discord_redirect_uri",
    "SECRET_KEY": "@secret_key",
    "GOOGLE_CLIENT_ID": "@google_client_id",
    "GOOGLE_CLIENT_SECRET": "@google_client_secret",
    "GOOGLE_REDIRECT_URI": "@google_redirect_uri"
  }
}
```

### 2. Verify Environment Variables in Vercel

1. Go to your Vercel dashboard
2. Select your project
3. Click on "Settings" tab
4. Select "Environment Variables" from the left menu
5. Verify that all these environment variables are set:
   - GEMINI_API_KEY
   - DISCORD_CLIENT_ID
   - DISCORD_CLIENT_SECRET
   - DISCORD_REDIRECT_URI
   - SECRET_KEY
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET
   - GOOGLE_REDIRECT_URI
6. If any are missing, add them with the correct values

### 3. Redeploy Your Application

1. Go to the "Deployments" tab in your Vercel project
2. Click "Redeploy" on your latest deployment
3. Wait for the deployment to complete

### 4. Check Deployment Logs

If you still encounter issues:

1. Click on the latest deployment
2. Go to "Functions" tab
3. Look for any error messages in the logs
4. Common issues include:
   - Missing dependencies: Check your `vercel_requirements.txt` file
   - Path issues: Ensure all file paths in your code are correct
   - Environment variable errors: Verify all variables are set correctly

## Additional Troubleshooting

### Python Version Issues

Vercel uses Python 3.9 by default. If your code requires a different version, specify it in the `vercel.json` file as shown above.

### Static Assets Not Loading

If your dashboard assets (CSS, JavaScript) aren't loading, ensure the assets route is correctly configured in your `vercel.json` file as shown above.

### Memory Limit Exceeded

If you see memory limit errors, you might need to optimize your code or increase the `maxLambdaSize` value in your `vercel.json` file (though 15mb is already quite high for the free tier).

## Need More Help?

If you continue to experience issues after following these steps, check the Vercel documentation or contact Vercel support for further assistance.