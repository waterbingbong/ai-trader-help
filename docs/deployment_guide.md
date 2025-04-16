# AI Trading Assistant - Free Deployment Guide

This guide provides step-by-step instructions for hosting the AI Trading Assistant online completely free of charge.

## Prerequisites

Before starting the deployment process, ensure you have:

1. A GitHub account (for source code hosting)
2. A Google account (for Gemini API access)
3. Basic familiarity with command line operations

## Step 1: Prepare Your Application

### 1.1 Set Up Environment Variables

Create a `.env` file in your project root to store sensitive information:

```
GEMINI_API_KEY=your_api_key_here
```

Modify `main.py` to load environment variables from the `.env` file instead of hardcoding the API key:

```python
# Replace the hardcoded API key with environment variable loading
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
```

### 1.2 Create a Procfile for Web Server

Create a file named `Procfile` (no extension) in the project root with the following content:

```
web: gunicorn dashboard.app:server
```

### 1.3 Update requirements.txt

Ensure your `requirements.txt` file includes all necessary dependencies. The current file already includes `gunicorn` for web server deployment.

## Step 2: Set Up Version Control

### 2.1 Initialize Git Repository (if not already done)

```bash
git init
git add .
git commit -m "Initial commit for deployment"
```

### 2.2 Create a GitHub Repository

1. Go to [GitHub](https://github.com/) and sign in
2. Click the '+' icon and select 'New repository'
3. Name your repository (e.g., "ai-trading-assistant")
4. Keep it public (for free deployment options)
5. Click 'Create repository'

### 2.3 Push Your Code to GitHub

```bash
git remote add origin https://github.com/yourusername/ai-trading-assistant.git
git branch -M main
git push -u origin main
```

## Step 3: Deploy the Backend

### Option A: Deploy on Render.com (Recommended)

1. Sign up for a free account at [Render](https://render.com/)
2. Click 'New +' and select 'Web Service'
3. Connect your GitHub repository
4. Configure your service:
   - Name: ai-trading-assistant
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn dashboard.app:server`
   - Select the free plan
5. Add environment variables:
   - Click 'Environment' tab
   - Add `GEMINI_API_KEY` with your API key value
6. Click 'Create Web Service'

### Option B: Deploy on PythonAnywhere

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Go to the Dashboard and open a Bash console
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/ai-trading-assistant.git
   ```
4. Set up a virtual environment:
   ```bash
   cd ai-trading-assistant
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Create a web app:
   - Go to the Web tab
   - Click 'Add a new web app'
   - Select 'Manual configuration' and 'Python'
   - Set source code directory to `/home/yourusername/ai-trading-assistant`
   - Set working directory to `/home/yourusername/ai-trading-assistant`
   - Set WSGI configuration file to point to your Flask app
6. Edit the WSGI configuration file:
   ```python
   import sys
   import os
   path = '/home/yourusername/ai-trading-assistant'
   if path not in sys.path:
       sys.path.append(path)
   from dotenv import load_dotenv
   load_dotenv(os.path.join(path, '.env'))
   from dashboard.app import server as application
   ```
7. Add environment variables in the `.env` file
8. Reload the web app

## Step 4: Set Up Database Storage

### 4.1 Use SQLite for Development

For a free deployment, SQLite is a good option for the knowledge base storage:

1. Update the knowledge base implementation to use SQLite:
   ```python
   # In ai_integration/knowledge_base.py
   import sqlite3
   
   class KnowledgeBase:
       def __init__(self, db_path='knowledge_base.db'):
           self.db_path = db_path
           self._initialize_db()
           
       def _initialize_db(self):
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()
           # Create tables for knowledge base storage
           # ...
           conn.commit()
           conn.close()
   ```

### 4.2 For Production (Optional)

For a more robust solution, consider using a free tier of a cloud database:

1. [ElephantSQL](https://www.elephantsql.com/) - Free PostgreSQL database (20MB)
2. [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Free MongoDB cluster

## Step 5: Continuous Deployment

### 5.1 Set Up GitHub Actions

Create a file `.github/workflows/deploy.yml` with the following content:

```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        uses: JorgeLNJunior/render-deploy@v1.3.2
        with:
          service_id: ${{ secrets.RENDER_SERVICE_ID }}
          api_key: ${{ secrets.RENDER_API_KEY }}
```

### 5.2 Configure Secrets in GitHub

1. Go to your GitHub repository
2. Click 'Settings' > 'Secrets' > 'New repository secret'
3. Add the following secrets:
   - `RENDER_SERVICE_ID`: Your Render service ID
   - `RENDER_API_KEY`: Your Render API key

## Step 6: Testing Your Deployment

1. Visit your deployed application URL (provided by Render or PythonAnywhere)
2. Test the dashboard functionality
3. Test the AI analysis features using the API endpoints

## Step 7: Maintenance and Updates

1. Make changes to your local repository
2. Commit and push changes to GitHub
3. GitHub Actions will automatically deploy the changes to your hosting provider

## Limitations of Free Hosting

1. **Performance**: Free tiers have limited resources and may be slower
2. **Uptime**: Free services may have limitations on uptime or go to sleep after inactivity
3. **Storage**: Limited storage space for your database and files
4. **API Limits**: Gemini API has usage limits on the free tier

## Troubleshooting

### Common Issues

1. **Application crashes**: Check the logs in your hosting provider dashboard
2. **API key issues**: Verify environment variables are correctly set
3. **Database connection problems**: Check connection strings and credentials
4. **Deployment failures**: Review GitHub Actions logs for errors

### Getting Help

If you encounter issues, check the following resources:

1. Render documentation: [https://render.com/docs](https://render.com/docs)
2. PythonAnywhere help pages: [https://help.pythonanywhere.com/](https://help.pythonanywhere.com/)
3. GitHub Actions documentation: [https://docs.github.com/en/actions](https://docs.github.com/en/actions)