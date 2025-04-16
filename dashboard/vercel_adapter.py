from dashboard.app_with_auth import server

# Create WSGI application for Vercel serverless deployment
app = server

# This is required for Vercel to properly handle the WSGI application
if __name__ == '__main__':
    app.run()
