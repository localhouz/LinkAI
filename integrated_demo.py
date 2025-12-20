"""
Integrated Demo: Ball Tracker + Course Mapping
Shows predicted ball landing location on a golf course map
"""

import folium
from course_mapper import CourseMapper
from location_service import LocationService
import argparse


class BallFinderApp:
    """Integrated ball finder application with course mapping"""

    def __init__(self):
        self.course_mapper = CourseMapper()
        self.location_service = LocationService()
        self.current_course = None
        self.current_hole = None
        self.user_location = None

    def load_course(self, course_file: str):
        """
        Loads a course from JSON file

        Args:
            course_file: Path to course JSON file
        """
        course = self.course_mapper.load_course_data(course_file)
        self.current_course = course['name']
        return course

    def set_current_hole(self, hole_number: int):
        """Sets the active hole for tracking"""
        self.current_hole = hole_number

    def detect_user_location(self):
        """Detects user's current location via IP"""
        self.user_location = self.location_service.get_user_location_by_ip()
        return self.user_location

    def find_nearby_courses(self, radius_km: int = 25):
        """
        Finds golf courses near the user

        Args:
            radius_km: Search radius in kilometers

        Returns:
            List of nearby courses
        """
        if not self.user_location:
            print("Detecting your location first...")
            self.detect_user_location()

        if not self.user_location:
            print("ERROR: Could not detect location")
            return []

        lat, lon = self.user_location
        return self.location_service.find_nearby_courses(lat, lon, radius_km)

    def show_nearby_courses_map(self, radius_km: int = 25, output_file: str = "nearby_courses.html"):
        """
        Creates a map showing nearby courses

        Args:
            radius_km: Search radius
            output_file: Output HTML file

        Returns:
            str: Path to output file
        """
        if not self.user_location:
            self.detect_user_location()

        if not self.user_location:
            print("ERROR: Could not detect location")
            return None

        lat, lon = self.user_location
        return self.location_service.visualize_nearby_courses(lat, lon, radius_km, output_file)

    def show_ball_landing_on_map(self,
                                  predicted_landing_lat: float,
                                  predicted_landing_lon: float,
                                  uncertainty_radius: float = 20,
                                  output_file: str = "ball_landing_map.html"):
        """
        Creates a map showing the predicted ball landing location

        Args:
            predicted_landing_lat: Predicted latitude of ball landing
            predicted_landing_lon: Predicted longitude of ball landing
            uncertainty_radius: Search radius in meters
            output_file: Output HTML file

        Returns:
            str: Path to output file
        """
        if not self.current_course or self.current_course not in self.course_mapper.courses:
            print("ERROR: No course loaded. Use load_course() first.")
            return None

        course = self.course_mapper.courses[self.current_course]

        # Find current hole data
        hole_data = None
        if self.current_hole:
            for hole in course['holes']:
                if hole['number'] == self.current_hole:
                    hole_data = hole
                    break

        # Create map centered on predicted landing
        m = folium.Map(
            location=[predicted_landing_lat, predicted_landing_lon],
            zoom_start=18,
            tiles='OpenStreetMap'
        )

        # If we have hole data, show it
        if hole_data:
            # Tee box
            folium.Marker(
                hole_data['tee'],
                popup=f"Hole {hole_data['number']} Tee (Par {hole_data['par']})",
                icon=folium.Icon(color='blue', icon='play')
            ).add_to(m)

            # Green
            folium.Marker(
                hole_data['green'],
                popup=f"Hole {hole_data['number']} Green",
                icon=folium.Icon(color='green', icon='flag')
            ).add_to(m)

            # Fairway line
            folium.PolyLine(
                [hole_data['tee'], hole_data['green']],
                color='darkgreen',
                weight=2,
                opacity=0.5,
                dash_array='10'
            ).add_to(m)

            # Hazards
            for hazard in hole_data.get('hazards', []):
                folium.Circle(
                    hazard['coords'],
                    radius=20,
                    color='red' if hazard['type'] == 'water' else 'yellow',
                    fill=True,
                    fillOpacity=0.3,
                    popup=f"{hazard['type'].capitalize()}"
                ).add_to(m)

        # MAIN FEATURE: Predicted ball landing zone
        folium.Circle(
            [predicted_landing_lat, predicted_landing_lon],
            radius=uncertainty_radius,
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.4,
            popup=f"<b>SEARCH HERE</b><br>Predicted ball location<br>±{uncertainty_radius}m",
            weight=3
        ).add_to(m)

        # Landing center marker
        folium.Marker(
            [predicted_landing_lat, predicted_landing_lon],
            popup="<b>Ball Landing (predicted)</b>",
            icon=folium.Icon(color='red', icon='certificate')
        ).add_to(m)

        # Save map
        m.save(output_file)
        print(f"Ball landing map saved to: {output_file}")
        print(f"Search zone: ±{uncertainty_radius}m radius around predicted location")

        return output_file

    def simulate_shot(self, hole_number: int,
                     distance_meters: float,
                     direction_offset: float = 0,
                     output_file: str = "simulated_shot.html"):
        """
        Simulates a golf shot and shows where to search for the ball

        Args:
            hole_number: Which hole
            distance_meters: How far the ball traveled
            direction_offset: Left/right offset in degrees (negative = left, positive = right)
            output_file: Output HTML file

        Returns:
            str: Path to output file
        """
        if not self.current_course or self.current_course not in self.course_mapper.courses:
            print("ERROR: No course loaded.")
            return None

        course = self.course_mapper.courses[self.current_course]

        # Find hole
        hole_data = None
        for hole in course['holes']:
            if hole['number'] == hole_number:
                hole_data = hole
                break

        if not hole_data:
            print(f"ERROR: Hole {hole_number} not found")
            return None

        self.set_current_hole(hole_number)

        # Calculate predicted landing using bearing and distance
        import math

        tee_lat, tee_lon = hole_data['tee']
        green_lat, green_lon = hole_data['green']

        # Calculate bearing from tee to green
        lat1, lon1 = math.radians(tee_lat), math.radians(tee_lon)
        lat2, lon2 = math.radians(green_lat), math.radians(green_lon)

        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.atan2(x, y)

        # Apply direction offset
        bearing += math.radians(direction_offset)

        # Calculate new position
        R = 6371000  # Earth radius in meters
        angular_distance = distance_meters / R

        lat3 = math.asin(
            math.sin(lat1) * math.cos(angular_distance) +
            math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing)
        )

        lon3 = lon1 + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat3)
        )

        predicted_lat = math.degrees(lat3)
        predicted_lon = math.degrees(lon3)

        print(f"\n{'='*60}")
        print(f"SHOT SIMULATION - Hole {hole_number}")
        print(f"{'='*60}")
        print(f"Distance: {distance_meters:.0f} meters ({distance_meters * 1.09361:.0f} yards)")
        print(f"Direction: {direction_offset:+.0f}° from tee-to-green line")
        print(f"Predicted landing: ({predicted_lat:.6f}, {predicted_lon:.6f})")

        # Show on map with 20m uncertainty
        return self.show_ball_landing_on_map(
            predicted_lat,
            predicted_lon,
            uncertainty_radius=20,
            output_file=output_file
        )


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Golf Ball Finder - Integrated Demo")
    print("="*60)

    # Create app
    app = BallFinderApp()

    # NEW FEATURE: Find nearby courses
    print("\n=== FEATURE 1: Find Nearby Courses ===")
    app.detect_user_location()

    if app.user_location:
        print("\nSearching for golf courses near you...")
        nearby = app.find_nearby_courses(radius_km=25)

        if nearby:
            print(f"\nFound {len(nearby)} courses within 25km:")
            for i, course in enumerate(nearby[:5], 1):  # Show top 5
                print(f"  {i}. {course['name']} - {course['distance_km']}km ({course['distance_miles']} mi)")

            print("\nGenerating map of nearby courses...")
            app.show_nearby_courses_map(radius_km=25, output_file="my_nearby_courses.html")
        else:
            print("No courses found nearby (OpenStreetMap may not have data for your area)")

    print("\n" + "="*60)

    # Option 1: Load a pre-saved course
    print("\n=== FEATURE 2: Ball Tracking Demo ===")
    print("Using sample course for demonstration...")

    # First, create the sample course if it doesn't exist
    mapper = CourseMapper()
    mapper.create_course(
        name="Demo Course",
        center_lat=36.1234,
        center_lon=-95.9876
    )

    mapper.add_hole(
        course_name="Demo Course",
        hole_number=1,
        tee_coords=(36.1234, -95.9876),
        green_coords=(36.1245, -95.9895),
        par=4,
        hazards=[
            {'type': 'bunker', 'coords': (36.1242, -95.9890)}
        ]
    )

    mapper.save_course_data("Demo Course", "demo_course.json")

    # Load it into the app
    app.load_course("demo_course.json")

    # Simulate different shots
    print("\n--- Simulation 1: Perfect shot ---")
    app.simulate_shot(
        hole_number=1,
        distance_meters=150,
        direction_offset=0,
        output_file="shot_1_perfect.html"
    )

    print("\n--- Simulation 2: Shot pulled left ---")
    app.simulate_shot(
        hole_number=1,
        distance_meters=140,
        direction_offset=-15,  # 15 degrees left
        output_file="shot_2_left.html"
    )

    print("\n--- Simulation 3: Shot pushed right ---")
    app.simulate_shot(
        hole_number=1,
        distance_meters=160,
        direction_offset=20,  # 20 degrees right
        output_file="shot_3_right.html"
    )

    print("\n" + "="*60)
    print("Open the HTML files to see the ball landing predictions!")
    print("="*60)
