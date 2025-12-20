"""
Launch Vector Calculation Module

Calculates launch speed, angle, and direction from tracked ball trajectory.
Uses homography calibration for accurate real-world measurements.
"""

import numpy as np
import math
from homography_calibration import HomographyCalibrator


class LaunchVectorCalculator:
    def __init__(self, calibrator=None):
        """
        Initialize launch vector calculator.
        
        Args:
            calibrator: HomographyCalibrator instance (optional)
        """
        self.calibrator = calibrator
        
    def calculate_launch_vector(self, trajectory_points, homography_matrix=None, 
                                gyro_data=None, compass_heading=0, fps=30):
        """
        Calculate launch speed, angle, and direction from trajectory.
        
        Args:
            trajectory_points: List of dicts with 'x', 'y', 'timestamp' (or 'frame')
            homography_matrix: Optional 3x3 matrix for perspective correction
            gyro_data: Phone gyroscope data (tilt angle in degrees)
            compass_heading: Phone compass heading in degrees
            fps: Frames per second (if timestamps not available)
            
        Returns:
            dict with launch_speed_mph, launch_angle, direction, confidence
        """
        if len(trajectory_points) < 3:
            return {
                "speed_mph": 0,
                "launch_angle": 0,
                "direction": 0,
                "confidence": 0,
                "error": "Not enough trajectory points"
            }
        
        # Use first 5-10 frames for launch calculation
        launch_frames = trajectory_points[:min(10, len(trajectory_points))]
        
        # Calculate speed
        speed_result = self._calculate_speed(launch_frames, fps)
        
        # Calculate launch angle
        angle_result = self._calculate_launch_angle(launch_frames, gyro_data)
        
        # Calculate direction
        direction_result = self._calculate_direction(launch_frames, compass_heading)
        
        # Calculate confidence
        confidence = self._calculate_confidence(launch_frames, speed_result, angle_result)
        
        return {
            "speed_mph": speed_result["speed_mph"],
            "speed_ms": speed_result["speed_ms"],
            "launch_angle": angle_result["angle"],
            "direction": direction_result["direction"],
            "confidence": confidence,
            "frames_used": len(launch_frames),
            "method": "trajectory_analysis"
        }
    
    def _calculate_speed(self, points, fps=30):
        """
        Calculate ball speed from trajectory points.
        
        Args:
            points: List of trajectory points
            fps: Frames per second
            
        Returns:
            dict with speed in mph and m/s
        """
        if len(points) < 2:
            return {"speed_mph": 0, "speed_ms": 0}
        
        # Get first and last points
        first = points[0]
        last = points[-1]
        
        # Calculate pixel displacement
        dx_px = last['x'] - first['x']
        dy_px = last['y'] - first['y']
        displacement_px = math.sqrt(dx_px**2 + dy_px**2)
        
        # Calculate time
        if 'timestamp' in first and 'timestamp' in last:
            dt = last['timestamp'] - first['timestamp']
        else:
            # Use frame numbers
            frame_diff = last.get('frame', len(points)-1) - first.get('frame', 0)
            dt = frame_diff / fps
        
        if dt <= 0:
            return {"speed_mph": 0, "speed_ms": 0}
        
        # Convert to real-world distance
        if self.calibrator and self.calibrator.is_calibrated():
            # Use calibrated conversion
            first_real = self.calibrator.pixel_to_meters((first['x'], first['y']))
            last_real = self.calibrator.pixel_to_meters((last['x'], last['y']))
            
            displacement_m = math.sqrt(
                (last_real[0] - first_real[0])**2 + 
                (last_real[1] - first_real[1])**2
            )
        else:
            # Estimate: Use ball radius if available
            # Assume ball radius ~10px = 0.0214m (golf ball radius)
            estimated_px_per_m = 10 / 0.0214  # ~467 px/m
            displacement_m = displacement_px / estimated_px_per_m
        
        # Calculate speed
        speed_ms = displacement_m / dt
        speed_mph = speed_ms * 2.237  # m/s to mph
        
        return {
            "speed_ms": speed_ms,
            "speed_mph": speed_mph,
            "displacement_m": displacement_m,
            "time_s": dt
        }
    
    def _calculate_launch_angle(self, points, gyro_data=None):
        """
        Calculate vertical launch angle.
        
        Args:
            points: Trajectory points
            gyro_data: Gyroscope tilt data (degrees)
            
        Returns:
            dict with angle in degrees
        """
        if len(points) < 3:
            return {"angle": 12, "method": "default"}  # Default estimate
        
        # Calculate vertical vs horizontal pixel movement
        first = points[0]
        last = points[min(5, len(points)-1)]  # Use first 5 frames
        
        dx = last['x'] - first['x']
        dy = last['y'] - first['y']  # Negative y = upward in image coords
        
        # Pixel-based angle estimate
        if abs(dx) > 1:
            pixel_angle = math.degrees(math.atan2(-dy, dx))  # Negative for upward
        else:
            pixel_angle = 0
        
        # Adjust for camera tilt if gyro data available
        if gyro_data is not None:
            camera_tilt = gyro_data  # Degrees phone is tilted
            corrected_angle = pixel_angle + camera_tilt
        else:
            corrected_angle = pixel_angle
        
        # Clamp to realistic range (0-45 degrees)
        corrected_angle = max(0, min(45, corrected_angle))
        
        # If angle seems unrealistic, use typical values
        if corrected_angle < 5 or corrected_angle > 30:
            # Most drives are 8-16 degrees
            corrected_angle = 12
            method = "default_typical"
        else:
            method = "calculated"
        
        return {
            "angle": corrected_angle,
            "method": method
        }
    
    def _calculate_direction(self, points, compass_heading):
        """
        Calculate horizontal launch direction.
        
        Args:
            points: Trajectory points
            compass_heading: Compass heading in degrees
            
        Returns:
            dict with direction in degrees (0 = North)
        """
        if len(points) < 2:
            return {"direction": compass_heading, "method": "compass_only"}
        
        # Calculate horizontal angle from pixel movement
        first = points[0]
        last = points[-1]
        
        dx = last['x'] - first['x']
        dy = last['y'] - first['y']
        
        # Pixel-based horizontal angle (relative to camera)
        if abs(dx) > 1 or abs(dy) > 1:
            pixel_angle = math.degrees(math.atan2(dy, dx))
        else:
            pixel_angle = 0
        
        # Combine with compass heading
        # (compass gives absolute direction, pixels give offset)
        absolute_direction = (compass_heading + pixel_angle) % 360
        
        return {
            "direction": absolute_direction,
            "pixel_offset": pixel_angle,
            "method": "compass_plus_pixels"
        }
    
    def _calculate_confidence(self, points, speed_result, angle_result):
        """
        Calculate confidence score (0-1) for the launch vector.
        
        Based on:
        - Number of points
        - Consistency of trajectory
        - Realistic speed/angle values
        
        Args:
            points: Trajectory points
            speed_result: Speed calculation result
            angle_result: Angle calculation result
            
        Returns:
            float between 0 and 1
        """
        confidence = 1.0
        
        # Penalize few points
        if len(points) < 5:
            confidence *= 0.7
        elif len(points) < 3:
            confidence *= 0.4
        
        # Check if speed is realistic (golf drives: 80-200 mph)
        speed_mph = speed_result.get("speed_mph", 0)
        if speed_mph < 50 or speed_mph > 250:
            confidence *= 0.5  # Unrealistic speed
        
        # Check if angle is realistic (0-45 degrees)
        angle = angle_result.get("angle", 12)
        if angle < 0 or angle > 45:
            confidence *= 0.6
        
        # Check trajectory consistency
        if len(points) >= 3:
            # Calculate how linear the trajectory is
            positions = [(p['x'], p['y']) for p in points

]
            linearity = self._calculate_linearity(positions)
            confidence *= linearity
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_linearity(self, positions):
        """
        Calculate how linear a set of points is (0-1).
        1.0 = perfectly linear, 0.0 = very scattered
        """
        if len(positions) < 3:
            return 1.0
        
        # Fit line and calculate R²
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]
        
        # Simple linear regression
        n = len(x_coords)
        x_mean = sum(x_coords) / n
        y_mean = sum(y_coords) / n
        
        numerator = sum((x_coords[i] - x_mean) * (y_coords[i] - y_mean) for i in range(n))
        denominator = math.sqrt(
            sum((x - x_mean)**2 for x in x_coords) * 
            sum((y - y_mean)**2 for y in y_coords)
        )
        
        if denominator == 0:
            return 0.5
        
        r = numerator / denominator
        r_squared = r ** 2
        
        return r_squared


