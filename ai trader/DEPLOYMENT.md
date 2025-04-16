# Quick Deployment Guide for AI Trading Assistant

This document provides a condensed guide for deploying the AI Trading Assistant online for free. For detailed instructions, please refer to the comprehensive [deployment guide](./docs/deployment_guide.md).

## Deployment Options

### Option 1: Render.com (Recommended)

1. Sign up for a free account at [Render](https://render.com/)
2. Connect your GitHub repository
3. Create a new Web Service with these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn dashboard.app:server`
   - Plan: Free
4. Add environment variable: `GEMINI_API_KEY`

### Option 2: PythonAnywhere

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Clone your repository and set up a virtual environment
3. Create a web app pointing to your Flask application
4. Configure environment variables

## Pre-Deployment Checklist

- [ ] Create a `.env` file from `.env.example` and add your Gemini API key
- [ ] Push your code to GitHub
- [ ] Ensure `Procfile` is in the root directory
- [ ] Verify all dependencies are in `requirements.txt`

## Post-Deployment

1. Test the dashboard functionality
2. Test the AI analysis features
3. Set up GitHub Actions for continuous deployment (optional)

## Free Hosting Limitations

- Limited computational resources
- Potential sleep/idle periods for inactive applications
- Storage constraints
- API usage limits

For questions or troubleshooting, refer to the hosting provider's documentation.