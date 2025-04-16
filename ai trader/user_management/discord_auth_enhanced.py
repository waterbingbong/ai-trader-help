# Enhanced Discord Authentication Module for AI Trading Assistant
# Handles Discord OAuth2 with role verification and Google Drive integration

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

# Import Google Drive integration
from user_management.google_drive_integration import GoogleDriveManager, DataSynchronizer, BackupManager

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', 'https://your-app-url.onrender.com/auth/discord/callback')
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10'
DISCORD_SERVER_ID = os.environ.get('DISCORD_SERVER_ID', '')  # ID of the Discord server to verify roles from

# Database simulation using file storage (for free tier compatibility)
# In production, this should be replaced with a proper database
DB_PATH = Path(__file__).parent / 'db'
USERS_DB_PATH = DB_PATH / 'users.json'
SESSIONS_DB_PATH = DB_PATH / 'sessions.json'
TOKENS_DB_PATH = DB_PATH / 'tokens.json'

# Ensure database directory exists
DB_PATH.mkdir(exist_ok=True)

# Initialize empty databases if they don't exist
if not USERS_DB_PATH.exists():
    with open(USERS_DB_PATH, 'w') as f:
        json.dump([], f)

if not SESSIONS_DB_PATH.exists():
    with open(SESSIONS_DB_PATH, 'w') as f:
        json.dump([], f)
        
if not TOKENS_DB_PATH.exists():
    with open(TOKENS_DB_PATH, 'w') as f:
        json.dump([], f)


class EnhancedUser(UserMixin):
    """Enhanced User class with Discord roles and Google Drive integration"""
    
    def __init__(self, id, username, email, discord_id=None, avatar=None, license_type='free', 
                 license_expiry=None, is_active=True, discord_roles=None, google_drive_connected=False):
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
        self.discord_roles = discord_roles or []
        self.google_drive_connected = google_drive_connected
    
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
            'last_login': self.last_login,
            'discord_roles': self.discord_roles,
            'google_drive_connected': self.google_drive_connected
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
            is_active=data.get('is_active', True),
            discord_roles=data.get('discord_roles', []),
            google_drive_connected=data.get('google_drive_connected', False)
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


