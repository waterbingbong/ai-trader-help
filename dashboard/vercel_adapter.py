# Vercel WSGI entry point
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the server from the dashboard module
from dashboard.app_with_auth import server

# Create WSGI application for Vercel serverless deployment
app = server

# This is required for Vercel to properly handle the WSGI application
if __name__ == '__main__':
    app.run()
