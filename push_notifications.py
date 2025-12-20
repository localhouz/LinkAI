"""
Push Notification System
Sends notifications to users for various events

For production:
- iOS: Apple Push Notification Service (APNS)
- Android: Firebase Cloud Messaging (FCM)
- React Native: react-native-push-notification + FCM
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class NotificationType(Enum):
    """Types of notifications"""
    GROUP_READY = "group_ready"  # "Your group is on the tee"
    BALL_FOUND = "ball_found"  # "Ball found by partner"
    WEATHER_ALERT = "weather_alert"  # Weather warnings
    FRIEND_REQUEST = "friend_request"  # New friend request
    SHOT_REMINDER = "shot_reminder"  # Reminder to log shot
    COURSE_UPDATE = "course_update"  # Course conditions updated
    ACHIEVEMENT = "achievement"  # Stats milestone
    TEE_TIME_REMINDER = "tee_time_reminder"  # Upcoming tee time


class PushNotificationService:
    """
    Manages push notifications

    This is a local simulation. In production:
    - iOS: Use APNS via HTTP/2 API
    - Android: Use FCM REST API
    - Both: Firebase Admin SDK handles both platforms
    """

    def __init__(self, db_path: str = "golf_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Creates notification tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Device tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                token TEXT NOT NULL,
                registered_at TEXT NOT NULL,
                last_used TEXT,
                is_active INTEGER DEFAULT 1,
                UNIQUE(user_id, device_id)
            )
        """)

        # Notification preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id TEXT PRIMARY KEY,
                group_ready INTEGER DEFAULT 1,
                ball_found INTEGER DEFAULT 1,
                weather_alert INTEGER DEFAULT 1,
                friend_request INTEGER DEFAULT 1,
                shot_reminder INTEGER DEFAULT 0,
                course_update INTEGER DEFAULT 1,
                achievement INTEGER DEFAULT 1,
                tee_time_reminder INTEGER DEFAULT 1,
                quiet_hours_start TEXT,
                quiet_hours_end TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Notification history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                data_json TEXT,
                sent_at TEXT NOT NULL,
                delivered INTEGER DEFAULT 0,
                opened INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    def register_device(self, user_id: str, device_id: str,
                       platform: str, token: str) -> bool:
        """
        Registers a device for push notifications

        Args:
            user_id: User ID
            device_id: Unique device identifier
            platform: 'ios' or 'android'
            token: APNS or FCM device token

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO device_tokens
                (user_id, device_id, platform, token, registered_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (user_id, device_id, platform, token, datetime.now().isoformat()))

            conn.commit()
            print(f"✅ Device registered for push: {platform} - {device_id[:20]}...")
            return True

        except sqlite3.Error as e:
            print(f"❌ Error registering device: {e}")
            return False

        finally:
            conn.close()

    def send_notification(self, user_id: str, notification_type: NotificationType,
                         title: str, body: str, data: Dict = None) -> Dict:
        """
        Sends a push notification to user

        Args:
            user_id: User ID to notify
            notification_type: Type of notification
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            Result dict
        """
        # Check if user has this notification type enabled
        if not self._is_notification_enabled(user_id, notification_type):
            return {"skipped": True, "reason": "User has disabled this notification type"}

        # Check quiet hours
        if self._is_quiet_hours(user_id):
            return {"skipped": True, "reason": "Quiet hours active"}

        # Get device tokens
        tokens = self._get_device_tokens(user_id)

        if not tokens:
            return {"error": "No registered devices"}

        # In production: Call APNS/FCM APIs
        # For now, simulate sending
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Log notification
        cursor.execute("""
            INSERT INTO notification_history
            (user_id, notification_type, title, body, data_json, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, notification_type.value, title, body,
            json.dumps(data) if data else None,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        print(f"📲 Notification sent: {title}")
        print(f"   To: {len(tokens)} device(s)")
        print(f"   Type: {notification_type.value}")

        return {
            "success": True,
            "devices_sent": len(tokens),
            "notification_id": cursor.lastrowid
        }

    def send_group_notification(self, group_session_id: str,
                               message: str, sender_id: str = None) -> int:
        """
        Sends notification to all players in a group

        Args:
            group_session_id: Group session ID
            message: Notification message
            sender_id: Optional sender to exclude

        Returns:
            Number of notifications sent
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all players in group
        cursor.execute("""
            SELECT DISTINCT player_id FROM session_players
            WHERE session_id = ? AND player_id != ?
        """, (group_session_id, sender_id or ""))

        players = cursor.fetchall()
        conn.close()

        sent_count = 0

        for (player_id,) in players:
            result = self.send_notification(
                user_id=player_id,
                notification_type=NotificationType.GROUP_READY,
                title="Group Update",
                body=message,
                data={'session_id': group_session_id}
            )

            if result.get('success'):
                sent_count += 1

        return sent_count

    def notify_ball_found(self, finder_id: str, ball_owner_id: str,
                         location: Dict) -> bool:
        """
        Notifies player that their ball was found

        Args:
            finder_id: Who found the ball
            ball_owner_id: Owner of the ball
            location: Ball location dict

        Returns:
            True if sent
        """
        # Get finder's name
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (finder_id,))
        finder = cursor.fetchone()
        conn.close()

        finder_name = finder[0] if finder else "Your playing partner"

        result = self.send_notification(
            user_id=ball_owner_id,
            notification_type=NotificationType.BALL_FOUND,
            title="Ball Found! ⛳",
            body=f"{finder_name} found your ball",
            data={
                'finder_id': finder_id,
                'location': location
            }
        )

        return result.get('success', False)

    def notify_weather_alert(self, user_ids: List[str], alert_type: str,
                            message: str) -> int:
        """
        Sends weather alerts to users

        Args:
            user_ids: List of user IDs
            alert_type: 'rain', 'lightning', 'wind', etc.
            message: Alert message

        Returns:
            Number of notifications sent
        """
        sent_count = 0

        for user_id in user_ids:
            result = self.send_notification(
                user_id=user_id,
                notification_type=NotificationType.WEATHER_ALERT,
                title=f"⚠️ Weather Alert: {alert_type.title()}",
                body=message,
                data={'alert_type': alert_type}
            )

            if result.get('success'):
                sent_count += 1

        return sent_count

    def set_notification_preferences(self, user_id: str, preferences: Dict) -> bool:
        """
        Updates notification preferences

        Args:
            user_id: User ID
            preferences: Dict of notification type -> enabled

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create or update preferences
        fields = []
        values = []

        for key, value in preferences.items():
            if key in ['group_ready', 'ball_found', 'weather_alert',
                      'friend_request', 'shot_reminder', 'course_update',
                      'achievement', 'tee_time_reminder']:
                fields.append(f"{key} = ?")
                values.append(1 if value else 0)

        if not fields:
            conn.close()
            return False

        values.append(user_id)

        cursor.execute(f"""
            INSERT OR REPLACE INTO notification_preferences
            (user_id, {', '.join(k for k, _ in preferences.items() if k in fields)})
            VALUES (?, {', '.join(['?' for _ in fields])})
        """, values)

        conn.commit()
        conn.close()

        print(f"✅ Notification preferences updated for {user_id}")
        return True

    def _is_notification_enabled(self, user_id: str, notification_type: NotificationType) -> bool:
        """Checks if user has enabled this notification type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT {notification_type.value} FROM notification_preferences
            WHERE user_id = ?
        """, (user_id,))

        result = cursor.fetchone()
        conn.close()

        # If no preferences set, default to enabled
        return result[0] == 1 if result else True

    def _is_quiet_hours(self, user_id: str) -> bool:
        """Checks if currently in quiet hours for user"""
        # Simplified - in production, use user's timezone
        return False

    def _get_device_tokens(self, user_id: str) -> List[Dict]:
        """Gets active device tokens for user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT device_id, platform, token FROM device_tokens
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))

        tokens = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return tokens

    def get_notification_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Gets user's notification history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM notification_history
            WHERE user_id = ?
            ORDER BY sent_at DESC
            LIMIT ?
        """, (user_id, limit))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history


