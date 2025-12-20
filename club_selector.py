"""
Club Selection Helper
Recommends clubs based on distance, conditions, and player history
"""

from shot_tracker import ShotTracker
from typing import Dict, List, Optional
import math


class ClubSelector:
    """Provides intelligent club recommendations"""

    def __init__(self, shot_tracker: ShotTracker):
        self.tracker = shot_tracker

        # Standard club distances for beginners (fallback if no data)
        self.default_distances = {
            'Driver': 220,
            '3-Wood': 200,
            '5-Wood': 180,
            '3-Hybrid': 170,
            '4-Hybrid': 160,
            '4-Iron': 150,
            '5-Iron': 140,
            '6-Iron': 130,
            '7-Iron': 120,
            '8-Iron': 110,
            '9-Iron': 100,
            'Pitching Wedge': 90,
            'Gap Wedge': 80,
            'Sand Wedge': 70,
            'Lob Wedge': 60,
            'Putter': 0
        }

    def recommend_club(self, player_id: str, target_distance: float,
                      wind_speed: float = 0, wind_direction: float = 0,
                      elevation_change: float = 0, lie: str = "fairway") -> List[Dict]:
        """
        Recommends clubs with adjustments for conditions

        Args:
            player_id: Player identifier
            target_distance: Target distance in yards
            wind_speed: Wind speed in mph (positive = headwind, negative = tailwind)
            wind_direction: Wind direction in degrees (0 = straight ahead)
            elevation_change: Elevation change in feet (positive = uphill, negative = downhill)
            lie: Current lie (fairway, rough, sand, etc.)

        Returns:
            List of club recommendations with adjusted distances
        """
        # Adjust distance for conditions
        adjusted_distance = self._adjust_for_conditions(
            target_distance, wind_speed, wind_direction, elevation_change, lie
        )

        print(f"\n📏 Target: {target_distance} yards")
        if adjusted_distance != target_distance:
            print(f"   Adjusted for conditions: {adjusted_distance:.0f} yards")

        # Get recommendations from player history
        recommendations = self.tracker.get_club_recommendation(player_id, adjusted_distance)

        # If no history, use defaults
        if not recommendations:
            recommendations = self._get_default_recommendations(adjusted_distance)

        # Add condition adjustments to each recommendation
        for rec in recommendations:
            rec['target_distance'] = target_distance
            rec['adjusted_distance'] = adjusted_distance
            rec['conditions'] = self._get_condition_summary(wind_speed, elevation_change, lie)

        return recommendations

    def _adjust_for_conditions(self, distance: float, wind_speed: float,
                               wind_direction: float, elevation: float, lie: str) -> float:
        """
        Adjusts distance for playing conditions

        Args:
            distance: Base distance in yards
            wind_speed: Wind speed in mph
            wind_direction: Wind direction in degrees
            elevation: Elevation change in feet
            lie: Current lie

        Returns:
            Adjusted distance in yards
        """
        adjusted = distance

        # Wind adjustment (rule of thumb: 1 mph wind = 1 yard per 10 yards distance)
        if wind_speed != 0:
            wind_effect = (wind_speed * distance / 10) * math.cos(math.radians(wind_direction))
            adjusted += wind_effect

        # Elevation adjustment (rule of thumb: 1 foot elevation = 1 yard distance)
        adjusted -= elevation

        # Lie adjustment
        lie_multipliers = {
            'fairway': 1.0,
            'tee': 1.0,
            'rough_light': 0.9,
            'rough_heavy': 0.75,
            'sand': 0.8,
            'hardpan': 1.05
        }
        adjusted *= lie_multipliers.get(lie, 1.0)

        return adjusted

    def _get_condition_summary(self, wind: float, elevation: float, lie: str) -> str:
        """Generates human-readable condition summary"""
        conditions = []

        if abs(wind) > 5:
            wind_type = "Headwind" if wind > 0 else "Tailwind"
            conditions.append(f"{wind_type} {abs(wind):.0f}mph")

        if abs(elevation) > 10:
            elev_type = "Uphill" if elevation > 0 else "Downhill"
            conditions.append(f"{elev_type} {abs(elevation):.0f}ft")

        if lie != "fairway":
            conditions.append(f"{lie.replace('_', ' ').title()}")

        return ", ".join(conditions) if conditions else "Perfect conditions"

    def _get_default_recommendations(self, distance: float) -> List[Dict]:
        """Fallback recommendations using standard distances"""
        recommendations = []

        for club, std_distance in self.default_distances.items():
            if club == 'Putter':
                continue

            diff = abs(std_distance - distance)

            # Show clubs within 20 yards
            if diff <= 20:
                confidence = max(0, 100 - diff * 5)
                recommendations.append({
                    'club': club,
                    'average_distance': std_distance,
                    'confidence': confidence,
                    'variance': 10,  # Assumed variance
                    'suggestion': self._get_club_suggestion(diff, std_distance, distance),
                    'source': 'default'
                })

        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        return recommendations

    def _get_club_suggestion(self, diff: float, mean: float, target: float) -> str:
        """Generates human-readable club suggestion"""
        if diff < 5:
            return "Perfect club choice"
        elif mean < target:
            return "Swing harder or club down"
        else:
            return "Swing easier or club up"

    def get_layup_options(self, player_id: str, distance_to_green: float,
                         hazard_distance: float) -> List[Dict]:
        """
        Suggests layup options when going for the green is risky

        Args:
            player_id: Player identifier
            distance_to_green: Distance to green in yards
            hazard_distance: Distance to hazard in yards

        Returns:
            List of layup club options
        """
        # Calculate safe layup distance (10-20 yards before hazard)
        safe_distance = hazard_distance - 20

        if safe_distance <= 50:
            safe_distance = hazard_distance - 10

        print(f"\n⚠️  LAYUP RECOMMENDATION")
        print(f"   Hazard at: {hazard_distance} yards")
        print(f"   Safe layup: {safe_distance} yards\n")

        return self.recommend_club(player_id, safe_distance)

    def compare_clubs(self, player_id: str, club1: str, club2: str) -> Dict:
        """
        Compares two clubs head-to-head

        Args:
            player_id: Player identifier
            club1: First club name
            club2: Second club name

        Returns:
            Comparison dictionary
        """
        stats = self.tracker.get_player_stats(player_id)

        if 'error' in stats:
            return {'error': 'No player data available'}

        club1_stats = stats['average_distances'].get(club1)
        club2_stats = stats['average_distances'].get(club2)

        if not club1_stats or not club2_stats:
            return {'error': 'One or both clubs not found in history'}

        comparison = {
            'club1': {
                'name': club1,
                'average': club1_stats['mean'],
                'consistency': club1_stats['stdev'],
                'range': f"{club1_stats['min']}-{club1_stats['max']}"
            },
            'club2': {
                'name': club2,
                'average': club2_stats['mean'],
                'consistency': club2_stats['stdev'],
                'range': f"{club2_stats['min']}-{club2_stats['max']}"
            },
            'difference': abs(club1_stats['mean'] - club2_stats['mean'])
        }

        # Determine which is more consistent
        if club1_stats['stdev'] < club2_stats['stdev']:
            comparison['more_consistent'] = club1
        else:
            comparison['more_consistent'] = club2

        return comparison


