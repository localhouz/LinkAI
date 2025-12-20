"""
OpenStreetMap Golf Course Data Fetcher
Queries OSM Overpass API for golf course features
"""

import requests
import json
from typing import Dict, List, Optional


class OSMGolfFetcher:
    """Fetches golf course data from OpenStreetMap"""

    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def search_courses_by_name(self, course_name: str, country: str = "US") -> List[Dict]:
        """
        Searches for golf courses by name

        Args:
            course_name: Name of the golf course
            country: Country code (default: US)

        Returns:
            List of course dictionaries with basic info
        """
        # Overpass QL query to find golf courses by name
        query = f"""
        [out:json];
        area["ISO3166-1"="{country}"]["admin_level"="2"];
        (
          way["leisure"="golf_course"]["name"~"{course_name}",i](area);
          relation["leisure"="golf_course"]["name"~"{course_name}",i](area);
        );
        out center;
        """

        try:
            response = requests.post(self.overpass_url, data={"data": query}, timeout=30)
            response.raise_for_status()
            data = response.json()

            courses = []
            for element in data.get('elements', []):
                course = {
                    'id': element.get('id'),
                    'name': element.get('tags', {}).get('name', 'Unknown'),
                    'type': element.get('type'),
                }

                # Get center coordinates
                if 'center' in element:
                    course['lat'] = element['center']['lat']
                    course['lon'] = element['center']['lon']
                elif 'lat' in element and 'lon' in element:
                    course['lat'] = element['lat']
                    course['lon'] = element['lon']

                courses.append(course)

            return courses

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from OpenStreetMap: {e}")
            return []

    def get_course_details(self, lat: float, lon: float, radius: int = 1000) -> Dict:
        """
        Fetches detailed golf course features near a location

        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters (default: 1000)

        Returns:
            Dict with course features (greens, tees, fairways, hazards)
        """
        # Query for golf features around the location
        query = f"""
        [out:json];
        (
          way["golf"="green"](around:{radius},{lat},{lon});
          way["golf"="tee"](around:{radius},{lat},{lon});
          way["golf"="fairway"](around:{radius},{lat},{lon});
          way["golf"="bunker"](around:{radius},{lat},{lon});
          way["golf"="hole"](around:{radius},{lat},{lon});
          way["natural"="water"](around:{radius},{lat},{lon});
          node["golf"="pin"](around:{radius},{lat},{lon});
        );
        out geom;
        """

        try:
            response = requests.post(self.overpass_url, data={"data": query}, timeout=30)
            response.raise_for_status()
            data = response.json()

            features = {
                'greens': [],
                'tees': [],
                'fairways': [],
                'bunkers': [],
                'water': [],
                'pins': [],
                'holes': []  # Hole paths with hole numbers
            }

            for element in data.get('elements', []):
                tags = element.get('tags', {})
                golf_type = tags.get('golf', tags.get('natural', ''))

                feature_data = {
                    'id': element.get('id'),
                    'type': element.get('type'),
                    'tags': tags,
                    'ref': tags.get('ref'),  # Hole number
                    'par': tags.get('par'),  # Par for the hole
                    'name': tags.get('name'),  # Hole name if any
                }

                # Extract geometry
                if element['type'] == 'way' and 'geometry' in element:
                    feature_data['coords'] = [
                        (node['lat'], node['lon'])
                        for node in element['geometry']
                    ]
                    # For holes, first coord is usually tee, last is green
                    if len(feature_data['coords']) >= 2:
                        feature_data['tee_coord'] = feature_data['coords'][0]
                        feature_data['green_coord'] = feature_data['coords'][-1]
                elif element['type'] == 'node':
                    feature_data['coords'] = [(element['lat'], element['lon'])]

                # Categorize feature
                if golf_type == 'green':
                    features['greens'].append(feature_data)
                elif golf_type == 'tee':
                    features['tees'].append(feature_data)
                elif golf_type == 'fairway':
                    features['fairways'].append(feature_data)
                elif golf_type == 'bunker':
                    features['bunkers'].append(feature_data)
                elif golf_type == 'water':
                    features['water'].append(feature_data)
                elif golf_type == 'pin':
                    features['pins'].append(feature_data)
                elif golf_type == 'hole':
                    features['holes'].append(feature_data)

            # Sort holes by hole number if available
            features['holes'].sort(key=lambda h: int(h['ref']) if h.get('ref') and h['ref'].isdigit() else 99)
            
            return features

        except requests.exceptions.RequestException as e:
            print(f"Error fetching course details: {e}")
            return {'greens': [], 'tees': [], 'fairways': [], 'bunkers': [], 'water': [], 'pins': [], 'holes': []}

    def visualize_osm_course(self, course_name: str, output_file: str = "osm_course.html"):
        """
        Searches for a course and creates an interactive map

        Args:
            course_name: Name of the golf course
            output_file: Output HTML file path

        Returns:
            str: Path to output file or None if course not found
        """
        import folium

        print(f"Searching for '{course_name}' on OpenStreetMap...")
        courses = self.search_courses_by_name(course_name)

        if not courses:
            print(f"No courses found matching '{course_name}'")
            return None

        print(f"Found {len(courses)} course(s):")
        for i, course in enumerate(courses, 1):
            print(f"  {i}. {course['name']} (ID: {course['id']})")

        # Use first result
        selected_course = courses[0]
        if 'lat' not in selected_course or 'lon' not in selected_course:
            print("Course location not available")
            return None

        lat, lon = selected_course['lat'], selected_course['lon']
        print(f"\nFetching details for '{selected_course['name']}' at ({lat}, {lon})...")

        # Get detailed features
        features = self.get_course_details(lat, lon)

        # Create map
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles='OpenStreetMap')

        # Add course marker
        folium.Marker(
            [lat, lon],
            popup=f"<b>{selected_course['name']}</b>",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

        # Add greens
        for green in features['greens']:
            if 'coords' in green and green['coords']:
                folium.Polygon(
                    green['coords'],
                    color='darkgreen',
                    fill=True,
                    fillColor='green',
                    fillOpacity=0.6,
                    popup='Green'
                ).add_to(m)

        # Add tees
        for tee in features['tees']:
            if 'coords' in tee and tee['coords']:
                folium.Polygon(
                    tee['coords'],
                    color='blue',
                    fill=True,
                    fillColor='lightblue',
                    fillOpacity=0.5,
                    popup='Tee Box'
                ).add_to(m)

        # Add fairways
        for fairway in features['fairways']:
            if 'coords' in fairway and fairway['coords']:
                folium.Polygon(
                    fairway['coords'],
                    color='green',
                    fill=True,
                    fillColor='lightgreen',
                    fillOpacity=0.4,
                    popup='Fairway'
                ).add_to(m)

        # Add bunkers
        for bunker in features['bunkers']:
            if 'coords' in bunker and bunker['coords']:
                folium.Polygon(
                    bunker['coords'],
                    color='orange',
                    fill=True,
                    fillColor='yellow',
                    fillOpacity=0.5,
                    popup='Bunker'
                ).add_to(m)

        # Add water hazards
        for water in features['water']:
            if 'coords' in water and water['coords']:
                folium.Polygon(
                    water['coords'],
                    color='blue',
                    fill=True,
                    fillColor='cyan',
                    fillOpacity=0.6,
                    popup='Water Hazard'
                ).add_to(m)

        # Save map
        m.save(output_file)
        print(f"\nMap saved to: {output_file}")
        print(f"Found {len(features['greens'])} greens, {len(features['tees'])} tees, "
              f"{len(features['fairways'])} fairways, {len(features['bunkers'])} bunkers")

        return output_file


# Example usage
if __name__ == "__main__":
    fetcher = OSMGolfFetcher()

    # Try searching for a popular course
    # Replace with a course near you or a famous course
    print("Example: Searching for Pebble Beach Golf Links...")
    fetcher.visualize_osm_course("Pebble Beach", "pebble_beach.html")

    print("\n" + "="*60)
    print("Try your own course:")
    print("  from osm_fetcher import OSMGolfFetcher")
    print("  fetcher = OSMGolfFetcher()")
    print("  fetcher.visualize_osm_course('Your Course Name')")
    print("="*60)
