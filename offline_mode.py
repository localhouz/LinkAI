"""
Offline Mode Module
Caches course data, maps, and allows offline operation
"""

import json
import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import pickle


class OfflineManager:
    """Manages offline data caching and synchronization"""

    def __init__(self, cache_dir: str = "offline_cache"):
        self.cache_dir = cache_dir
        self.db_path = os.path.join(cache_dir, "offline_data.db")

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Creates database for offline cache management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Cached courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_courses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data TEXT NOT NULL,
                cached_at TEXT NOT NULL,
                expires_at TEXT,
                size_bytes INTEGER,
                version INTEGER DEFAULT 1
            )
        """)

        # Cached map tiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_tiles (
                id TEXT PRIMARY KEY,
                tile_url TEXT NOT NULL,
                tile_data BLOB NOT NULL,
                cached_at TEXT NOT NULL,
                expires_at TEXT
            )
        """)

        # Sync queue table (for pending uploads when back online)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,
                action TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                synced INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def cache_course(self, course_id: str, course_name: str, course_data: Dict,
                    expires_days: int = 30):
        """
        Caches course data for offline use

        Args:
            course_id: Unique course identifier
            course_name: Course name
            course_data: Course data dictionary
            expires_days: Days until cache expires
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Serialize course data
        data_json = json.dumps(course_data)
        size = len(data_json.encode('utf-8'))

        # Calculate expiration
        from datetime import timedelta
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO cached_courses
            (id, name, data, cached_at, expires_at, size_bytes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            course_id, course_name, data_json,
            datetime.now().isoformat(), expires_at, size
        ))

        conn.commit()
        conn.close()

        print(f"✅ Cached course: {course_name} ({size/1024:.1f} KB)")

    def get_cached_course(self, course_id: str) -> Optional[Dict]:
        """
        Retrieves cached course data

        Args:
            course_id: Course identifier

        Returns:
            Course data dict or None if not cached/expired
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cached_courses WHERE id = ?
        """, (course_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Check if expired
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            print(f"⚠️  Cache expired for: {row['name']}")
            return None

        return json.loads(row['data'])

    def list_cached_courses(self) -> List[Dict]:
        """
        Lists all cached courses

        Returns:
            List of course info dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, cached_at, expires_at, size_bytes
            FROM cached_courses
            ORDER BY cached_at DESC
        """)

        courses = []
        for row in cursor.fetchall():
            expires_at = datetime.fromisoformat(row['expires_at'])
            is_expired = datetime.now() > expires_at

            courses.append({
                'id': row['id'],
                'name': row['name'],
                'cached_at': row['cached_at'],
                'expires_at': row['expires_at'],
                'size_kb': row['size_bytes'] / 1024,
                'expired': is_expired
            })

        conn.close()
        return courses

    def delete_cached_course(self, course_id: str):
        """Deletes a cached course"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cached_courses WHERE id = ?", (course_id,))
        conn.commit()
        conn.close()

        print(f"🗑️  Deleted cached course: {course_id}")

    def clear_expired_cache(self):
        """Removes all expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete expired courses
        cursor.execute("""
            DELETE FROM cached_courses
            WHERE datetime(expires_at) < datetime('now')
        """)

        deleted_courses = cursor.rowcount

        # Delete expired tiles
        cursor.execute("""
            DELETE FROM cached_tiles
            WHERE datetime(expires_at) < datetime('now')
        """)

        deleted_tiles = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"🗑️  Cleared {deleted_courses} expired courses, {deleted_tiles} expired tiles")

    def add_to_sync_queue(self, data_type: str, action: str, data: Dict):
        """
        Adds data to sync queue for when internet connection is restored

        Args:
            data_type: Type of data (shot, round, etc.)
            action: Action to perform (create, update, delete)
            data: Data to sync
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sync_queue (data_type, action, data, created_at, synced)
            VALUES (?, ?, ?, ?, 0)
        """, (
            data_type, action, json.dumps(data), datetime.now().isoformat()
        ))

        queue_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"📤 Added to sync queue: {data_type} {action} (ID: {queue_id})")
        return queue_id

    def get_sync_queue(self) -> List[Dict]:
        """
        Gets all pending sync items

        Returns:
            List of sync queue items
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM sync_queue WHERE synced = 0
            ORDER BY created_at ASC
        """)

        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row['id'],
                'data_type': row['data_type'],
                'action': row['action'],
                'data': json.loads(row['data']),
                'created_at': row['created_at']
            })

        conn.close()
        return items

    def mark_synced(self, queue_id: int):
        """Marks a sync queue item as synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sync_queue SET synced = 1 WHERE id = ?
        """, (queue_id,))

        conn.commit()
        conn.close()

    def process_sync_queue(self, upload_function):
        """
        Processes sync queue (uploads pending data when online)

        Args:
            upload_function: Function to call for each item
                            Signature: upload_function(data_type, action, data) -> bool
        """
        queue = self.get_sync_queue()

        if not queue:
            print("✅ Sync queue is empty")
            return

        print(f"📤 Processing {len(queue)} items in sync queue...")

        for item in queue:
            try:
                success = upload_function(
                    item['data_type'],
                    item['action'],
                    item['data']
                )

                if success:
                    self.mark_synced(item['id'])
                    print(f"  ✅ Synced: {item['data_type']} {item['action']}")
                else:
                    print(f"  ❌ Failed: {item['data_type']} {item['action']}")

            except Exception as e:
                print(f"  ❌ Error syncing item {item['id']}: {e}")

        remaining = len(self.get_sync_queue())
        print(f"\n📊 Sync complete. {remaining} items remaining.")

    def get_cache_stats(self) -> Dict:
        """
        Gets statistics about offline cache

        Returns:
            Dict with cache statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Course stats
        cursor.execute("SELECT COUNT(*), SUM(size_bytes) FROM cached_courses")
        courses_count, courses_size = cursor.fetchone()

        # Tile stats
        cursor.execute("SELECT COUNT(*), SUM(LENGTH(tile_data)) FROM cached_tiles")
        tiles_count, tiles_size = cursor.fetchone()

        # Sync queue stats
        cursor.execute("SELECT COUNT(*) FROM sync_queue WHERE synced = 0")
        pending_sync = cursor.fetchone()[0]

        conn.close()

        return {
            'courses_cached': courses_count or 0,
            'courses_size_mb': (courses_size or 0) / (1024 * 1024),
            'tiles_cached': tiles_count or 0,
            'tiles_size_mb': (tiles_size or 0) / (1024 * 1024),
            'total_size_mb': ((courses_size or 0) + (tiles_size or 0)) / (1024 * 1024),
            'pending_sync': pending_sync
        }

    def is_online(self) -> bool:
        """
        Checks if device has internet connection

        Returns:
            bool: True if online
        """
        import socket
        try:
            # Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("OFFLINE MODE - Course Caching & Sync")
    print("="*60)

    manager = OfflineManager()

    # Check online status
    print("\n📡 Checking connection...")
    if manager.is_online():
        print("✅ Device is ONLINE")
    else:
        print("⚠️  Device is OFFLINE")

    # Cache a sample course
    print("\n" + "="*60)
    print("Caching Sample Course")
    print("="*60)

    sample_course = {
        'name': 'Pine Valley Golf Club',
        'holes': [
            {
                'number': 1,
                'par': 4,
                'tee': (36.1234, -95.9876),
                'green': (36.1245, -95.9895)
            },
            {
                'number': 2,
                'par': 3,
                'tee': (36.1246, -95.9896),
                'green': (36.1250, -95.9900)
            }
        ],
        'center': (36.1240, -95.9890)
    }

    manager.cache_course("pine_valley", "Pine Valley Golf Club", sample_course)

    # List cached courses
    print("\n" + "="*60)
    print("Cached Courses")
    print("="*60)
    cached = manager.list_cached_courses()
    for course in cached:
        status = "❌ Expired" if course['expired'] else "✅ Valid"
        print(f"{course['name']:30s} {status}  Size: {course['size_kb']:.1f} KB")

    # Retrieve cached course
    print("\n" + "="*60)
    print("Retrieving Cached Course")
    print("="*60)
    retrieved = manager.get_cached_course("pine_valley")
    if retrieved:
        print(f"✅ Retrieved: {retrieved['name']}")
        print(f"   Holes: {len(retrieved['holes'])}")
    else:
        print("❌ Course not found or expired")

    # Add to sync queue (simulate offline shot recording)
    print("\n" + "="*60)
    print("Simulating Offline Shot Recording")
    print("="*60)

    shot_data = {
        'player_id': 'player1',
        'club': 'Driver',
        'distance': 250,
        'hole': 1,
        'timestamp': datetime.now().isoformat()
    }

    manager.add_to_sync_queue('shot', 'create', shot_data)

    # View sync queue
    print("\n" + "="*60)
    print("Pending Sync Queue")
    print("="*60)
    queue = manager.get_sync_queue()
    print(f"Items pending sync: {len(queue)}")
    for item in queue:
        print(f"  - {item['data_type']} {item['action']} (created: {item['created_at']})")

    # Cache statistics
    print("\n" + "="*60)
    print("Cache Statistics")
    print("="*60)
    stats = manager.get_cache_stats()
    print(f"Courses cached:     {stats['courses_cached']}")
    print(f"Courses size:       {stats['courses_size_mb']:.2f} MB")
    print(f"Map tiles cached:   {stats['tiles_cached']}")
    print(f"Tiles size:         {stats['tiles_size_mb']:.2f} MB")
    print(f"Total cache size:   {stats['total_size_mb']:.2f} MB")
    print(f"Pending sync items: {stats['pending_sync']}")

    # Clear expired cache
    print("\n" + "="*60)
    print("Cache Maintenance")
    print("="*60)
    manager.clear_expired_cache()

    print("\n" + "="*60)
    print("Offline mode ready!")
    print("Users can now play without internet connection.")
    print("Data will sync automatically when back online.")
    print("="*60)
