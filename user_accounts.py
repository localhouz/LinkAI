"""
User Accounts & Authentication System
Handles user registration, login, profiles, and data persistence
"""

import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import re


class UserAccountManager:
    """
    Manages user accounts, authentication, and profiles

    For mobile implementation:
    - iOS: Use Firebase Auth or AWS Amplify
    - Android: Firebase Auth or custom backend
    - React Native: Firebase Auth
    """

    def __init__(self, db_path: str = "golf_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Creates user-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                handicap REAL DEFAULT 0.0,
                profile_photo_url TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                email_verified INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                units TEXT DEFAULT 'yards',
                theme TEXT DEFAULT 'light',
                notifications_enabled INTEGER DEFAULT 1,
                share_stats INTEGER DEFAULT 0,
                auto_sync INTEGER DEFAULT 1,
                preferences_json TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Sessions table (for login persistence)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                device_id TEXT,
                device_type TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_activity TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Friends/connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                friend_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (friend_id) REFERENCES users(id),
                UNIQUE(user_id, friend_id)
            )
        """)

        conn.commit()
        conn.close()

    def register_user(self, email: str, username: str, password: str,
                     full_name: str = None) -> Dict:
        """
        Registers a new user

        Args:
            email: User email
            username: Unique username
            password: Plain text password (will be hashed)
            full_name: Optional full name

        Returns:
            Dict with user_id and session_token or error
        """
        # Validate inputs
        if not self._validate_email(email):
            return {"error": "Invalid email format"}

        if len(username) < 3 or len(username) > 20:
            return {"error": "Username must be 3-20 characters"}

        if len(password) < 8:
            return {"error": "Password must be at least 8 characters"}

        # Check if email/username already exists
        if self._user_exists(email=email):
            return {"error": "Email already registered"}

        if self._user_exists(username=username):
            return {"error": "Username already taken"}

        # Create user
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        user_id = self._generate_id()
        salt = secrets.token_hex(32)
        password_hash = self._hash_password(password, salt)

        try:
            cursor.execute("""
                INSERT INTO users (id, email, username, password_hash, salt,
                                 full_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, email.lower(), username, password_hash, salt,
                full_name, datetime.now().isoformat()
            ))

            # Create default preferences
            cursor.execute("""
                INSERT INTO user_preferences (user_id)
                VALUES (?)
            """, (user_id,))

            conn.commit()

            # Create session
            session = self._create_session(user_id)

            print(f"✅ User registered: {username} ({email})")

            return {
                "success": True,
                "user_id": user_id,
                "username": username,
                "session_token": session['token']
            }

        except sqlite3.Error as e:
            conn.rollback()
            return {"error": f"Database error: {e}"}

        finally:
            conn.close()

    def login(self, email_or_username: str, password: str,
             device_id: str = None) -> Dict:
        """
        Authenticates a user

        Args:
            email_or_username: Email or username
            password: Password
            device_id: Optional device identifier

        Returns:
            Dict with user data and session_token or error
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Find user by email or username
        cursor.execute("""
            SELECT * FROM users
            WHERE (email = ? OR username = ?) AND is_active = 1
        """, (email_or_username.lower(), email_or_username))

        user = cursor.fetchone()

        if not user:
            conn.close()
            return {"error": "Invalid credentials"}

        # Verify password
        password_hash = self._hash_password(password, user['salt'])

        if password_hash != user['password_hash']:
            conn.close()
            return {"error": "Invalid credentials"}

        # Update last login
        cursor.execute("""
            UPDATE users SET last_login = ? WHERE id = ?
        """, (datetime.now().isoformat(), user['id']))
        conn.commit()
        conn.close()

        # Create session
        session = self._create_session(user['id'], device_id)

        print(f"✅ User logged in: {user['username']}")

        return {
            "success": True,
            "user_id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "full_name": user['full_name'],
            "handicap": user['handicap'],
            "session_token": session['token']
        }

    def verify_session(self, session_token: str) -> Optional[Dict]:
        """
        Verifies a session token

        Args:
            session_token: Session token

        Returns:
            User dict if valid, None if invalid/expired
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.*, u.* FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND datetime(s.expires_at) > datetime('now')
        """, (session_token,))

        session = cursor.fetchone()

        if not session:
            conn.close()
            return None

        # Update last activity
        cursor.execute("""
            UPDATE sessions SET last_activity = ? WHERE token = ?
        """, (datetime.now().isoformat(), session_token))

        conn.commit()
        conn.close()

        return dict(session)

    def logout(self, session_token: str):
        """Logs out a user by deleting their session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
        conn.commit()
        conn.close()

        print("✅ User logged out")

    def update_profile(self, user_id: str, updates: Dict) -> bool:
        """
        Updates user profile

        Args:
            user_id: User ID
            updates: Dict of fields to update

        Returns:
            True if successful
        """
        allowed_fields = ['full_name', 'phone', 'handicap', 'profile_photo_url']
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [user_id]

        cursor.execute(f"""
            UPDATE users SET {set_clause} WHERE id = ?
        """, values)

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        if success:
            print(f"✅ Profile updated for user {user_id}")

        return success

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Gets user profile"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.*, p.* FROM users u
            LEFT JOIN user_preferences p ON u.id = p.user_id
            WHERE u.id = ?
        """, (user_id,))

        user = cursor.fetchone()
        conn.close()

        return dict(user) if user else None

    def add_friend(self, user_id: str, friend_username: str) -> Dict:
        """
        Sends a friend request

        Args:
            user_id: Current user ID
            friend_username: Username to add

        Returns:
            Result dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find friend
        cursor.execute("SELECT id FROM users WHERE username = ?", (friend_username,))
        friend = cursor.fetchone()

        if not friend:
            conn.close()
            return {"error": "User not found"}

        friend_id = friend[0]

        if user_id == friend_id:
            conn.close()
            return {"error": "Cannot add yourself"}

        # Check if already friends
        cursor.execute("""
            SELECT status FROM friendships
            WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)
        """, (user_id, friend_id, friend_id, user_id))

        existing = cursor.fetchone()

        if existing:
            conn.close()
            return {"error": f"Already {existing[0]}"}

        # Create friend request
        try:
            cursor.execute("""
                INSERT INTO friendships (user_id, friend_id, status, created_at)
                VALUES (?, ?, 'pending', ?)
            """, (user_id, friend_id, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            print(f"✅ Friend request sent to {friend_username}")

            return {"success": True, "message": "Friend request sent"}

        except sqlite3.Error as e:
            conn.rollback()
            conn.close()
            return {"error": str(e)}

    def get_friends(self, user_id: str, status: str = 'accepted') -> List[Dict]:
        """Gets user's friends list"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.id, u.username, u.full_name, u.handicap, u.profile_photo_url
            FROM friendships f
            JOIN users u ON (f.friend_id = u.id OR f.user_id = u.id)
            WHERE (f.user_id = ? OR f.friend_id = ?) AND f.status = ? AND u.id != ?
        """, (user_id, user_id, status, user_id))

        friends = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return friends

    def _validate_email(self, email: str) -> bool:
        """Validates email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _user_exists(self, email: str = None, username: str = None) -> bool:
        """Checks if user exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
        elif username:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        else:
            conn.close()
            return False

        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def _hash_password(self, password: str, salt: str) -> str:
        """Hashes password with salt"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()

    def _generate_id(self) -> str:
        """Generates unique user ID"""
        return f"user_{secrets.token_hex(16)}"

    def _create_session(self, user_id: str, device_id: str = None) -> Dict:
        """Creates a new session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        session_id = f"session_{secrets.token_hex(16)}"
        token = secrets.token_urlsafe(32)
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=30)  # 30-day sessions

        cursor.execute("""
            INSERT INTO sessions (id, user_id, token, device_id, created_at, expires_at, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, user_id, token, device_id,
            created_at.isoformat(), expires_at.isoformat(), created_at.isoformat()
        ))

        conn.commit()
        conn.close()

        return {
            'session_id': session_id,
            'token': token,
            'expires_at': expires_at.isoformat()
        }


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("USER ACCOUNTS & AUTHENTICATION")
    print("="*60)

    manager = UserAccountManager()

    # Test registration
    print("\n--- Registering User ---")
    result = manager.register_user(
        email="john.doe@example.com",
        username="johndoe",
        password="SecurePassword123",
        full_name="John Doe"
    )

    if "success" in result:
        print(f"✅ Registration successful!")
        print(f"   User ID: {result['user_id']}")
        print(f"   Session Token: {result['session_token'][:20]}...")

        session_token = result['session_token']
        user_id = result['user_id']

        # Test login
        print("\n--- Testing Login ---")
        login_result = manager.login("johndoe", "SecurePassword123")
        if "success" in login_result:
            print(f"✅ Login successful!")
            print(f"   Username: {login_result['username']}")

        # Update profile
        print("\n--- Updating Profile ---")
        manager.update_profile(user_id, {
            'full_name': 'John D. Doe',
            'handicap': 15.2
        })

        # Get profile
        print("\n--- Getting Profile ---")
        profile = manager.get_user_profile(user_id)
        print(f"Name: {profile['full_name']}")
        print(f"Handicap: {profile['handicap']}")
        print(f"Email: {profile['email']}")

        # Register second user
        print("\n--- Registering Second User ---")
        result2 = manager.register_user(
            email="jane.smith@example.com",
            username="janesmith",
            password="AnotherPassword456",
            full_name="Jane Smith"
        )

        if "success" in result2:
            # Add friend
            print("\n--- Adding Friend ---")
            friend_result = manager.add_friend(user_id, "janesmith")
            print(friend_result.get('message', friend_result))

            # Accept friend request (would be done by jane)
            conn = manager._UserAccountManager__conn = sqlite3.connect(manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE friendships SET status = 'accepted'
                WHERE user_id = ? AND friend_id = ?
            """, (user_id, result2['user_id']))
            conn.commit()
            conn.close()

            # Get friends
            print("\n--- Getting Friends List ---")
            friends = manager.get_friends(user_id)
            print(f"Friends: {[f['username'] for f in friends]}")

        # Verify session
        print("\n--- Verifying Session ---")
        session_check = manager.verify_session(session_token)
        if session_check:
            print(f"✅ Session valid for: {session_check['username']}")

        # Logout
        print("\n--- Logging Out ---")
        manager.logout(session_token)

        # Try to verify again
        if not manager.verify_session(session_token):
            print("✅ Session invalidated after logout")

    else:
        print(f"❌ Registration failed: {result['error']}")

    print("\n" + "="*60)
    print("Mobile Implementation:")
    print("  - iOS: Use Firebase Auth + Keychain for tokens")
    print("  - Android: Firebase Auth + EncryptedSharedPreferences")
    print("  - React Native: Firebase Auth + AsyncStorage")
    print("="*60)
