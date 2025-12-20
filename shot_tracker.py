"""
Shot History & Statistics Module
Tracks all shots, calculates statistics, and provides insights
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import statistics


class ShotTracker:
    """Manages shot history and calculates player statistics"""

    def __init__(self, db_path: str = "golf_data.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Creates database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Shots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                player_id TEXT NOT NULL,
                course_name TEXT,
                hole_number INTEGER,
                shot_number INTEGER,
                club TEXT,
                distance_yards REAL,
                predicted_lat REAL,
                predicted_lon REAL,
                actual_lat REAL,
                actual_lon REAL,
                accuracy_yards REAL,
                lie TEXT,
                result TEXT,
                notes TEXT
            )
        """)

        # Rounds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                player_id TEXT NOT NULL,
                course_name TEXT,
                score INTEGER,
                putts INTEGER,
                fairways_hit INTEGER,
                greens_in_regulation INTEGER,
                total_holes INTEGER DEFAULT 18,
                notes TEXT
            )
        """)

        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                handicap REAL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def add_player(self, player_id: str, name: str, handicap: float = 0.0):
        """
        Adds a new player to the database

        Args:
            player_id: Unique player identifier
            name: Player name
            handicap: Golf handicap
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO players (id, name, handicap, created_at)
            VALUES (?, ?, ?, ?)
        """, (player_id, name, handicap, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def record_shot(self, player_id: str, club: str, distance_yards: float,
                   predicted_coords: Tuple[float, float] = None,
                   course_name: str = None, hole_number: int = None,
                   shot_number: int = None, lie: str = "fairway",
                   result: str = "good", notes: str = ""):
        """
        Records a shot in the database

        Args:
            player_id: Player identifier
            club: Club used (e.g., "Driver", "7-Iron", "Putter")
            distance_yards: Distance of shot in yards
            predicted_coords: (lat, lon) predicted landing
            course_name: Name of course
            hole_number: Hole number (1-18)
            shot_number: Shot number on this hole
            lie: Type of lie (fairway, rough, sand, etc.)
            result: Shot outcome (good, great, poor, lost)
            notes: Additional notes

        Returns:
            int: Shot ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        predicted_lat, predicted_lon = predicted_coords if predicted_coords else (None, None)

        cursor.execute("""
            INSERT INTO shots (
                timestamp, player_id, course_name, hole_number, shot_number,
                club, distance_yards, predicted_lat, predicted_lon,
                lie, result, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(), player_id, course_name, hole_number,
            shot_number, club, distance_yards, predicted_lat, predicted_lon,
            lie, result, notes
        ))

        shot_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return shot_id

    def update_shot_actual_location(self, shot_id: int, actual_lat: float, actual_lon: float):
        """
        Updates a shot with actual ball location after it's found

        Args:
            shot_id: Shot ID
            actual_lat: Actual latitude where ball was found
            actual_lon: Actual longitude where ball was found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get predicted location
        cursor.execute("""
            SELECT predicted_lat, predicted_lon FROM shots WHERE id = ?
        """, (shot_id,))
        result = cursor.fetchone()

        if result and result[0] and result[1]:
            # Calculate accuracy
            predicted_lat, predicted_lon = result
            accuracy = self._calculate_distance(
                (predicted_lat, predicted_lon),
                (actual_lat, actual_lon)
            ) * 1.09361  # Convert meters to yards

            cursor.execute("""
                UPDATE shots
                SET actual_lat = ?, actual_lon = ?, accuracy_yards = ?
                WHERE id = ?
            """, (actual_lat, actual_lon, accuracy, shot_id))
        else:
            cursor.execute("""
                UPDATE shots
                SET actual_lat = ?, actual_lon = ?
                WHERE id = ?
            """, (actual_lat, actual_lon, shot_id))

        conn.commit()
        conn.close()

    def get_player_stats(self, player_id: str, last_n_rounds: int = None) -> Dict:
        """
        Calculates comprehensive statistics for a player

        Args:
            player_id: Player identifier
            last_n_rounds: Only use last N rounds (None = all time)

        Returns:
            Dict with statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all shots (optionally filtered by recent rounds)
        if last_n_rounds:
            cursor.execute("""
                SELECT * FROM shots
                WHERE player_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (player_id, last_n_rounds * 20))  # Assume ~20 shots per round
        else:
            cursor.execute("""
                SELECT * FROM shots
                WHERE player_id = ?
            """, (player_id,))

        shots = [dict(row) for row in cursor.fetchall()]

        if not shots:
            conn.close()
            return {"error": "No shots found for this player"}

        # Calculate stats
        stats = {
            "total_shots": len(shots),
            "clubs": {},
            "average_distances": {},
            "accuracy": {},
            "lies": {},
            "results": {}
        }

        # Per-club statistics
        for shot in shots:
            club = shot['club']
            if club not in stats['clubs']:
                stats['clubs'][club] = {
                    'count': 0,
                    'distances': [],
                    'accuracy': []
                }

            stats['clubs'][club]['count'] += 1

            if shot['distance_yards']:
                stats['clubs'][club]['distances'].append(shot['distance_yards'])

            if shot['accuracy_yards']:
                stats['clubs'][club]['accuracy'].append(shot['accuracy_yards'])

        # Calculate averages and standard deviations
        for club, data in stats['clubs'].items():
            if data['distances']:
                stats['average_distances'][club] = {
                    'mean': round(statistics.mean(data['distances']), 1),
                    'median': round(statistics.median(data['distances']), 1),
                    'stdev': round(statistics.stdev(data['distances']), 1) if len(data['distances']) > 1 else 0,
                    'min': round(min(data['distances']), 1),
                    'max': round(max(data['distances']), 1)
                }

            if data['accuracy']:
                stats['accuracy'][club] = {
                    'mean': round(statistics.mean(data['accuracy']), 1),
                    'median': round(statistics.median(data['accuracy']), 1)
                }

        # Lie statistics
        for shot in shots:
            lie = shot['lie']
            stats['lies'][lie] = stats['lies'].get(lie, 0) + 1

        # Result statistics
        for shot in shots:
            result = shot['result']
            stats['results'][result] = stats['results'].get(result, 0) + 1

        conn.close()
        return stats

    def get_club_recommendation(self, player_id: str, target_distance: float) -> List[Dict]:
        """
        Recommends clubs based on target distance and player history

        Args:
            player_id: Player identifier
            target_distance: Target distance in yards

        Returns:
            List of club recommendations with confidence scores
        """
        stats = self.get_player_stats(player_id)

        if 'error' in stats:
            return []

        recommendations = []

        for club, distances in stats['average_distances'].items():
            mean_dist = distances['mean']
            stdev = distances['stdev']

            # Calculate how well this club matches the target
            diff = abs(mean_dist - target_distance)

            # Club is suitable if target is within 1.5 standard deviations
            if stdev > 0:
                confidence = max(0, 100 - (diff / stdev) * 33)
            else:
                confidence = 100 if diff < 5 else 0

            if confidence > 20:  # Only show relevant clubs
                recommendations.append({
                    'club': club,
                    'average_distance': mean_dist,
                    'confidence': round(confidence, 1),
                    'variance': stdev,
                    'suggestion': self._get_club_suggestion(diff, mean_dist, target_distance)
                })

        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations

    def _get_club_suggestion(self, diff: float, mean: float, target: float) -> str:
        """Generates human-readable club suggestion"""
        if diff < 5:
            return f"Perfect club choice"
        elif mean < target:
            return f"Swing harder or club down"
        else:
            return f"Swing easier or club up"

    def _calculate_distance(self, coord1: Tuple[float, float],
                           coord2: Tuple[float, float]) -> float:
        """Haversine distance in meters"""
        import math
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def export_stats_report(self, player_id: str, output_file: str = "player_stats.txt"):
        """
        Generates a text report of player statistics

        Args:
            player_id: Player identifier
            output_file: Output file path
        """
        stats = self.get_player_stats(player_id)

        with open(output_file, 'w') as f:
            f.write("="*60 + "\n")
            f.write("GOLF STATISTICS REPORT\n")
            f.write("="*60 + "\n\n")

            f.write(f"Total Shots: {stats['total_shots']}\n\n")

            f.write("CLUB DISTANCES (Yards)\n")
            f.write("-"*60 + "\n")
            for club, dist in sorted(stats['average_distances'].items(),
                                    key=lambda x: x[1]['mean'], reverse=True):
                f.write(f"{club:15s} Avg: {dist['mean']:6.1f}  "
                       f"Range: {dist['min']:.0f}-{dist['max']:.0f}  "
                       f"StDev: {dist['stdev']:.1f}\n")

            f.write("\n")

        print(f"Stats report saved to: {output_file}")