class TokenManager:
    """Manages authentication tokens for Discord and Google"""
    
    @staticmethod
    def save_token(user_id, service, token_data):
        """Save authentication token"""
        try:
            with open(TOKENS_DB_PATH, 'r') as f:
                tokens = json.load(f)
            
            # Add timestamp to token data
            token_data['timestamp'] = datetime.now().isoformat()
            
            # Check if user exists in tokens
            user_exists = False
            for i, token_entry in enumerate(tokens):
                if token_entry.get('user_id') == user_id:
                    # Update service token
                    token_entry[service] = token_data
                    user_exists = True
                    break
            
            if not user_exists:
                # Create new user entry
                tokens.append({
                    'user_id': user_id,
                    service: token_data
                })
            
            with open(TOKENS_DB_PATH, 'w') as f:
                json.dump(tokens, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving token: {e}")
            return False
    
    @staticmethod
    def get_token(user_id, service):
        """Get authentication token"""
        try:
            with open(TOKENS_DB_PATH, 'r') as f:
                tokens = json.load(f)
            
            for token_entry in tokens:
                if token_entry.get('user_id') == user_id and service in token_entry:
                    return token_entry[service]
            
            return None
        except Exception as e:
            print(f"Error getting token: {e}")
            return None
    
    @staticmethod
    def refresh_discord_token(user_id):
        """Refresh Discord token if expired"""
        token_data = TokenManager.get_token(user_id, 'discord')
        if not token_data or 'refresh_token' not in token_data:
            return None
        
        # Check if token is expired
        expires_at = token_data.get('expires_at', 0)
        if expires_at > time.time():
            # Token is still valid
            return token_data
        
        # Refresh token
        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': token_data['refresh_token']
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(f"{DISCORD_API_ENDPOINT}/oauth2/token", data=data, headers=headers)
        
        if response.status_code == 200:
            new_token_data = response.json()
            # Calculate expiration time
            new_token_data['expires_at'] = time.time() + new_token_data.get('expires_in', 604800)  # Default to 7 days
            
            # Save new token
            TokenManager.save_token(user_id, 'discord', new_token_data)
            return new_token_data
        
        return None


class EnhancedAuthManager:
    """Enhanced authentication manager with Discord role verification and Google Drive integration"""
    
    @staticmethod
    def init_login_manager(app):
        """Initialize Flask-Login manager"""
        login_manager = LoginManager()
        login_manager.init_app(app)
        
        @login_manager.user_loader
        def load_user(user_id):
            return EnhancedUser.get_by_id(user_id)
        
        return login_manager
    
    @staticmethod
    def get_discord_auth_url():
        """Generate Discord OAuth2 authorization URL with guild membership scope"""
        params = {
            'client_id': DISCORD_CLIENT_ID,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify email guilds guilds.members.read'
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
        
        if response.status_code == 200:
            token_data = response.json()
            # Calculate expiration time
            token_data['expires_at'] = time.time() + token_data.get('expires_in', 604800)  # Default to 7 days
            return token_data
        
        return None
    
    @staticmethod
    def get_user_info(access_token):
        """Get user information from Discord API"""
        headers = {
            'Authorization': f"Bearer {access_token}"
        }
        
        response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me", headers=headers)
        return response.json() if response.status_code == 200 else None
    
    @staticmethod
    def get_user_guilds(access_token):
        """Get user's Discord servers"""
        headers = {
            'Authorization': f"Bearer {access_token}"
        }
        
        response = requests.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=headers)
        return response.json() if response.status_code == 200 else []
    
    @staticmethod
    def get_user_roles(access_token, guild_id, user_id):
        """Get user's roles in a specific Discord server"""
        headers = {
            'Authorization': f"Bot {os.environ.get('DISCORD_BOT_TOKEN')}"
        }
        
        response = requests.get(f"{DISCORD_API_ENDPOINT}/guilds/{guild_id}/members/{user_id}", headers=headers)
        
        if response.status_code == 200:
            member_data = response.json()
            return member_data.get('roles', [])
        
        return []
    
    @staticmethod
    def verify_server_membership(access_token, server_id):
        """Verify if user is a member of the specified Discord server"""
        guilds = EnhancedAuthManager.get_user_guilds(access_token)
        
        for guild in guilds:
            if guild.get('id') == server_id:
                return True
        
        return False
    
    @staticmethod
    def process_discord_login(code):
        """Process Discord OAuth login flow with role verification"""
        # Exchange code for token
        token_data = EnhancedAuthManager.exchange_code(code)
        if not token_data or 'access_token' not in token_data:
            return None, "Failed to exchange code for token"
        
        # Get user info from Discord
        user_info = EnhancedAuthManager.get_user_info(token_data['access_token'])
        if not user_info or 'id' not in user_info:
            return None, "Failed to get user info from Discord"
        
        # Verify server membership if server ID is specified
        if DISCORD_SERVER_ID:
            is_member = EnhancedAuthManager.verify_server_membership(token_data['access_token'], DISCORD_SERVER_ID)
            if not is_member:
                return None, "You must be a member of the required Discord server"
        
        # Get user roles if server ID and bot token are specified
        discord_roles = []
        if DISCORD_SERVER_ID and os.environ.get('DISCORD_BOT_TOKEN'):
            discord_roles = EnhancedAuthManager.get_user_roles(
                token_data['access_token'], DISCORD_SERVER_ID, user_info['id']
            )
        
        # Check if user exists
        user = EnhancedUser.get_by_discord_id(user_info['id'])
        
        if not user:
            # Create new user
            user = EnhancedUser(
                id=str(uuid.uuid4()),
                username=user_info['username'],
                email=user_info.get('email', ''),
                discord_id=user_info['id'],
                avatar=user_info.get('avatar'),
                license_type='free',
                license_expiry=(datetime.now() + timedelta(days=30)).isoformat() if user_info.get('email') else None,
                discord_roles=discord_roles
            )
            user.save()
        else:
            # Update user info
            user.username = user_info['username']
            user.avatar = user_info.get('avatar')
            user.last_login = datetime.now().isoformat()
            user.discord_roles = discord_roles
            user.save()
        
        # Save token data
        TokenManager.save_token(user.id, 'discord', token_data)
        
        return user, None
    
    @staticmethod
    def get_google_auth_url(user_id):
        """Generate Google OAuth2 authorization URL"""
        return GoogleDriveManager.get_auth_url(user_id)
    
    @staticmethod
    def process_google_login(code, state, user_id):
        """Process Google OAuth login flow"""
        # Exchange code for credentials
        credentials, error = GoogleDriveManager.exchange_code(code, state)
        if error:
            return False, error
        
        # Save credentials
        if not GoogleDriveManager.save_credentials(user_id, credentials):
            return False, "Failed to save Google credentials"
        
        # Create user folder in Google Drive
        root_folder_id = GoogleDriveManager.create_user_folder(user_id)
        if not root_folder_id:
            return False, "Failed to create Google Drive folder"
        
        # Update user's Google Drive connection status
        user = EnhancedUser.get_by_id(user_id)
        if user:
            user.google_drive_connected = True
            user.save()
        
        return True, "Google Drive connected successfully"
    
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
def init_enhanced_auth_routes(app):
    """Initialize enhanced authentication routes for Flask app"""
    
    @app.route('/auth/login')
    def login():
        """Redirect to Discord OAuth login"""
        return redirect(EnhancedAuthManager.get_discord_auth_url())
    
    @app.route('/auth/discord/callback')
    def discord_callback():
        """Handle Discord OAuth callback"""
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400
        
        user, error = EnhancedAuthManager.process_discord_login(code)
        if error:
            return jsonify({'error': error}), 400
        
        # Log user in
        login_user(user)
        
        # Store user ID in session for Google auth
        session['user_id'] = user.id
        
        # Redirect to dashboard
        return redirect('/')
    
    @app.route('/auth/google/connect')
    def google_connect():
        """Connect Google Drive account"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Generate Google auth URL
        auth_url, state = EnhancedAuthManager.get_google_auth_url(current_user.id)
        
        # Store state in session
        session['google_auth_state'] = state
        
        return redirect(auth_url)
    
    @app.route('/auth/google/callback')
    def google_callback():
        """Handle Google OAuth callback"""
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code or not state:
            return jsonify({'error': 'Invalid request parameters'}), 400
        
        # Verify state
        if state != session.get('google_auth_state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Process Google login
        success, message = EnhancedAuthManager.process_google_login(
            code, state, current_user.id
        )
        
        if not success:
            return jsonify({'error': message}), 400
        
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
            is_valid, message = EnhancedAuthManager.validate_license(current_user)
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email,
                    'avatar': current_user.avatar,
                    'license_type': current_user.license_type,
                    'license_valid': is_valid,
                    'license_message': message,
                    'discord_roles': current_user.discord_roles,
                    'google_drive_connected': current_user.google_drive_connected
                }
            })
        else:
            return jsonify({
                'authenticated': False
            })
    
    @app.route('/api/drive/sync', methods=['POST'])
    def sync_to_drive():
        """Sync local data to Google Drive"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not current_user.google_drive_connected:
            return jsonify({'error': 'Google Drive not connected'}), 400
        
        # Get local directory from request
        data = request.get_json()
        local_dir = data.get('local_dir')
        
        if not local_dir:
            return jsonify({'error': 'No local directory specified'}), 400
        
        # Get or create user's root folder
        root_folder_id = GoogleDriveManager.create_user_folder(current_user.id)
        if not root_folder_id:
            return jsonify({'error': 'Failed to access Google Drive folder'}), 500
        
        # Create synchronizer
        synchronizer = DataSynchronizer(current_user.id)
        
        # Sync directory
        success, message = synchronizer.sync_directory(local_dir, root_folder_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
    
    @app.route('/api/drive/download', methods=['POST'])
    def download_from_drive():
        """Download data from Google Drive"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not current_user.google_drive_connected:
            return jsonify({'error': 'Google Drive not connected'}), 400
        
        # Get parameters from request
        data = request.get_json()
        folder_id = data.get('folder_id')
        local_dir = data.get('local_dir')
        
        if not folder_id or not local_dir:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Create synchronizer
        synchronizer = DataSynchronizer(current_user.id)
        
        # Download and sync
        success, message = synchronizer.download_and_sync(folder_id, local_dir)
        
        return jsonify({
            'success': success,
            'message': message
        })
    
    @app.route('/api/drive/backup', methods=['POST'])
    def create_backup():
        """Create backup of user data"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not current_user.google_drive_connected:
            return jsonify({'error': 'Google Drive not connected'}), 400
        
        # Get parameters from request
        data = request.get_json()
        local_dirs = data.get('local_dirs', [])
        backup_name = data.get('backup_name')
        
        if not local_dirs:
            return jsonify({'error': 'No directories specified for backup'}), 400
        
        # Create backup
        success, message = BackupManager.create_backup(
            current_user.id, local_dirs, backup_name
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
    
    @app.route('/api/drive/backups', methods=['GET'])
    def list_backups():
        """List available backups"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not current_user.google_drive_connected:
            return jsonify({'error': 'Google Drive not connected'}), 400
        
        # List backups
        backups = BackupManager.list_backups(current_user.id)
        
        return jsonify({
            'backups': backups
        })
    
    @app.route('/api/drive/restore', methods=['POST'])
    def restore_backup():
        """Restore backup"""
        if not current_user.is_authenticated:
            return jsonify({'error': 'Not authenticated'}), 401
        
        if not current_user.google_drive_connected:
            return jsonify({'error': 'Google Drive not connected'}), 400
        
        # Get parameters from request
        data = request.get_json()
        backup_folder_id = data.get('backup_folder_id')
        local_dir = data.get('local_dir')
        
        if not backup_folder_id or not local_dir:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Restore backup
        success, message = BackupManager.restore_backup(
            current_user.id, backup_folder_id, local_dir
        )
        
        return jsonify({
            'success': success,
            'message': message
        })