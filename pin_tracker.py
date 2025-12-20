"""
Pin Position Tracker
Stores and manages daily pin positions for golf courses

Crowdsources pin data:
- First player detects pin → uploads to database
- Other players that day → use the detected position
- Builds historical database of pin positions
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from pin_detector import PinDetector, PinPositionCalculator


class PinPositionTracker:
    """
    Manages pin positions across courses and time

    Features:
    - Store daily pin positions
    - Share positions between players
    - Historical pin position data
    - Pin position heatmaps per hole
    """

    def __init__(self, db_path: str = "golf_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Creates pin position tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Daily pin positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pin_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                hole_number INTEGER NOT NULL,
                date TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                detected_by TEXT,
                detection_method TEXT DEFAULT 'cv',
                confidence REAL,
                flag_color TEXT,
                verified_count INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                UNIQUE(course_name, hole_number, date)
            )
        """)

        # Historical pin positions (all detections, not just daily)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pin_position_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                hole_number INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                detected_by TEXT,
                confidence REAL,
                timestamp TEXT NOT NULL
            )
        """)

        # Pin position zones (heatmap data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pin_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                hole_number INTEGER NOT NULL,
                zone_name TEXT NOT NULL,
                center_lat REAL NOT NULL,
                center_lon REAL NOT NULL,
                usage_count INTEGER DEFAULT 0,
                UNIQUE(course_name, hole_number, zone_name)
            )
        """)

        conn.commit()
        conn.close()

    def record_pin_detection(self, course_name: str, hole_number: int,
                           pin_gps: Tuple[float, float],
                           detected_by: str = None,
                           confidence: float = None,
                           flag_color: str = None) -> Dict:
        """
        Records a pin detection

        Args:
            course_name: Course name
            hole_number: Hole number (1-18)
            pin_gps: (latitude, longitude) of pin
            detected_by: User ID who detected it
            confidence: Detection confidence
            flag_color: Detected flag color

        Returns:
            Result dict
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = date.today().isoformat()
        now = datetime.now().isoformat()

        try:
            # Check if pin already recorded today
            cursor.execute("""
                SELECT id, verified_count FROM pin_positions
                WHERE course_name = ? AND hole_number = ? AND date = ?
            """, (course_name, hole_number, today))

            existing = cursor.fetchone()

            if existing:
                # Update verified count (multiple people confirmed same position)
                cursor.execute("""
                    UPDATE pin_positions SET verified_count = verified_count + 1
                    WHERE id = ?
                """, (existing[0],))

                result = {
                    'status': 'updated',
                    'message': f'Pin position verified (now {existing[1] + 1} confirmations)'
                }

            else:
                # New pin position for today
                cursor.execute("""
                    INSERT INTO pin_positions
                    (course_name, hole_number, date, latitude, longitude,
                     detected_by, confidence, flag_color, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course_name, hole_number, today,
                    pin_gps[0], pin_gps[1],
                    detected_by, confidence, flag_color, now
                ))

                result = {
                    'status': 'created',
                    'message': 'New pin position recorded for today'
                }

            # Always add to history
            cursor.execute("""
                INSERT INTO pin_position_history
                (course_name, hole_number, latitude, longitude, detected_by, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (course_name, hole_number, pin_gps[0], pin_gps[1], detected_by, confidence, now))

            # Update pin zone heatmap
            self._update_pin_zone(cursor, course_name, hole_number, pin_gps)

            conn.commit()

            print(f"✅ Pin recorded: {course_name} Hole {hole_number} - {result['message']}")

            return result

        except sqlite3.Error as e:
            conn.rollback()
            return {'error': str(e)}

        finally:
            conn.close()

    def get_todays_pin(self, course_name: str, hole_number: int) -> Optional[Dict]:
        """
        Gets today's pin position for a hole

        Args:
            course_name: Course name
            hole_number: Hole number

        Returns:
            Pin position dict or None if not detected today
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT * FROM pin_positions
            WHERE course_name = ? AND hole_number = ? AND date = ?
        """, (course_name, hole_number, today))

        pin = cursor.fetchone()
        conn.close()

        if pin:
            return {
                'latitude': pin['latitude'],
                'longitude': pin['longitude'],
                'confidence': pin['confidence'],
                'verified_count': pin['verified_count'],
                'flag_color': pin['flag_color'],
                'detected_by': pin['detected_by']
            }

        return None

    def get_pin_history(self, course_name: str, hole_number: int,
                       days: int = 30) -> List[Dict]:
        """
        Gets pin position history for a hole

        Args:
            course_name: Course name
            hole_number: Hole number
            days: Number of days of history

        Returns:
            List of pin positions
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM pin_positions
            WHERE course_name = ? AND hole_number = ?
            ORDER BY date DESC
            LIMIT ?
        """, (course_name, hole_number, days))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history

    def get_pin_heatmap(self, course_name: str, hole_number: int) -> Dict:
        """
        Gets pin position heatmap for a hole

        Shows common pin positions based on historical data

        Returns:
            Dict with zones and their usage counts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM pin_zones
            WHERE course_name = ? AND hole_number = ?
            ORDER BY usage_count DESC
        """, (course_name, hole_number))

        zones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        if not zones:
            return {
                'message': 'No historical data yet',
                'zones': []
            }

        # Calculate percentages
        total = sum(z['usage_count'] for z in zones)

        for zone in zones:
            zone['percentage'] = (zone['usage_count'] / total) * 100 if total > 0 else 0

        return {
            'zones': zones,
            'total_detections': total,
            'most_common': zones[0] if zones else None
        }

    def _update_pin_zone(self, cursor, course_name: str, hole_number: int,
                        pin_gps: Tuple[float, float]):
        """Updates pin zone heatmap based on new detection"""
        # Determine which zone this pin is in
        zone = self._determine_pin_zone(pin_gps)

        cursor.execute("""
            INSERT INTO pin_zones (course_name, hole_number, zone_name, center_lat, center_lon, usage_count)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(course_name, hole_number, zone_name)
            DO UPDATE SET usage_count = usage_count + 1
        """, (course_name, hole_number, zone, pin_gps[0], pin_gps[1]))

    def _determine_pin_zone(self, pin_gps: Tuple[float, float]) -> str:
        """
        Determines pin zone name (front/middle/back, left/center/right)

        In production, this would use actual green boundaries
        For now, returns a placeholder
        """
        # This is simplified - in production, you'd:
        # 1. Get green boundary polygon
        # 2. Calculate position relative to green center
        # 3. Return zone like "front_left", "middle_center", etc.

        return "middle_center"  # Placeholder

    def get_all_pins_for_course_today(self, course_name: str) -> Dict:
        """
        Gets all pin positions for a course today

        Useful for displaying pins for entire round

        Returns:
            Dict mapping hole_number -> pin_position
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT * FROM pin_positions
            WHERE course_name = ? AND date = ?
            ORDER BY hole_number
        """, (course_name, today))

        pins = {}
        for row in cursor.fetchall():
            pins[row['hole_number']] = dict(row)

        conn.close()

        return pins


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("PIN POSITION TRACKER")
    print("Crowdsourced daily pin positions")
    print("="*60)

    tracker = PinPositionTracker()

    # Simulate pin detection and recording
    course = "Pebble Beach Golf Links"

    print("\n--- Scenario: First Player of the Day ---")
    print(f"Course: {course}")
    print("Player 1 approaches Hole 1...")

    # Player 1 detects pin
    result = tracker.record_pin_detection(
        course_name=course,
        hole_number=1,
        pin_gps=(36.5674, -121.9500),  # Example coordinates
        detected_by="player1",
        confidence=0.85,
        flag_color="red"
    )

    print(f"Result: {result['message']}")

    # Check if today's pin exists
    print("\n--- Player 2 Checks for Today's Pin ---")
    todays_pin = tracker.get_todays_pin(course, 1)

    if todays_pin:
        print(f"✅ Pin already detected today!")
        print(f"   Location: {todays_pin['latitude']:.6f}, {todays_pin['longitude']:.6f}")
        print(f"   Verified by: {todays_pin['verified_count']} player(s)")
        print(f"   Flag color: {todays_pin['flag_color']}")
    else:
        print("❌ No pin detected yet today - be the first!")

    # Player 2 also detects it (verification)
    print("\n--- Player 2 Also Detects Pin (Verification) ---")
    result2 = tracker.record_pin_detection(
        course_name=course,
        hole_number=1,
        pin_gps=(36.5674, -121.9500),  # Same position
        detected_by="player2",
        confidence=0.90
    )

    print(f"Result: {result2['message']}")

    # Record more pins for history
    print("\n--- Building Historical Data ---")
    import random
    from datetime import timedelta

    # Simulate 10 days of pin positions
    base_lat, base_lon = 36.5674, -121.9500

    for i in range(10):
        # Vary pin position slightly each day
        pin_lat = base_lat + random.uniform(-0.0001, 0.0001)
        pin_lon = base_lon + random.uniform(-0.0001, 0.0001)

        tracker.record_pin_detection(
            course_name=course,
            hole_number=1,
            pin_gps=(pin_lat, pin_lon),
            detected_by=f"player{random.randint(1, 10)}",
            confidence=random.uniform(0.7, 0.95)
        )

    print("✅ 10 days of historical data added")

    # Get pin history
    print("\n--- Pin Position History (Last 10 Days) ---")
    history = tracker.get_pin_history(course, 1, days=10)

    for i, pin in enumerate(history[:5], 1):
        print(f"{i}. {pin['date']}: ({pin['latitude']:.6f}, {pin['longitude']:.6f}) "
              f"- {pin['verified_count']} verifications")

    # Get heatmap
    print("\n--- Pin Position Heatmap ---")
    heatmap = tracker.get_pin_heatmap(course, 1)

    print(f"Total detections: {heatmap['total_detections']}")
    if heatmap.get('most_common'):
        print(f"Most common zone: {heatmap['most_common']['zone_name']} "
              f"({heatmap['most_common']['percentage']:.1f}% of the time)")

    # Get all pins for today
    print("\n--- All Pins for Course Today ---")
    all_pins = tracker.get_all_pins_for_course_today(course)

    print(f"Pins detected today: {len(all_pins)} holes")
    for hole_num, pin in all_pins.items():
        print(f"  Hole {hole_num}: ({pin['latitude']:.6f}, {pin['longitude']:.6f})")

    print("\n" + "="*60)
    print("Benefits:")
    print("  ✅ First player detects pin → everyone else uses it")
    print("  ✅ Builds historical database of pin positions")
    print("  ✅ Can show 'pin is usually front-left on Sundays'")
    print("  ✅ Crowdsourced = free, scales automatically")
    print("="*60)
