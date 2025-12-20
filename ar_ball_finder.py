"""
AR Ball Finder Module
Provides augmented reality guidance to help find lost golf balls
Uses phone GPS, compass, and camera to guide user to predicted location
"""

import math
from typing import Tuple, Dict, Optional
import numpy as np


class ARBallFinder:
    """
    Augmented Reality ball finding assistant

    Note: This is the Python prototype. For mobile implementation:
    - iOS: Use ARKit + CoreLocation + CoreMotion
    - Android: Use ARCore + Location Services + Sensors
    """

    def __init__(self):
        self.target_location = None
        self.user_location = None
        self.user_heading = 0  # Compass direction (0-360 degrees)
        self.search_radius = 20  # meters

    def set_target_ball_location(self, lat: float, lon: float, radius: float = 20):
        """
        Sets the predicted ball location

        Args:
            lat: Target latitude
            lon: Target longitude
            radius: Search radius uncertainty in meters
        """
        self.target_location = (lat, lon)
        self.search_radius = radius
        print(f"🎯 Target set: ({lat:.6f}, {lon:.6f}) ±{radius}m")

    def update_user_location(self, lat: float, lon: float):
        """
        Updates user's current GPS location

        Args:
            lat: User latitude
            lon: User longitude
        """
        self.user_location = (lat, lon)

    def update_user_heading(self, heading: float):
        """
        Updates user's compass heading

        Args:
            heading: Compass direction in degrees (0 = North, 90 = East, etc.)
        """
        self.user_heading = heading

    def get_guidance(self) -> Dict:
        """
        Calculates guidance information for finding the ball

        Returns:
            Dict with distance, bearing, direction instructions, and visual hints
        """
        if not self.target_location or not self.user_location:
            return {'error': 'Target or user location not set'}

        # Calculate distance and bearing
        distance = self._calculate_distance(self.user_location, self.target_location)
        bearing = self._calculate_bearing(self.user_location, self.target_location)

        # Calculate relative direction (where to turn)
        relative_direction = bearing - self.user_heading

        # Normalize to -180 to 180
        relative_direction = (relative_direction + 180) % 360 - 180

        # Generate instructions
        instruction = self._generate_instruction(distance, relative_direction)

        # Visual AR indicators
        ar_indicator = self._generate_ar_indicator(distance, relative_direction)

        # Hot/Cold indicator
        temperature = self._get_temperature_indicator(distance)

        return {
            'distance_meters': round(distance, 1),
            'distance_yards': round(distance * 1.09361, 1),
            'bearing_absolute': round(bearing, 1),
            'bearing_relative': round(relative_direction, 1),
            'instruction': instruction,
            'ar_indicator': ar_indicator,
            'temperature': temperature,
            'in_search_zone': distance <= self.search_radius
        }

    def _calculate_distance(self, coord1: Tuple[float, float],
                           coord2: Tuple[float, float]) -> float:
        """Haversine distance in meters"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _calculate_bearing(self, coord1: Tuple[float, float],
                          coord2: Tuple[float, float]) -> float:
        """
        Calculates bearing from coord1 to coord2
        Returns: Bearing in degrees (0-360, where 0 = North)
        """
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        dlon = lon2 - lon1

        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - \
            math.sin(lat1) * math.cos(lat2) * math.cos(dlon)

        bearing = math.atan2(x, y)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360

        return bearing

    def _generate_instruction(self, distance: float, relative_bearing: float) -> str:
        """
        Generates human-readable walking instructions

        Args:
            distance: Distance in meters
            relative_bearing: Bearing relative to current heading

        Returns:
            Instruction string
        """
        # Convert to yards for readability
        yards = distance * 1.09361

        if distance < 2:
            return "🎉 YOU'RE HERE! Look around for the ball."

        # Direction instruction
        if abs(relative_bearing) < 15:
            direction = "straight ahead"
        elif abs(relative_bearing) > 165:
            direction = "behind you (turn around)"
        elif relative_bearing > 0:
            if relative_bearing < 45:
                direction = "slightly right"
            elif relative_bearing < 90:
                direction = "to your right"
            elif relative_bearing < 135:
                direction = "sharp right"
            else:
                direction = "behind right"
        else:
            if relative_bearing > -45:
                direction = "slightly left"
            elif relative_bearing > -90:
                direction = "to your left"
            elif relative_bearing > -135:
                direction = "sharp left"
            else:
                direction = "behind left"

        if yards < 10:
            return f"⛳ Ball is {yards:.0f} yards {direction}. Almost there!"
        else:
            return f"🚶 Walk {yards:.0f} yards {direction}"

    def _generate_ar_indicator(self, distance: float, relative_bearing: float) -> Dict:
        """
        Generates visual indicators for AR overlay

        Returns:
            Dict with visual indicator data
        """
        # Arrow direction
        arrow_rotation = relative_bearing

        # Arrow size based on distance (larger when closer)
        if distance < 5:
            arrow_size = "large"
            arrow_color = "green"
        elif distance < 15:
            arrow_size = "medium"
            arrow_color = "yellow"
        else:
            arrow_size = "small"
            arrow_color = "red"

        # Pulsing effect when very close
        pulse = distance < 3

        return {
            'arrow_rotation': arrow_rotation,
            'arrow_size': arrow_size,
            'arrow_color': arrow_color,
            'pulse': pulse,
            'show_circle': distance <= self.search_radius
        }

    def _get_temperature_indicator(self, distance: float) -> str:
        """
        Gets "hot/cold" indicator based on distance

        Args:
            distance: Distance in meters

        Returns:
            Temperature string
        """
        if distance < 2:
            return "🔥 BURNING HOT!"
        elif distance < 5:
            return "🔥 Very Hot"
        elif distance < 10:
            return "🌡️ Hot"
        elif distance < 20:
            return "🌡️ Warm"
        elif distance < 40:
            return "❄️ Cool"
        elif distance < 60:
            return "❄️ Cold"
        else:
            return "🧊 Freezing"

    def simulate_search(self, start_location: Tuple[float, float],
                       target_location: Tuple[float, float],
                       heading: float = 0):
        """
        Simulates a search scenario for testing

        Args:
            start_location: Starting (lat, lon)
            target_location: Target (lat, lon)
            heading: Initial compass heading
        """
        self.set_target_ball_location(target_location[0], target_location[1])
        self.update_user_location(start_location[0], start_location[1])
        self.update_user_heading(heading)

        print("\n" + "="*60)
        print("AR BALL FINDER - SIMULATION")
        print("="*60)

        guidance = self.get_guidance()

        print(f"\n📍 Your location: {start_location}")
        print(f"🎯 Ball location: {target_location}")
        print(f"🧭 Your heading:  {heading}° (0=North)")
        print(f"\n{guidance['instruction']}")
        print(f"\nDistance: {guidance['distance_yards']:.1f} yards")
        print(f"Temperature: {guidance['temperature']}")
        print(f"Turn: {guidance['bearing_relative']:.0f}° "
              f"({'right' if guidance['bearing_relative'] > 0 else 'left'})")

        if guidance['in_search_zone']:
            print(f"\n✅ You're in the search zone! Look carefully.")

        # Simulate walking path
        print(f"\n{'='*60}")
        print("SIMULATED WALK TO BALL")
        print(f"{'='*60}")

        # Simulate 10 steps toward the ball
        for step in range(1, 11):
            # Move 1/10 of the way toward target each step
            lat = start_location[0] + (target_location[0] - start_location[0]) * step / 10
            lon = start_location[1] + (target_location[1] - start_location[1]) * step / 10

            self.update_user_location(lat, lon)
            guidance = self.get_guidance()

            print(f"\nStep {step}: {guidance['distance_yards']:.1f} yards  "
                  f"{guidance['temperature']}")

            if guidance['in_search_zone']:
                print("  ✅ Entered search zone!")
                break


class ARVisualization:
    """
    Helper class for generating AR visualization assets
    (For mobile app implementation)
    """

    @staticmethod
    def generate_ar_arrow_svg(rotation: float, color: str = "red") -> str:
        """
        Generates SVG code for AR arrow overlay

        Args:
            rotation: Rotation in degrees
            color: Arrow color

        Returns:
            SVG string
        """
        return f"""
        <svg width="200" height="200" viewBox="0 0 200 200"
             style="transform: rotate({rotation}deg)">
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          <g filter="url(#glow)">
            <path d="M100 20 L140 80 L115 80 L115 140 L85 140 L85 80 L60 80 Z"
                  fill="{color}" stroke="white" stroke-width="3"/>
          </g>
          <circle cx="100" cy="160" r="8" fill="{color}" stroke="white" stroke-width="2"/>
        </svg>
        """

    @staticmethod
    def generate_search_circle_overlay(radius_meters: float) -> str:
        """
        Generates overlay for search zone circle
        (For AR implementation)
        """
        return f"""
        Search Zone:
        - Draw circle on ground plane
        - Radius: {radius_meters}m
        - Semi-transparent yellow fill
        - Dashed border
        - Label: "Search in this area"
        """


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("AR BALL FINDER - Interactive Demo")
    print("="*60)

    finder = ARBallFinder()

    # Test scenario: User lost ball at a course
    user_start = (36.1234, -95.9876)  # User's current location
    ball_location = (36.1240, -95.9890)  # Predicted ball location
    user_heading = 45  # User facing northeast

    # Run simulation
    finder.simulate_search(user_start, ball_location, user_heading)

    # Show AR visualization example
    print("\n" + "="*60)
    print("AR OVERLAY EXAMPLE")
    print("="*60)
    print("\nFor mobile app, this would show:")
    print("  - Camera view of surroundings")
    print("  - Rotating arrow pointing to ball")
    print("  - Distance indicator overlay")
    print("  - Hot/cold temperature gauge")
    print("  - Search zone circle on ground (when close)")
    print("  - Haptic feedback (vibration when getting warmer)")

    # Generate sample AR arrow
    viz = ARVisualization()
    arrow_svg = viz.generate_ar_arrow_svg(rotation=45, color="green")

    print("\n" + "="*60)
    print("MOBILE IMPLEMENTATION NOTES")
    print("="*60)
    print("""
iOS (ARKit + Swift):
- Use ARWorldTrackingConfiguration for camera + motion
- CoreLocation for GPS
- CoreMotion for compass heading
- SCNNode with arrow 3D model for direction indicator
- Haptic feedback via UIImpactFeedbackGenerator

Android (ARCore + Kotlin):
- Use ArFragment for camera view
- FusedLocationProviderClient for GPS
- SensorManager for compass (TYPE_ROTATION_VECTOR)
- Anchor + Renderable for AR arrow
- Vibration via Vibrator service

React Native:
- react-native-arkit / viro-react for AR
- react-native-geolocation for GPS
- react-native-sensors for compass
- Custom native modules for advanced AR features
    """)

    print("="*60)
    print("✅ AR Ball Finder module complete!")
    print("="*60)