# Example usage
if __name__ == "__main__":
    tracker = ShotTracker()

    # Add a player
    tracker.add_player("player1", "John Doe", handicap=15.2)

    # Record some sample shots
    print("Recording sample shots...")
    tracker.record_shot("player1", "Driver", 250, result="good")
    tracker.record_shot("player1", "Driver", 245, result="great")
    tracker.record_shot("player1", "Driver", 235, result="good")
    tracker.record_shot("player1", "7-Iron", 150, result="good")
    tracker.record_shot("player1", "7-Iron", 155, result="great")
    tracker.record_shot("player1", "7-Iron", 148, result="good")
    tracker.record_shot("player1", "Putter", 20, result="good")
    tracker.record_shot("player1", "Pitching Wedge", 110, result="good")
    tracker.record_shot("player1", "Pitching Wedge", 105, result="poor")

    # Get stats
    print("\n" + "="*60)
    print("PLAYER STATISTICS")
    print("="*60)
    stats = tracker.get_player_stats("player1")
    print(f"Total shots: {stats['total_shots']}")
    print(f"\nClub averages:")
    for club, dist in sorted(stats['average_distances'].items(),
                            key=lambda x: x[1]['mean'], reverse=True):
        print(f"  {club:20s} {dist['mean']:6.1f} yards (±{dist['stdev']:.1f})")

    # Get club recommendation
    print("\n" + "="*60)
    print("CLUB RECOMMENDATIONS")
    print("="*60)
    target = 150
    print(f"Target distance: {target} yards\n")
    recommendations = tracker.get_club_recommendation("player1", target)
    for rec in recommendations:
        print(f"{rec['club']:20s} Confidence: {rec['confidence']:5.1f}%  "
              f"Avg: {rec['average_distance']:.0f}y  ({rec['suggestion']})")

    # Export report
    tracker.export_stats_report("player1")