# Example usage
if __name__ == "__main__":
    from shot_tracker import ShotTracker

    print("="*60)
    print("CLUB SELECTION HELPER")
    print("="*60)

    # Create tracker and selector
    tracker = ShotTracker()
    selector = ClubSelector(tracker)

    # Add a player and some sample data
    tracker.add_player("player1", "Test Player", handicap=15.0)

    print("\nRecording sample shots for analysis...")
    # Driver
    for dist in [240, 250, 245, 235, 255]:
        tracker.record_shot("player1", "Driver", dist)

    # 7-Iron
    for dist in [150, 155, 148, 152, 151]:
        tracker.record_shot("player1", "7-Iron", dist)

    # Pitching Wedge
    for dist in [105, 110, 108, 112, 107]:
        tracker.record_shot("player1", "Pitching Wedge", dist)

    print("✅ Sample data recorded\n")

    # Test 1: Basic recommendation
    print("="*60)
    print("TEST 1: Basic Club Recommendation")
    print("="*60)
    target = 150
    print(f"Target distance: {target} yards\n")

    recommendations = selector.recommend_club("player1", target)
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec['club']:20s} "
              f"Confidence: {rec['confidence']:5.1f}%  "
              f"Avg: {rec['average_distance']:.0f}y")
        print(f"   {rec['suggestion']}")

    # Test 2: Recommendations with wind
    print("\n" + "="*60)
    print("TEST 2: Club Recommendation with Headwind")
    print("="*60)
    recommendations = selector.recommend_club(
        "player1",
        target_distance=150,
        wind_speed=15,  # 15 mph headwind
        wind_direction=0
    )
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec['club']:20s} "
              f"Confidence: {rec['confidence']:5.1f}%")
        print(f"   Conditions: {rec['conditions']}")

    # Test 3: Layup recommendation
    print("\n" + "="*60)
    print("TEST 3: Layup Recommendation")
    print("="*60)
    layups = selector.get_layup_options(
        "player1",
        distance_to_green=180,
        hazard_distance=160
    )
    for i, rec in enumerate(layups[:3], 1):
        print(f"{i}. {rec['club']:20s} Avg: {rec['average_distance']:.0f}y")

    # Test 4: Club comparison
    print("\n" + "="*60)
    print("TEST 4: Club Comparison")
    print("="*60)
    comp = selector.compare_clubs("player1", "Driver", "7-Iron")
    print(f"{comp['club1']['name']:15s} Avg: {comp['club1']['average']:.0f}y  "
          f"Range: {comp['club1']['range']}")
    print(f"{comp['club2']['name']:15s} Avg: {comp['club2']['average']:.0f}y  "
          f"Range: {comp['club2']['range']}")
    print(f"\nDifference: {comp['difference']:.0f} yards")
    print(f"More consistent: {comp['more_consistent']}")

    print("\n" + "="*60)