# Example usage
if __name__ == "__main__":
    from user_accounts import UserAccountManager

    print("="*60)
    print("PUSH NOTIFICATION SYSTEM")
    print("="*60)

    # Setup
    account_manager = UserAccountManager()
    notification_service = PushNotificationService()

    # Register users
    print("\n--- Registering Users ---")
    user1 = account_manager.register_user(
        email="player1@example.com",
        username="player1",
        password="Password123"
    )

    user2 = account_manager.register_user(
        email="player2@example.com",
        username="player2",
        password="Password123"
    )

    if user1.get('success') and user2.get('success'):
        user1_id = user1['user_id']
        user2_id = user2['user_id']

        # Register devices
        print("\n--- Registering Devices ---")
        notification_service.register_device(
            user1_id,
            "device_123",
            "ios",
            "apns_token_abc123..."
        )

        notification_service.register_device(
            user2_id,
            "device_456",
            "android",
            "fcm_token_xyz789..."
        )

        # Send various notifications
        print("\n--- Sending Notifications ---")

        # Ball found notification
        notification_service.notify_ball_found(
            finder_id=user2_id,
            ball_owner_id=user1_id,
            location={'lat': 36.1234, 'lon': -95.9876}
        )

        # Weather alert
        notification_service.notify_weather_alert(
            user_ids=[user1_id, user2_id],
            alert_type="lightning",
            message="Lightning detected nearby. Seek shelter immediately."
        )

        # Custom notification
        notification_service.send_notification(
            user_id=user1_id,
            notification_type=NotificationType.ACHIEVEMENT,
            title="New Achievement! 🏆",
            body="You've played 10 rounds this month",
            data={'achievement_id': 'rounds_10'}
        )

        # Update preferences
        print("\n--- Updating Preferences ---")
        notification_service.set_notification_preferences(user1_id, {
            'shot_reminder': False,
            'weather_alert': True,
            'ball_found': True
        })

        # Get notification history
        print("\n--- Notification History ---")
        history = notification_service.get_notification_history(user1_id)
        print(f"User has {len(history)} notifications")
        for notif in history[:3]:
            print(f"  - {notif['title']}: {notif['body']}")

    print("\n" + "="*60)
    print("Production Implementation:")
    print("  - iOS: APNS via Firebase Admin SDK or HTTP/2 API")
    print("  - Android: FCM REST API")
    print("  - Server: Node.js/Python backend to send")
    print("  - Real-time: Use Firebase Cloud Functions for triggers")
    print("="*60)
