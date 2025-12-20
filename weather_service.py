"""
Weather API Integration for Wind Data

Fetches current wind conditions from OpenWeatherMap API.
Wind significantly affects golf ball trajectories (10mph = 15-20 yard difference).
"""

import requests
import time
import os


class WeatherService:
    def __init__(self, api_key=None):
        """
        Initialize weather service.
        
        Args:
            api_key: OpenWeatherMap API key (or set OPENWEATHER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        
        # Cache to avoid excessive API calls
        self.cache = {}
        self.cache_duration = 600  # 10 minutes
        
    def get_wind_data(self, lat, lon):
        """
        Get current wind conditions for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            dict with wind data or None if API fails
        """
        if not self.api_key:
            print("Warning: No OpenWeatherMap API key. Using no wind.")
            return {"wind_speed_mph": 0, "wind_direction_deg": 0, "source": "default"}
        
        # Check cache
        cache_key = f"{lat:.2f},{lon:.2f}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        # Fetch from API
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'  # Get wind in m/s
            }
            
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract wind data
            wind_speed_mps = data.get('wind', {}).get('speed', 0)
            wind_direction_deg = data.get('wind', {}).get('deg', 0)
            
            # Convert to mph
            wind_speed_mph = wind_speed_mps * 2.237
            
            result = {
                "wind_speed_mph": round(wind_speed_mph, 1),
                "wind_direction_deg": wind_direction_deg,
                "wind_speed_mps": wind_speed_mps,
                "temperature_f": self._celsius_to_fahrenheit(data.get('main', {}).get('temp', 20)),
                "humidity": data.get('main', {}).get('humidity', 50),
                "description": data.get('weather', [{}])[0].get('description', 'unknown'),
                "source": "openweathermap"
            }
            
            # Cache result
            self.cache[cache_key] = (result, time.time())
            
            return result
            
        except requests.RequestException as e:
            print(f"Weather API error: {e}")
            return {"wind_speed_mph": 0, "wind_direction_deg": 0, "source": "error"}
        except Exception as e:
            print(f"Unexpected weather error: {e}")
            return {"wind_speed_mph": 0, "wind_direction_deg": 0, "source": "error"}
    
    def _celsius_to_fahrenheit(self, celsius):
        """Convert Celsius to Fahrenheit."""
        return celsius * 9/5 + 32
    
    def get_wind_relative_to_shot(self, lat, lon, shot_bearing_deg):
        """
        Get wind data relative to shot direction.
        
        Args:
            lat: Latitude
            lon: Longitude
            shot_bearing_deg: Direction of shot (0=North, 90=East, etc.)
            
        Returns:
            dict with relative wind data
        """
        wind_data = self.get_wind_data(lat, lon)
        
        if not wind_data:
            return None
        
        wind_direction = wind_data['wind_direction_deg']
        wind_speed = wind_data['wind_speed_mph']
        
        # Calculate relative wind direction
        # 0° = headwind, 90° = right crosswind, 180° = tailwind, 270° = left crosswind
        relative_direction = (wind_direction - shot_bearing_deg + 360) % 360
        
        # Categorize wind
        if relative_direction < 45 or relative_direction > 315:
            wind_type = "headwind"
        elif 45 <= relative_direction < 135:
            wind_type = "right_crosswind"
        elif 135 <= relative_direction < 225:
            wind_type = "tailwind"
        else:
            wind_type = "left_crosswind"
        
        return {
            **wind_data,
            "relative_direction_deg": relative_direction,
            "wind_type": wind_type,
            "headwind_component": wind_speed * abs(1 - (relative_direction / 180)),
            "crosswind_component": wind_speed * abs((90 - relative_direction) / 90)
        }
    
    def format_wind_description(self, wind_data):
        """
        Create human-readable wind description.
        
        Args:
            wind_data: Wind data dict
            
        Returns:
            str description
        """
        speed = wind_data.get('wind_speed_mph', 0)
        
        if speed < 1:
            return "Calm (no wind)"
        elif speed < 5:
            return f"Light breeze ({speed:.0f} mph)"
        elif speed < 10:
            return f"Moderate breeze ({speed:.0f} mph)"
        elif speed < 15:
            return f"Fresh wind ({speed:.0f} mph)"
        else:
            return f"Strong wind ({speed:.0f} mph)"


# Singleton instance
_weather_service = None

def get_weather_service(api_key=None):
    """Get or create weather service singleton."""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService(api_key)
    return _weather_service


if __name__ == "__main__":
    """Test weather service"""
    print("Weather Service Test")
    print("=" * 60)
    
    # Note: Set OPENWEATHER_API_KEY environment variable to test
    service = WeatherService()
    
    # Test location (Los Angeles)
    lat, lon = 34.0522, -118.2437
    
    print(f"\nFetching weather for {lat}, {lon}...")
    print("(Set OPENWEATHER_API_KEY env var for live data)")
    
    wind_data = service.get_wind_data(lat, lon)
    
    if wind_data:
        print(f"\nWind Data:")
        print(f"  Speed: {wind_data['wind_speed_mph']} mph")
        print(f"  Direction: {wind_data['wind_direction_deg']}°")
        print(f"  Description: {service.format_wind_description(wind_data)}")
        print(f"  Source: {wind_data['source']}")
        
        if 'temperature_f' in wind_data:
            print(f"  Temperature: {wind_data['temperature_f']:.1f}°F")
            print(f"  Humidity: {wind_data['humidity']}%")
    
    # Test relative wind
    shot_bearing = 0  # Shot going North
    relative_wind = service.get_wind_relative_to_shot(lat, lon, shot_bearing)
    
    if relative_wind:
        print(f"\nWind relative to shot (bearing {shot_bearing}°):")
        print(f"  Type: {relative_wind['wind_type']}")
        print(f"  Relative direction: {relative_wind['relative_direction_deg']:.0f}°")
    
    print("\n" + "=" * 60)
    print("\nTo use live weather data:")
    print("1. Sign up at https://openweathermap.org/api")
    print("2. Get a free API key (1000 calls/day)")
    print("3. Set environment variable: OPENWEATHER_API_KEY=your_key")
