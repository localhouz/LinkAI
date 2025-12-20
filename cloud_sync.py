"""
Cloud Sync Service
Syncs user data across devices using cloud storage

For production:
- iOS: CloudKit or Firebase
- Android: Firebase or AWS Amplify
- React Native: Firebase Realtime Database
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import time


class CloudSyncService:
    """
    Manages cloud synchronization of user data

    This is a local simulation. In production:
    - Replace with Firebase, AWS, or custom API
    - Use real-time database for instant sync
    - Add conflict resolution
    """

    def __init__(self, db_path: str = "golf_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Creates sync-related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sync metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                last_synced TEXT,
                checksum TEXT,
                device_id TEXT,
                UNIQUE(user_id, data_type, record_id)
            )
        """)

        # Cloud backup table (simulates cloud storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cloud_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                data_json TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                updated_at TEXT NOT NULL,
                checksum TEXT NOT NULL,
                UNIQUE(user_id, data_type, record_id)
            )
        """)

        # Sync conflicts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                record_id TEXT NOT NULL,
                local_data TEXT,
                cloud_data TEXT,
                detected_at TEXT NOT NULL,
                resolved INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def sync_user_data(self, user_id: str, device_id: str = None) -> Dict:
        """
        Syncs all user data with cloud

        Args:
            user_id: User ID
            device_id: Device identifier

        Returns:
            Sync result with statistics
        """
        print(f"\n🔄 Starting sync for user: {user_id}")

        result = {
            'uploaded': 0,
            'downloaded': 0,
            'conflicts': 0,
            'errors': []
        }

        # Sync different data types
        data_types = ['shots', 'rounds', 'courses', 'preferences']

        for data_type in data_types:
            try:
                # Upload local changes
                uploaded = self._upload_changes(user_id, data_type, device_id)
                result['uploaded'] += uploaded

                # Download remote changes
                downloaded = self._download_changes(user_id, data_type)
                result['downloaded'] += downloaded

            except Exception as e:
                result['errors'].append(f"{data_type}: {str(e)}")

        # Check for conflicts
        result['conflicts'] = self._detect_conflicts(user_id)

        print(f"✅ Sync complete: ↑{result['uploaded']} ↓{result['downloaded']} ⚠️{result['conflicts']}")

        return result

    def _upload_changes(self, user_id: str, data_type: str, device_id: str) -> int:
        """Uploads local changes to cloud"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get local records that need syncing
        if data_type == 'shots':
            cursor.execute("""
                SELECT s.*, sm.last_synced
                FROM shots s
                LEFT JOIN sync_metadata sm ON (
                    sm.user_id = s.player_id AND
                    sm.data_type = 'shots' AND
                    sm.record_id = CAST(s.id AS TEXT)
                )
                WHERE s.player_id = ? AND (
                    sm.last_synced IS NULL OR
                    s.timestamp > sm.last_synced
                )
            """, (user_id,))

        elif data_type == 'preferences':
            cursor.execute("""
                SELECT * FROM user_preferences WHERE user_id = ?
            """, (user_id,))

        else:
            conn.close()
            return 0

        records = cursor.fetchall()

        uploaded_count = 0

        for record in records:
            record_dict = dict(record)
            record_id = str(record_dict.get('id', user_id))

            # Calculate checksum
            data_json = json.dumps(record_dict, sort_keys=True)
            checksum = hashlib.md5(data_json.encode()).hexdigest()

            # Upload to cloud (in production: Firebase/AWS API call)
            cursor.execute("""
                INSERT OR REPLACE INTO cloud_backup
                (user_id, data_type, record_id, data_json, updated_at, checksum, version)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE(
                    (SELECT version + 1 FROM cloud_backup
                     WHERE user_id = ? AND data_type = ? AND record_id = ?),
                    1
                ))
            """, (
                user_id, data_type, record_id, data_json,
                datetime.now().isoformat(), checksum,
                user_id, data_type, record_id
            ))

            # Update sync metadata
            cursor.execute("""
                INSERT OR REPLACE INTO sync_metadata
                (user_id, data_type, record_id, last_synced, checksum, device_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, data_type, record_id,
                datetime.now().isoformat(), checksum, device_id
            ))

            uploaded_count += 1

        conn.commit()
        conn.close()

        if uploaded_count > 0:
            print(f"  ↑ Uploaded {uploaded_count} {data_type} records")

        return uploaded_count

    def _download_changes(self, user_id: str, data_type: str) -> int:
        """Downloads remote changes from cloud"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get cloud records that are newer than local
        cursor.execute("""
            SELECT cb.*
            FROM cloud_backup cb
            LEFT JOIN sync_metadata sm ON (
                sm.user_id = cb.user_id AND
                sm.data_type = cb.data_type AND
                sm.record_id = cb.record_id
            )
            WHERE cb.user_id = ? AND cb.data_type = ? AND (
                sm.last_synced IS NULL OR
                cb.updated_at > sm.last_synced
            )
        """, (user_id, data_type))

        records = cursor.fetchall()

        downloaded_count = 0

        for record in records:
            data = json.loads(record['data_json'])

            # Apply to local database
            if data_type == 'shots':
                # Update or insert shot
                self._apply_shot_update(cursor, data)

            elif data_type == 'preferences':
                # Update preferences
                self._apply_preferences_update(cursor, data)

            # Update sync metadata
            cursor.execute("""
                INSERT OR REPLACE INTO sync_metadata
                (user_id, data_type, record_id, last_synced, checksum)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, data_type, record['record_id'],
                record['updated_at'], record['checksum']
            ))

            downloaded_count += 1

        conn.commit()
        conn.close()

        if downloaded_count > 0:
            print(f"  ↓ Downloaded {downloaded_count} {data_type} records")

        return downloaded_count

    def _apply_shot_update(self, cursor, shot_data):
        """Applies a shot update to local database"""
        # Check if shot exists
        cursor.execute("SELECT id FROM shots WHERE id = ?", (shot_data.get('id'),))

        if cursor.fetchone():
            # Update existing
            cursor.execute("""
                UPDATE shots SET
                    club = ?, distance_yards = ?, predicted_lat = ?,
                    predicted_lon = ?, actual_lat = ?, actual_lon = ?
                WHERE id = ?
            """, (
                shot_data.get('club'), shot_data.get('distance_yards'),
                shot_data.get('predicted_lat'), shot_data.get('predicted_lon'),
                shot_data.get('actual_lat'), shot_data.get('actual_lon'),
                shot_data.get('id')
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO shots (
                    id, timestamp, player_id, club, distance_yards,
                    predicted_lat, predicted_lon, actual_lat, actual_lon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                shot_data.get('id'), shot_data.get('timestamp'),
                shot_data.get('player_id'), shot_data.get('club'),
                shot_data.get('distance_yards'), shot_data.get('predicted_lat'),
                shot_data.get('predicted_lon'), shot_data.get('actual_lat'),
                shot_data.get('actual_lon')
            ))

    def _apply_preferences_update(self, cursor, pref_data):
        """Applies preferences update to local database"""
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences
            (user_id, units, theme, notifications_enabled, auto_sync)
            VALUES (?, ?, ?, ?, ?)
        """, (
            pref_data.get('user_id'), pref_data.get('units'),
            pref_data.get('theme'), pref_data.get('notifications_enabled'),
            pref_data.get('auto_sync')
        ))

    def _detect_conflicts(self, user_id: str) -> int:
        """Detects sync conflicts"""
        # Simplified conflict detection
        # In production: Use vector clocks or CRDTs
        return 0

    def get_sync_status(self, user_id: str) -> Dict:
        """Gets current sync status for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Count pending uploads
        cursor.execute("""
            SELECT COUNT(*) FROM shots s
            LEFT JOIN sync_metadata sm ON (
                sm.user_id = s.player_id AND
                sm.data_type = 'shots' AND
                sm.record_id = CAST(s.id AS TEXT)
            )
            WHERE s.player_id = ? AND sm.last_synced IS NULL
        """, (user_id,))

        pending_uploads = cursor.fetchone()[0]

        # Last sync time
        cursor.execute("""
            SELECT MAX(last_synced) FROM sync_metadata WHERE user_id = ?
        """, (user_id,))

        last_sync = cursor.fetchone()[0]

        conn.close()

        return {
            'pending_uploads': pending_uploads,
            'last_sync': last_sync,
            'is_synced': pending_uploads == 0
        }


# Example usage
if __name__ == "__main__":
    from user_accounts import UserAccountManager
    from shot_tracker import ShotTracker

    print("="*60)
    print("CLOUD SYNC SERVICE")
    print("="*60)

    # Setup
    account_manager = UserAccountManager()
    shot_tracker = ShotTracker()
    sync_service = CloudSyncService()

    # Register user
    print("\n--- Setting Up User ---")
    result = account_manager.register_user(
        email="sync.test@example.com",
        username="synctest",
        password="TestPassword123"
    )

    if "success" in result:
        user_id = result['user_id']

        # Record some shots
        print("\n--- Recording Shots (Device 1) ---")
        shot_tracker.add_player(user_id, "Sync Test User")

        for i in range(5):
            shot_tracker.record_shot(user_id, "7-Iron", 150 + i * 5)

        print(f"Recorded 5 shots")

        # Sync to cloud
        print("\n--- Syncing to Cloud ---")
        sync_result = sync_service.sync_user_data(user_id, device_id="device_1")

        print(f"Sync result: {sync_result}")

        # Check sync status
        print("\n--- Checking Sync Status ---")
        status = sync_service.get_sync_status(user_id)
        print(f"Pending uploads: {status['pending_uploads']}")
        print(f"Last sync: {status['last_sync']}")
        print(f"Is synced: {status['is_synced']}")

        # Simulate second device
        print("\n--- Simulating Second Device ---")
        print("(On device 2, download would pull those 5 shots)")

        sync_result2 = sync_service.sync_user_data(user_id, device_id="device_2")
        print(f"Device 2 sync: ↓{sync_result2['downloaded']} shots downloaded")

    print("\n" + "="*60)
    print("Production Implementation:")
    print("  - Firebase Realtime Database for instant sync")
    print("  - AWS AppSync for GraphQL-based sync")
    print("  - CloudKit for iOS-only apps")
    print("  - Custom REST API + WebSockets")
    print("="*60)
