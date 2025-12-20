"""
Location Service Module
Detects user location and finds nearby golf courses
"""

import requests
from typing import Dict, List, Tuple, Optional
import json


class LocationService:
    """Handles user location and nearby course discovery"""

    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.geocoding_url = "https://nominatim.openstreetmap.org/search"

    def get_user_location_by_ip(self) -> Optional[Tuple[float, float]]:
        """
        Gets approximate user location using IP geolocation (free, no API key)

        Returns:
            tuple: (latitude, longitude) or None if failed
        """
        try:
            # Using ipapi.co free API (no key required, 1000 requests/day)
            response = requests.get('https://ipapi.co/json/', timeout=10)
            response.raise_for_status()
            data = response.json()

            lat = data.get('latitude')
            lon = data.get('longitude')

            if lat and lon:
                city = data.get('city', 'Unknown')
                region = data.get('region', 'Unknown')
                country = data.get('country_name', 'Unknown')
                print(f"Location detected: {city}, {region}, {country}")
                print(f"Coordinates: ({lat}, {lon})")
                return (lat, lon)
            else:
                print("Could not determine location from IP")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error detecting location: {e}")
            return None

    def get_location_by_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Converts an address to GPS coordinates using OSM Nominatim

        Args:
            address: Address string (e.g., "1234 Main St, City, State")

        Returns:
            tuple: (latitude, longitude) or None if not found
        """
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            headers = {
                'User-Agent': 'GolfBallFinderApp/1.0'
            }

            response = requests.get(
                self.geocoding_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                display_name = data[0].get('display_name', address)
                print(f"Found location: {display_name}")
                print(f"Coordinates: ({lat}, {lon})")
                return (lat, lon)
            else:
                print(f"Could not find location for: {address}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error geocoding address: {e}")
            return None

    def find_nearby_courses(self, lat: float, lon: float, radius_km: int = 25) -> List[Dict]:
        """
        Finds golf courses near a location using OpenStreetMap

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers (default: 25km)

        Returns:
            List of course dictionaries with name, distance, coordinates
        """
        radius_meters = radius_km * 1000

        # Overpass query for golf courses
        query = f"""
        [out:json];
        (
          way["leisure"="golf_course"](around:{radius_meters},{lat},{lon});
          relation["leisure"="golf_course"](around:{radius_meters},{lat},{lon});
        );
        out center;
        """

        try:
            print(f"Searching for golf courses within {radius_km}km...")
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            courses = []
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                course_name = tags.get('name', 'Unnamed Course')

                # Get coordinates
                course_lat, course_lon = None, None
                if 'center' in element:
                    course_lat = element['center']['lat']
                    course_lon = element['center']['lon']
                elif 'lat' in element and 'lon' in element:
                    course_lat = element['lat']
                    course_lon = element['lon']

                if course_lat and course_lon:
                    # Calculate distance
                    distance = self._calculate_distance(
                        (lat, lon),
                        (course_lat, course_lon)
                    )

                    course_info = {
                        'name': course_name,
                        'lat': course_lat,
                        'lon': course_lon,
                        'distance_km': round(distance / 1000, 2),
                        'distance_miles': round(distance / 1609.34, 2),
                        'id': element.get('id'),
                        'website': tags.get('website', ''),
                        'phone': tags.get('phone', ''),
                        'holes': tags.get('holes', 'Unknown')
                    }
                    courses.append(course_info)

            # Sort by distance
            courses.sort(key=lambda x: x['distance_km'])

            print(f"Found {len(courses)} golf course(s)")
            return courses

        except requests.exceptions.RequestException as e:
            print(f"Error searching for courses: {e}")
            return []

    def _calculate_distance(self, coord1: Tuple[float, float],
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

        R = 6371000  # Earth radius in meters

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def visualize_nearby_courses(self, lat: float, lon: float,
                                 radius_km: int = 25,
                                 output_file: str = "nearby_courses.html"):
        """
        Creates a map showing nearby courses

        Args:
            lat: User latitude
            lon: User longitude
            radius_km: Search radius in km
            output_file: Output HTML file

        Returns:
            str: Path to output file
        """
        import folium

        courses = self.find_nearby_courses(lat, lon, radius_km)

        if not courses:
            print("No courses found nearby")
            return None

        # Create map centered on user location
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add user location marker
        folium.Marker(
            [lat, lon],
            popup="<b>Your Location</b>",
            icon=folium.Icon(color='red', icon='user', prefix='fa')
        ).add_to(m)

        # Add search radius circle
        folium.Circle(
            [lat, lon],
            radius=radius_km * 1000,
            color='blue',
            fill=False,
            weight=2,
            opacity=0.5,
            popup=f"Search radius: {radius_km}km"
        ).add_to(m)

        # Add course markers
        for i, course in enumerate(courses, 1):
            popup_html = f"""
            <b>{i}. {course['name']}</b><br>
            Distance: {course['distance_km']}km ({course['distance_miles']} miles)<br>
            Holes: {course['holes']}
            """
            if course['website']:
                popup_html += f"<br><a href='{course['website']}' target='_blank'>Website</a>"

            folium.Marker(
                [course['lat'], course['lon']],
                popup=popup_html,
                icon=folium.Icon(color='green', icon='flag-checkered', prefix='fa')
            ).add_to(m)

        m.save(output_file)
        print(f"\nMap saved to: {output_file}")
        return output_file


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("Golf Course Finder - Location Service")
    print("="*60)

    service = LocationService()

    # Method 1: Detect location by IP
    print("\n--- Method 1: Detect by IP ---")
    location = service.get_user_location_by_ip()

    if location:
        lat, lon = location
        print(f"\nSearching for nearby courses...")
        courses = service.find_nearby_courses(lat, lon, radius_km=25)

        if courses:
            print(f"\n{'='*60}")
            print("NEARBY GOLF COURSES")
            print(f"{'='*60}")
            for i, course in enumerate(courses[:10], 1):  # Show top 10
                print(f"{i}. {course['name']}")
                print(f"   Distance: {course['distance_km']}km ({course['distance_miles']} miles)")
                print(f"   Holes: {course['holes']}")
                print()

            # Create map
            service.visualize_nearby_courses(lat, lon, radius_km=25)

    # Method 2: Search by address
    print("\n" + "="*60)
    print("--- Method 2: Search by Address ---")
    print("Example: Try entering 'Pebble Beach, CA' or your city")
    print("="*60)

    # Example with a famous location
    address = "Pebble Beach, CA"
    print(f"\nSearching for: {address}")
    location = service.get_location_by_address(address)

    if location:
        lat, lon = location
        courses = service.find_nearby_courses(lat, lon, radius_km=10)

        if courses:
            print(f"\nTop 5 courses near {address}:")
            for i, course in enumerate(courses[:5], 1):
                print(f"  {i}. {course['name']} - {course['distance_km']}km away")
