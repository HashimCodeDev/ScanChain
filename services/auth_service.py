import json
import os
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional

class AuthService:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.users_file = os.path.join(self.data_dir, 'users.json')
        self.sessions_file = os.path.join(self.data_dir, 'sessions.json')
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        # Load demo users
        self._load_demo_users()

    def _initialize_files(self):
        """Initialize JSON files with default structure"""
        files = [
            (self.users_file, {"users": [], "lastUserId": 0}),
            (self.sessions_file, {"sessions": []})
        ]
        
        for file_path, default_data in files:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2)

    def _load_demo_users(self):
        """Load demo users for testing"""
        users_data = self._load_users()
        
        # Check if demo users already exist
        existing_emails = {user['email'] for user in users_data['users']}
        
        demo_users = [
            {
                'username': 'techcorp_mfg',
                'email': 'manufacturer@techcorp.com',
                'password': 'demo123',
                'fullName': 'TechCorp Manufacturing',
                'role': 'manufacturer',
                'companyName': 'TechCorp Industries'
            },
            {
                'username': 'logistics_supplier',
                'email': 'supplier@logistics.com',
                'password': 'demo123',
                'fullName': 'Global Logistics Supplier',
                'role': 'supplier',
                'companyName': 'Global Logistics Inc'
            }
        ]
        
        for demo_user in demo_users:
            if demo_user['email'] not in existing_emails:
                self.register_user(
                    email=demo_user['email'],
                    password=demo_user['password'],
                    full_name=demo_user['fullName'],
                    role=demo_user['role'],
                    company_name=demo_user['companyName']
                )

    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": [], "lastUserId": 0}

    def _save_users(self, users_data: Dict):
        """Save users to JSON file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")

    def _load_sessions(self) -> Dict:
        """Load sessions from JSON file"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"sessions": []}

    def _save_sessions(self, sessions_data: Dict):
        """Save sessions to JSON file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")

    def register_user(self, email: str, password: str, full_name: str, 
                     role: str = 'user', company_name: str = '') -> Dict:
        """Register a new user"""
        users_data = self._load_users()
        
        # Check if user already exists
        for user in users_data['users']:
            if user['email'] == email:
                return {'success': False, 'error': 'User already exists'}
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = {
            'id': users_data['lastUserId'] + 1,
            'username': email.split('@')[0],
            'email': email,
            'password': password_hash,
            'fullName': full_name,
            'role': role,
            'companyName': company_name,
            'verified': True,
            'createdAt': datetime.utcnow().isoformat(),
            'lastLogin': None,
            'blockchainHashes': [],
            'profileData': {
                'totalBatches': 0,
                'totalScans': 0,
                'joinedAt': datetime.utcnow().isoformat()
            }
        }
        
        users_data['users'].append(new_user)
        users_data['lastUserId'] += 1
        self._save_users(users_data)
        
        # Remove password from response
        user_response = new_user.copy()
        del user_response['password']
        
        return {'success': True, 'user': user_response}

    def login_user(self, email: str, password: str) -> Dict:
        """Authenticate user login"""
        users_data = self._load_users()
        
        # Find user
        user = None
        for u in users_data['users']:
            if u['email'] == email:
                user = u
                break
        
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return {'success': False, 'error': 'Invalid password'}
        
        # Update last login
        user['lastLogin'] = datetime.utcnow().isoformat()
        self._save_users(users_data)
        
        # Create session
        session_data = {
            'userId': user['id'],
            'email': user['email'],
            'loginTime': datetime.utcnow().isoformat(),
            'lastActivity': datetime.utcnow().isoformat()
        }
        
        sessions_data = self._load_sessions()
        sessions_data['sessions'].append(session_data)
        self._save_sessions(sessions_data)
        
        # Remove password from response
        user_response = user.copy()
        del user_response['password']
        
        return {'success': True, 'user': user_response}

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        users_data = self._load_users()
        
        for user in users_data['users']:
            if user['id'] == user_id:
                # Remove password from response
                user_response = user.copy()
                del user_response['password']
                return user_response
        
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        users_data = self._load_users()
        
        for user in users_data['users']:
            if user['email'] == email:
                # Remove password from response
                user_response = user.copy()
                del user_response['password']
                return user_response
        
        return None

    def associate_blockchain_hash(self, user_id: int, hash_data: Dict) -> bool:
        """Associate blockchain hash with user"""
        users_data = self._load_users()
        
        for user in users_data['users']:
            if user['id'] == user_id:
                hash_record = {
                    **hash_data,
                    'timestamp': datetime.utcnow().isoformat()
                }
                user['blockchainHashes'].append(hash_record)
                user['profileData']['totalBatches'] += 1
                self._save_users(users_data)
                return True
        
        return False

    def update_user_activity(self, user_id: int, activity_type: str):
        """Update user activity statistics"""
        users_data = self._load_users()
        
        for user in users_data['users']:
            if user['id'] == user_id:
                if activity_type == 'scan':
                    user['profileData']['totalScans'] += 1
                elif activity_type == 'batch':
                    user['profileData']['totalBatches'] += 1
                
                user['lastLogin'] = datetime.utcnow().isoformat()
                self._save_users(users_data)
                break
