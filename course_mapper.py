"""
Course Mapping Module
Fetches and displays golf course maps using OpenStreetMap
"""

import folium
import json
from typing import Dict, List, Tuple


class CourseMapper:
    """Handles golf course mapping and visualization"""

    def __init__(self):
        self.courses = {}

    def create_course(self, name: str, center_lat: float, center_lon: float):
        """
        Creates a new course entry

        Args:
            name: Course name
            center_lat: Center latitude
            center_lon: Center longitude

        Returns:
            dict: Course data structure
        """
        course = {
            'name': name,
            'center': (center_lat, center_lon),
            'holes': []
        }
        self.courses[name] = course
        return course

    def add_hole(self, course_name: str, hole_number: int,
                 tee_coords: Tuple[float, float],
                 green_coords: Tuple[float, float],
                 par: int = 4,
                 hazards: List[Dict] = None):
        """
        Adds a hole to a course

        Args:
            course_name: Name of the course
            hole_number: Hole number (1-18)
            tee_coords: (lat, lon) of tee box
            green_coords: (lat, lon) of green center
            par: Par for the hole
            hazards: List of hazard dicts with 'type' and 'coords'
        """
        if course_name not in self.courses:
            raise ValueError(f"Course '{course_name}' not found. Create it first.")

        hole = {
            'number': hole_number,
            'tee': tee_coords,
            'green': green_coords,
            'par': par,
            'hazards': hazards or []
        }

        self.courses[course_name]['holes'].append(hole)

    def visualize_course(self, course_name: str, output_file: str = "course_map.html"):
        """
        Creates an interactive map of the course using folium

        Args:
            course_name: Name of the course to visualize
            output_file: Output HTML file path
        """
        if course_name not in self.courses:
            raise ValueError(f"Course '{course_name}' not found")

        course = self.courses[course_name]

        # Create map centered on course
        m = folium.Map(
            location=course['center'],
            zoom_start=16,
            tiles='OpenStreetMap'
        )

        # Add each hole
        for hole in course['holes']:
            # Tee marker
            folium.Marker(
                hole['tee'],
                popup=f"Hole {hole['number']} Tee (Par {hole['par']})",
                icon=folium.Icon(color='blue', icon='play')
            ).add_to(m)

            # Green marker
            folium.Marker(
                hole['green'],
                popup=f"Hole {hole['number']} Green",
                icon=folium.Icon(color='green', icon='flag')
            ).add_to(m)

            # Line from tee to green
            folium.PolyLine(
                [hole['tee'], hole['green']],
                color='darkgreen',
                weight=3,
                opacity=0.7,
                popup=f"Hole {hole['number']}"
            ).add_to(m)

            # Add hazards
            for hazard in hole['hazards']:
                folium.Circle(
                    hazard['coords'],
                    radius=20,  # meters
                    color='red' if hazard['type'] == 'water' else 'yellow',
                    fill=True,
                    popup=f"{hazard['type'].capitalize()} Hazard"
                ).add_to(m)

        # Save map
        m.save(output_file)
        print(f"Course map saved to: {output_file}")
        return output_file

    def save_course_data(self, course_name: str, filename: str):
        """
        Saves course data to JSON file

        Args:
            course_name: Name of course to save
            filename: Output JSON file path
        """
        if course_name not in self.courses:
            raise ValueError(f"Course '{course_name}' not found")

        with open(filename, 'w') as f:
            json.dump(self.courses[course_name], f, indent=2)
        print(f"Course data saved to: {filename}")

    def load_course_data(self, filename: str):
        """
        Loads course data from JSON file

        Args:
            filename: JSON file to load

        Returns:
            dict: Course data
        """
        with open(filename, 'r') as f:
            course = json.load(f)
        self.courses[course['name']] = course
        print(f"Loaded course: {course['name']}")
        return course

    def calculate_distance(self, coord1: Tuple[float, float],
                          coord2: Tuple[float, float]) -> float:
        """
        Calculates distance between two GPS coordinates using Haversine formula

        Args:
            coord1: (lat, lon) first point
            coord2: (lat, lon) second point

        Returns:
            float: Distance in meters
        """
        import math

        lat1, lon1 = coord1
        lat2, lon2 = coord2

        # Radius of Earth in meters
        R = 6371000

        # Convert to radians
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        # Haversine formula
        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        distance = R * c
        return distance


# Example usage
if __name__ == "__main__":
    # Create a sample course
    mapper = CourseMapper()

    # Example: Create a fictional course
    # (Replace with real GPS coordinates from your local course)
    mapper.create_course(
        name="Sample Golf Course",
        center_lat=36.1234,
        center_lon=-95.9876
    )

    # Add hole 1
    mapper.add_hole(
        course_name="Sample Golf Course",
        hole_number=1,
        tee_coords=(36.1234, -95.9876),
        green_coords=(36.1240, -95.9890),
        par=4,
        hazards=[
            {'type': 'water', 'coords': (36.1237, -95.9883)},
            {'type': 'bunker', 'coords': (36.1239, -95.9888)}
        ]
    )

    # Add hole 2
    mapper.add_hole(
        course_name="Sample Golf Course",
        hole_number=2,
        tee_coords=(36.1241, -95.9891),
        green_coords=(36.1235, -95.9900),
        par=3,
        hazards=[]
    )

    # Calculate distance
    distance = mapper.calculate_distance(
        (36.1234, -95.9876),
        (36.1240, -95.9890)
    )
    print(f"Hole 1 distance: {distance:.0f} meters ({distance * 1.09361:.0f} yards)")

    # Visualize
    mapper.visualize_course("Sample Golf Course", "sample_course.html")

    # Save data
    mapper.save_course_data("Sample Golf Course", "sample_course.json")
