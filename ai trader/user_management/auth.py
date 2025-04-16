# Authentication Module for AI Trading Assistant
# Handles user authentication, session management, and license validation

import os
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import requests
from flask import Flask, request, redirect, session, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', 'https://your-app-url.onrender.com/auth/discord/callback')
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'

# Database simulation using file storage (for free tier compatibility)
# In production, this should be replaced with a proper database
DB_PATH = Path(__file__).parent / 'db'
USERS_DB_PATH = DB_PATH / 'users.json'
SESSIONS_DB_PATH = DB_PATH / 'sessions.json'

# Ensure database directory exists
DB_PATH.mkdir(exist_ok=True)

# Initialize empty databases if they don't exist
if not USERS_DB_PATH.exists():
    with open(USERS_DB_PATH, 'w') as f:
        json.dump([], f)

if not SESSIONS_DB_PATH.exists():
    with open(SESSIONS_DB_PATH, 'w') as f:
        json.dump([], f)


class User(UserMixin):
    """User class for authentication and license management"""
    
    def __init__(self, id, username, email, discord_id=None, avatar=None, license_type='free', 
                 license_expiry=None, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.discord_id = discord_id
        self.avatar = avatar
        self.license_type = license_type
        self.license_expiry = license_expiry
        self.is_active = is_active
        self.created_at = datetime.now().isoformat()
        self.last_login = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'discord_id': self.discord_id,
            'avatar': self.avatar,
            'license_type': self.license_type,
            'license_expiry': self.license_expiry,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            username=data['username'],
            email=data['email'],
            discord_id=data.get('discord_id'),
            avatar=data.get('avatar'),
            license_type=data.get('license_type', 'free'),
            license_expiry=data.get('license_expiry'),
            is_active=data.get('is_active', True)
        )
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID"""
        try:
            with open(USERS_DB_PATH, 'r') as f:
                users = json.load(f)
                for user_data in users:
                    if user_data['id'] == user_id:
                        return cls.from_dict(user_data)
        except Exception as e:
            print(f"Error getting user by ID: {e}")
        return None
    
    @classmethod
    def get_by_discord_id(cls, discord_id):
        """Get user by Discord ID"""
        try:
            with open(USERS_DB_PATH, 'r') as f:
                users = json.load(f)
                for user_data in users:
                    if user_data.get('discord_id') == discord_id:
                        return cls.from_dict(user_data)
        except Exception as e:
            print(f"Error getting user by Discord ID: {e}")
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        try:
            with open(USERS_DB_PATH, 'r') as f:
                users = json.load(f)
                for user_data in users:
                    if user_data['email'] == email:
                        return cls.from_dict(user_data)
        except Exception as e:
            print(f"Error getting user by email: {e}")
        return None
    
    def save(self):
        """Save user to database"""
        try:
            with open(USERS_DB_PATH, 'r') as f:
                users = json.load(f)
            
            # Update existing user or add new user
            user_exists = False
            for i, user_data in enumerate(users):
                if user_data['id'] == self.id:
                    users[i] = self.to_dict()
                    user_exists = True
                    break
            
            if not user_exists:
                users.append(self.to_dict())
            
            with open(USERS_DB_PATH, 'w') as f:
                json.dump(users, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving user: {e}")
            return False


class AuthManager:
    """Manages authentication and license validation"""
    
    @staticmethod
    def init_login_manager(app):
        """Initialize Flask-Login manager"""
        login_manager = LoginManager()
        login_manager.init_app(app)
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.get_by_id(user_id)
        
        return login_manager
    
    @staticmethod
    def get_discord_auth_url():
        """Generate Discord OAuth2 authorization URL"""
        params = {
            'client_id': DISCORD_CLIENT_ID,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify email'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{DISCORD_API_ENDPOINT}/oauth2/authorize?{query_string}"
    
    @staticmethod
    def exchange_code(code):
        """Exchange authorization code for access token"""
        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(f"{DISCORD_API_ENDPOINT}/oauth2/token", data=data, headers=headers)
        return response.json() if response.status_code == 200 else None
    
    @staticmethod
    def get_user_info(access_token):
        """Get user information from Discord API"""
        headers = {
            'Authorization': f"Bearer {access_token}"
        }
        
        response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me", headers=headers)
        return response.json() if response.status_code == 200 else None
    
    @staticmethod
    def process_discord_login(code):
        """Process Discord OAuth login flow"""
        # Exchange code for token
        token_data = AuthManager.exchange_code(code)
        if not token_data or 'access_token' not in token_data:
            return None, "Failed to exchange code for token"
        
        # Get user info from Discord
        user_info = AuthManager.get_user_info(token_data['access_token'])
        if not user_info or 'id' not in user_info:
            return None, "Failed to get user info from Discord"
        
        # Check if user exists
        user = User.get_by_discord_id(user_info['id'])
        
        if not user:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                username=user_info['username'],
                email=user_info.get('email', ''),
                discord_id=user_info['id'],
                avatar=user_info.get('avatar'),
                license_type='free',
                license_expiry=(datetime.now() + timedelta(days=30)).isoformat() if user_info.get('email') else None
            )
            user.save()
        else:
            # Update user info
            user.username = user_info['username']
            user.avatar = user_info.get('avatar')
            user.last_login = datetime.now().isoformat()
            user.save()
        
        return user, None
    
    @staticmethod
    def validate_license(user):
        """Validate user license"""
        if not user:
            return False, "User not found"
        
        # Free license is always valid
        if user.license_type == 'free':
            return True, "Free license"
        
        # Check license expiry
        if user.license_expiry:
            expiry_date = datetime.fromisoformat(user.license_expiry)
            if expiry_date > datetime.now():
                return True, "Valid license"
            else:
                # Downgrade to free license if premium expired
                user.license_type = 'free'
                user.save()
                return True, "License expired, downgraded to free"
        
        return False, "Invalid license"


# Initialize routes for a Flask application
def init_auth_routes(app):
    """Initialize authentication routes for Flask app"""
    
    @app.route('/auth/login')
    def login():
        """Redirect to Discord OAuth login"""
        return redirect(AuthManager.get_discord_auth_url())
    
    @app.route('/auth/discord/callback')
    def discord_callback():
        """Handle Discord OAuth callback"""
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400
        
        user, error = AuthManager.process_discord_login(code)
        if error:
            return jsonify({'error': error}), 400
        
        # Log user in
        login_user(user)
        
        # Redirect to dashboard
        return redirect('/')
    
    @app.route('/auth/logout')
    def logout():
        """Log user out"""
        logout_user()
        return redirect('/')
    
    @app.route('/auth/status')
    def auth_status():
        """Get current authentication status"""
        if current_user.is_authenticated:
            is_valid, message = AuthManager.validate_license(current_user)
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'avatar': current_user.avatar,
                    'license_type': current_user.license_type,
                    'license_valid': is_valid,
                    'license_message': message
                }
            })
        else:
            return jsonify({
                'authenticated': False
            })