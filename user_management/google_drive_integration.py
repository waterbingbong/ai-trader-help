# Google Drive Integration Module for AI Trading Assistant
# Handles Google Drive API authentication, file operations, and synchronization

import os
import json
import time
import pickle
from datetime import datetime, timedelta
from pathlib import Path
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import hashlib

# Google Drive API Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'https://your-app-url.onrender.com/auth/google/callback')
GOOGLE_API_SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Token storage path
TOKEN_PATH = Path(__file__).parent / 'tokens'
TOKEN_PATH.mkdir(exist_ok=True)

class GoogleDriveManager:
    """Manages Google Drive integration for user data storage"""
    
    @staticmethod
    def get_auth_url(user_id):
        """Generate Google OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GOOGLE_API_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        
        # Store state for verification
        state = hashlib.sha256(user_id.encode()).hexdigest()
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        
        # Save flow for later use
        with open(TOKEN_PATH / f"{state}_flow.pickle", 'wb') as f:
            pickle.dump(flow, f)
        
        return auth_url, state
    
    @staticmethod
    def exchange_code(code, state):
        """Exchange authorization code for access token"""
        try:
            # Load saved flow
            flow_path = TOKEN_PATH / f"{state}_flow.pickle"
            if not flow_path.exists():
                return None, "Invalid state parameter"
                
            with open(flow_path, 'rb') as f:
                flow = pickle.load(f)
            
            # Exchange code for token
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Clean up flow file
            flow_path.unlink()
            
            return credentials, None
        except Exception as e:
            return None, f"Error exchanging code: {str(e)}"
    
    @staticmethod
    def save_credentials(user_id, credentials):
        """Save user credentials"""
        try:
            creds_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            with open(TOKEN_PATH / f"{user_id}_token.json", 'w') as f:
                json.dump(creds_dict, f)
            
            return True
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    @staticmethod
    def load_credentials(user_id):
        """Load user credentials"""
        try:
            token_path = TOKEN_PATH / f"{user_id}_token.json"
            if not token_path.exists():
                return None
                
            with open(token_path, 'r') as f:
                creds_dict = json.load(f)
            
            # Convert expiry string back to datetime
            if creds_dict.get('expiry'):
                creds_dict['expiry'] = datetime.fromisoformat(creds_dict['expiry'])
            
            credentials = Credentials.from_authorized_user_info(creds_dict)
            
            # Check if credentials are expired and refresh if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(requests.Request())
                GoogleDriveManager.save_credentials(user_id, credentials)
            
            return credentials
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return None
    
    @staticmethod
    def get_drive_service(user_id):
        """Get Google Drive service for a user"""
        credentials = GoogleDriveManager.load_credentials(user_id)
        if not credentials:
            return None
        
        return build('drive', 'v3', credentials=credentials)
    
    @staticmethod
    def create_user_folder(user_id):
        """Create root folder for user in Google Drive"""
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return None
        
        # Check if root folder already exists
        results = service.files().list(
            q=f"name='AI_Trading_Assistant_{user_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        if results.get('files'):
            # Folder already exists
            return results['files'][0]['id']
        
        # Create new folder
        folder_metadata = {
            'name': f'AI_Trading_Assistant_{user_id}',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    
    @staticmethod
    def create_subfolder(user_id, parent_folder_id, subfolder_name):
        """Create subfolder within a parent folder"""
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return None
        
        # Check if subfolder already exists
        results = service.files().list(
            q=f"name='{subfolder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        if results.get('files'):
            # Subfolder already exists
            return results['files'][0]['id']
        
        # Create new subfolder
        folder_metadata = {
            'name': subfolder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    
    @staticmethod
    def upload_file(user_id, folder_id, file_path, file_name=None):
        """Upload a file to Google Drive"""
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return None
        
        if file_name is None:
            file_name = Path(file_path).name
        
        # Check if file already exists
        results = service.files().list(
            q=f"name='{file_name}' and '{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name, modifiedTime)'
        ).execute()
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        if results.get('files'):
            # Update existing file
            file_id = results['files'][0]['id']
            file = service.files().update(
                fileId=file_id,
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
        else:
            # Upload new file
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
        
        return file.get('id')
    
    @staticmethod
    def download_file(user_id, file_id, destination_path):
        """Download a file from Google Drive"""
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return False
        
        try:
            request = service.files().get_media(fileId=file_id)
            
            with open(destination_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            return True
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    
    @staticmethod
    def list_files(user_id, folder_id):
        """List files in a folder"""
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return []
        
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name, mimeType, modifiedTime, size)'
        ).execute()
        
        return results.get('files', [])
    
    @staticmethod
    def delete_file(user_id, file_id):
        """Delete a file from Google Drive"""
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return False
        
        try:
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False


class DataSynchronizer:
    """Manages synchronization between local files and Google Drive"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.sync_log_path = TOKEN_PATH / f"{user_id}_sync_log.json"
        self.load_sync_log()
    
    def load_sync_log(self):
        """Load synchronization log"""
        if self.sync_log_path.exists():
            with open(self.sync_log_path, 'r') as f:
                self.sync_log = json.load(f)
        else:
            self.sync_log = {
                'last_sync': None,
                'files': {}
            }
    
    def save_sync_log(self):
        """Save synchronization log"""
        with open(self.sync_log_path, 'w') as f:
            json.dump(self.sync_log, f, indent=2)
    
    def get_file_hash(self, file_path):
        """Calculate file hash for change detection"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return None
    
    def sync_file(self, local_path, remote_folder_id, file_name=None):
        """Synchronize a single file"""
        if file_name is None:
            file_name = Path(local_path).name
        
        # Calculate current file hash
        current_hash = self.get_file_hash(local_path)
        if not current_hash:
            return False, "Failed to calculate file hash"
        
        # Check if file has changed since last sync
        file_key = f"{remote_folder_id}/{file_name}"
        file_info = self.sync_log['files'].get(file_key, {})
        last_hash = file_info.get('hash')
        drive_file_id = file_info.get('drive_id')
        
        if current_hash == last_hash and drive_file_id:
            # File hasn't changed, no need to sync
            return True, "File already in sync"
        
        # Upload file to Google Drive
        drive_file_id = GoogleDriveManager.upload_file(
            self.user_id, remote_folder_id, local_path, file_name
        )
        
        if not drive_file_id:
            return False, "Failed to upload file to Google Drive"
        
        # Update sync log
        self.sync_log['files'][file_key] = {
            'hash': current_hash,
            'drive_id': drive_file_id,
            'last_sync': datetime.now().isoformat()
        }
        self.save_sync_log()
        
        return True, "File synchronized successfully"
    
    def sync_directory(self, local_dir, remote_folder_id, recursive=True):
        """Synchronize an entire directory"""
        local_path = Path(local_dir)
        if not local_path.exists() or not local_path.is_dir():
            return False, "Local directory does not exist"
        
        success_count = 0
        error_count = 0
        
        # Process all files in the directory
        for item in local_path.iterdir():
            if item.is_file():
                # Sync file
                success, _ = self.sync_file(str(item), remote_folder_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
            elif item.is_dir() and recursive:
                # Create subfolder and sync recursively
                subfolder_name = item.name
                subfolder_id = GoogleDriveManager.create_subfolder(
                    self.user_id, remote_folder_id, subfolder_name
                )
                
                if subfolder_id:
                    sub_success, sub_message = self.sync_directory(str(item), subfolder_id, recursive)
                    if sub_success:
                        success_count += 1
                    else:
                        error_count += 1
        
        # Update last sync time
        self.sync_log['last_sync'] = datetime.now().isoformat()
        self.save_sync_log()
        
        if error_count == 0:
            return True, f"Directory synchronized successfully ({success_count} items)"
        else:
            return False, f"Directory sync completed with errors ({error_count} errors, {success_count} successes)"
    
    def download_and_sync(self, remote_folder_id, local_dir):
        """Download files from Google Drive and sync with local directory"""
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        
        # List files in remote folder
        files = GoogleDriveManager.list_files(self.user_id, remote_folder_id)
        
        success_count = 0
        error_count = 0
        
        for file in files:
            file_name = file['name']
            file_id = file['id']
            local_file_path = local_path / file_name
            
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                # Create local subfolder and sync recursively
                subfolder_path = local_path / file_name
                subfolder_path.mkdir(exist_ok=True)
                
                sub_success, _ = self.download_and_sync(file_id, str(subfolder_path))
                if sub_success:
                    success_count += 1
                else:
                    error_count += 1
            else:
                # Download file
                success = GoogleDriveManager.download_file(
                    self.user_id, file_id, str(local_file_path)
                )
                
                if success:
                    # Update sync log
                    file_key = f"{remote_folder_id}/{file_name}"
                    current_hash = self.get_file_hash(str(local_file_path))
                    
                    if current_hash:
                        self.sync_log['files'][file_key] = {
                            'hash': current_hash,
                            'drive_id': file_id,
                            'last_sync': datetime.now().isoformat()
                        }
                    
                    success_count += 1
                else:
                    error_count += 1
        
        # Save sync log
        self.sync_log['last_sync'] = datetime.now().isoformat()
        self.save_sync_log()
        
        if error_count == 0:
            return True, f"Downloaded and synchronized successfully ({success_count} items)"
        else:
            return False, f"Download completed with errors ({error_count} errors, {success_count} successes)"


# Backup system for user data
class BackupManager:
    """Manages automatic backups of user data to Google Drive"""
    
    @staticmethod
    def create_backup(user_id, local_dirs, backup_name=None):
        """Create a backup of user data"""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get or create user's root folder
        root_folder_id = GoogleDriveManager.create_user_folder(user_id)
        if not root_folder_id:
            return False, "Failed to create root folder"
        
        # Create backup folder
        backup_folder_id = GoogleDriveManager.create_subfolder(
            user_id, root_folder_id, f"Backup_{backup_name}"
        )
        
        if not backup_folder_id:
            return False, "Failed to create backup folder"
        
        # Sync each directory to the backup folder
        synchronizer = DataSynchronizer(user_id)
        success_count = 0
        error_count = 0
        
        for local_dir in local_dirs:
            # Create subfolder for each directory
            dir_name = Path(local_dir).name
            subfolder_id = GoogleDriveManager.create_subfolder(
                user_id, backup_folder_id, dir_name
            )
            
            if subfolder_id:
                success, _ = synchronizer.sync_directory(local_dir, subfolder_id)
                if success:
                    success_count += 1
                else:
                    error_count += 1
            else:
                error_count += 1
        
        if error_count == 0:
            return True, f"Backup created successfully ({success_count} directories)"
        else:
            return False, f"Backup completed with errors ({error_count} errors, {success_count} successes)"
    
    @staticmethod
    def list_backups(user_id):
        """List available backups for a user"""
        # Get user's root folder
        root_folder_id = GoogleDriveManager.create_user_folder(user_id)
        if not root_folder_id:
            return []
        
        # List files in root folder
        service = GoogleDriveManager.get_drive_service(user_id)
        if not service:
            return []
        
        results = service.files().list(
            q=f"'{root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and name contains 'Backup_' and trashed=false",
            spaces='drive',
            fields='files(id, name, createdTime)'
        ).execute()
        
        return results.get('files', [])
    
    @staticmethod
    def restore_backup(user_id, backup_folder_id, local_dir):
        """Restore a backup to local directory"""
        # Create synchronizer
        synchronizer = DataSynchronizer(user_id)
        
        # Download and sync backup folder
        return synchronizer.download_and_sync(backup_folder_id, local_dir)