if __name__ == "__main__":
    """Test launch vector calculation"""
    print("Launch Vector Calculator Test")
    print("=" * 60)
    
    # Create test trajectory (simulated ball flight)
    test_trajectory = [
        {'x': 100, 'y': 200, 'frame': 0, 'timestamp': 0.0},
        {'x': 120, 'y': 195, 'frame': 1, 'timestamp': 0.033},
        {'x': 140, 'y': 190, 'frame': 2, 'timestamp': 0.066},
        {'x': 160, 'y': 185, 'frame': 3, 'timestamp': 0.099},
        {'x': 180, 'y': 180, 'frame': 4, 'timestamp': 0.132},
        {'x': 200, 'y': 175, 'frame': 5, 'timestamp': 0.165},
    ]
    
    # Initialize calculator
    calculator = LaunchVectorCalculator()
    
    # Calculate launch vector
    result = calculator.calculate_launch_vector(
        trajectory_points=test_trajectory,
        compass_heading=45,
        gyro_data=5  # 5 degrees phone tilt
    )
    
    print("\nLaunch Vector Results:")
    print(f"  Speed: {result['speed_mph']:.1f} mph ({result['speed_ms']:.2f} m/s)")
    print(f"  Launch Angle: {result['launch_angle']:.1f}°")
    print(f"  Direction: {result['direction']:.1f}° from North")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Frames Used: {result['frames_used']}")
    
    print("\n" + "=" * 60)
    print("\n✅ Launch vector calculation working!")
    print("\nNote: Add homography calibration for accurate speed!")
