"""
Group/Multiplayer Mode
Allows tracking multiple players and their balls simultaneously
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from shot_tracker import ShotTracker


class GroupSession:
    """Manages a group playing session with multiple players"""

    def __init__(self, db_path: str = "golf_data.db"):
        self.db_path = db_path
        self.shot_tracker = ShotTracker(db_path)
        self._init_database()

        self.active_session_id = None
        self.players_in_session = []

    def _init_database(self):
        """Creates database tables for group sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                course_name TEXT,
                current_hole INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                notes TEXT
            )
        """)

        # Session players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_players (
                session_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                player_name TEXT NOT NULL,
                order_position INTEGER,
                FOREIGN KEY (session_id) REFERENCES group_sessions(id),
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """)

        # Ball locations table (for tracking multiple balls in play)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ball_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                hole_number INTEGER NOT NULL,
                shot_id INTEGER,
                predicted_lat REAL,
                predicted_lon REAL,
                actual_lat REAL,
                actual_lon REAL,
                found INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES group_sessions(id),
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (shot_id) REFERENCES shots(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_session(self, course_name: str, player_ids: List[str],
                      player_names: List[str] = None) -> str:
        """
        Creates a new group session

        Args:
            course_name: Name of the course
            player_ids: List of player IDs
            player_names: Optional list of player names (if not in DB)

        Returns:
            str: Session ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Generate session ID
        session_id = f"session_{int(datetime.now().timestamp())}"

        # Create session
        cursor.execute("""
            INSERT INTO group_sessions (id, created_at, course_name, status)
            VALUES (?, ?, ?, 'active')
        """, (session_id, datetime.now().isoformat(), course_name))

        # Add players to session
        for i, player_id in enumerate(player_ids):
            player_name = player_names[i] if player_names and i < len(player_names) else f"Player {i+1}"

            # Ensure player exists
            self.shot_tracker.add_player(player_id, player_name)

            cursor.execute("""
                INSERT INTO session_players (session_id, player_id, player_name, order_position)
                VALUES (?, ?, ?, ?)
            """, (session_id, player_id, player_name, i))

        conn.commit()
        conn.close()

        self.active_session_id = session_id
        self.players_in_session = player_ids

        print(f"✅ Group session created: {session_id}")
        print(f"   Course: {course_name}")
        print(f"   Players: {', '.join(player_names if player_names else player_ids)}")

        return session_id

    def record_group_shot(self, player_id: str, club: str, distance_yards: float,
                         predicted_coords: Tuple[float, float] = None,
                         hole_number: int = 1):
        """
        Records a shot for a player in the active session

        Args:
            player_id: Player ID
            club: Club used
            distance_yards: Distance in yards
            predicted_coords: (lat, lon) predicted landing
            hole_number: Current hole number

        Returns:
            tuple: (shot_id, ball_location_id)
        """
        if not self.active_session_id:
            raise ValueError("No active session. Create a session first.")

        # Record shot in shot tracker
        shot_id = self.shot_tracker.record_shot(
            player_id=player_id,
            club=club,
            distance_yards=distance_yards,
            predicted_coords=predicted_coords,
            hole_number=hole_number
        )

        # Add ball location to track
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        pred_lat, pred_lon = predicted_coords if predicted_coords else (None, None)

        cursor.execute("""
            INSERT INTO ball_locations (
                session_id, player_id, hole_number, shot_id,
                predicted_lat, predicted_lon, found, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            self.active_session_id, player_id, hole_number, shot_id,
            pred_lat, pred_lon, datetime.now().isoformat()
        ))

        ball_location_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"⛳ Shot recorded for {player_id}")
        return (shot_id, ball_location_id)

    def mark_ball_found(self, ball_location_id: int, actual_coords: Tuple[float, float]):
        """
        Marks a ball as found and updates actual location

        Args:
            ball_location_id: Ball location ID
            actual_coords: (lat, lon) where ball was found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get shot_id from ball_location
        cursor.execute("SELECT shot_id FROM ball_locations WHERE id = ?", (ball_location_id,))
        result = cursor.fetchone()

        if result:
            shot_id = result[0]

            # Update ball location
            actual_lat, actual_lon = actual_coords
            cursor.execute("""
                UPDATE ball_locations
                SET actual_lat = ?, actual_lon = ?, found = 1
                WHERE id = ?
            """, (actual_lat, actual_lon, ball_location_id))

            # Update shot tracker
            if shot_id:
                self.shot_tracker.update_shot_actual_location(shot_id, actual_lat, actual_lon)

            conn.commit()
            print(f"✅ Ball found and location updated")

        conn.close()

    def get_all_ball_locations(self, hole_number: int = None) -> List[Dict]:
        """
        Gets all ball locations in the current session

        Args:
            hole_number: Optional hole number filter

        Returns:
            List of ball location dictionaries
        """
        if not self.active_session_id:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if hole_number:
            cursor.execute("""
                SELECT bl.*, sp.player_name
                FROM ball_locations bl
                JOIN session_players sp ON bl.player_id = sp.player_id
                WHERE bl.session_id = ? AND bl.hole_number = ?
                ORDER BY bl.timestamp DESC
            """, (self.active_session_id, hole_number))
        else:
            cursor.execute("""
                SELECT bl.*, sp.player_name
                FROM ball_locations bl
                JOIN session_players sp ON bl.player_id = sp.player_id
                WHERE bl.session_id = ?
                ORDER BY bl.timestamp DESC
            """, (self.active_session_id,))

        balls = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return balls

    def get_unfound_balls(self, hole_number: int = None) -> List[Dict]:
        """
        Gets all balls that haven't been found yet

        Args:
            hole_number: Optional hole number filter

        Returns:
            List of unfound ball location dictionaries
        """
        all_balls = self.get_all_ball_locations(hole_number)
        return [ball for ball in all_balls if ball['found'] == 0]

    def visualize_group_balls(self, hole_number: int, output_file: str = "group_balls_map.html"):
        """
        Creates a map showing all players' ball locations

        Args:
            hole_number: Hole number
            output_file: Output HTML file

        Returns:
            str: Path to output file
        """
        import folium

        balls = self.get_all_ball_locations(hole_number)

        if not balls:
            print("No balls to display")
            return None

        # Calculate center of map
        lats = [b['predicted_lat'] for b in balls if b['predicted_lat']]
        lons = [b['predicted_lon'] for b in balls if b['predicted_lon']]

        if not lats or not lons:
            print("No location data available")
            return None

        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)

        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=17)

        # Color map for different players
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred']
        player_colors = {}

        for i, player_id in enumerate(self.players_in_session):
            player_colors[player_id] = colors[i % len(colors)]

        # Add each ball
        for ball in balls:
            if not ball['predicted_lat'] or not ball['predicted_lon']:
                continue

            player_name = ball['player_name']
            color = player_colors.get(ball['player_id'], 'gray')
            found_status = "✅ Found" if ball['found'] else "❓ Not Found"

            # Predicted location
            folium.Circle(
                [ball['predicted_lat'], ball['predicted_lon']],
                radius=15,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.5 if ball['found'] else 0.7,
                popup=f"<b>{player_name}</b><br>{found_status}"
            ).add_to(m)

            # Actual location if found
            if ball['found'] and ball['actual_lat'] and ball['actual_lon']:
                folium.Marker(
                    [ball['actual_lat'], ball['actual_lon']],
                    popup=f"<b>{player_name}</b><br>Ball found here",
                    icon=folium.Icon(color=color, icon='check')
                ).add_to(m)

        # Save map
        m.save(output_file)
        print(f"Group balls map saved to: {output_file}")
        return output_file

    def get_session_summary(self) -> Dict:
        """
        Gets summary of the current session

        Returns:
            Dict with session statistics
        """
        if not self.active_session_id:
            return {"error": "No active session"}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get session info
        cursor.execute("SELECT * FROM group_sessions WHERE id = ?", (self.active_session_id,))
        session = dict(cursor.fetchone())

        # Get player stats
        cursor.execute("""
            SELECT sp.player_name, COUNT(bl.id) as total_shots,
                   SUM(bl.found) as balls_found
            FROM session_players sp
            LEFT JOIN ball_locations bl ON sp.player_id = bl.player_id
                AND bl.session_id = ?
            WHERE sp.session_id = ?
            GROUP BY sp.player_id
        """, (self.active_session_id, self.active_session_id))

        players = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'session': session,
            'players': players
        }


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("GROUP MODE - Multiplayer Ball Tracking")
    print("="*60)

    # Create group session
    group = GroupSession()

    print("\nCreating group session...")
    session_id = group.create_session(
        course_name="Pine Valley Golf Club",
        player_ids=["player1", "player2", "player3"],
        player_names=["Alice", "Bob", "Charlie"]
    )

    # Simulate shots from different players
    print("\n" + "="*60)
    print("Hole 1 - Tee Shots")
    print("="*60)

    # Alice's shot
    print("\nAlice hits...")
    group.record_group_shot(
        "player1", "Driver", 230,
        predicted_coords=(36.1240, -95.9890),
        hole_number=1
    )

    # Bob's shot
    print("Bob hits...")
    group.record_group_shot(
        "player2", "Driver", 210,
        predicted_coords=(36.1238, -95.9888),
        hole_number=1
    )

    # Charlie's shot
    print("Charlie hits...")
    shot_id, ball_id = group.record_group_shot(
        "player3", "Driver", 195,
        predicted_coords=(36.1235, -95.9885),
        hole_number=1
    )

    # Check unfound balls
    print("\n" + "="*60)
    print("Searching for balls...")
    print("="*60)
    unfound = group.get_unfound_balls(hole_number=1)
    print(f"Balls to find: {len(unfound)}")
    for ball in unfound:
        print(f"  - {ball['player_name']}'s ball (predicted: {ball['predicted_lat']}, {ball['predicted_lon']})")

    # Mark Charlie's ball as found
    print("\n✅ Found Charlie's ball!")
    group.mark_ball_found(ball_id, actual_coords=(36.1236, -95.9886))

    # Visualize all balls
    print("\n" + "="*60)
    print("Generating map...")
    print("="*60)
    group.visualize_group_balls(hole_number=1)

    # Session summary
    print("\n" + "="*60)
    print("SESSION SUMMARY")
    print("="*60)
    summary = group.get_session_summary()
    print(f"Course: {summary['session']['course_name']}")
    print(f"Status: {summary['session']['status']}")
    print("\nPlayers:")
    for player in summary['players']:
        found_rate = (player['balls_found'] / player['total_shots'] * 100) if player['total_shots'] > 0 else 0
        print(f"  {player['player_name']:10s} Shots: {player['total_shots']:2d}  "
              f"Found: {player['balls_found']:2d} ({found_rate:.0f}%)")

    print("\n" + "="*60)
