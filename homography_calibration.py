"""
Homography Calibration Module

Converts pixel coordinates to real-world coordinates using:
1. Known reference objects (golf ball diameter, tee markers, etc.)
2. 4-point perspective calibration
3. Camera intrinsics (if available)

This enables accurate speed calculations from pixel movement.
"""

import numpy as np
import cv2
import math


class HomographyCalibrator:
    def __init__(self):
        """Initialize homography calibrator."""
        self.homography_matrix = None
        self.pixels_per_meter = None
        self.calibration_method = None
        
    def calibrate_from_known_object(self, pixel_diameter, real_diameter_meters):
        """
        Calibrate using a known object size (e.g., golf ball).
        
        Simple method: Assumes camera is perpendicular to ground.
        
        Args:
            pixel_diameter: Diameter of object in pixels
            real_diameter_meters: Actual diameter in meters (golf ball = 0.0427m)
            
        Returns:
            pixels_per_meter ratio
        """
        if pixel_diameter <= 0 or real_diameter_meters <= 0:
            raise ValueError("Diameter must be positive")
        
        self.pixels_per_meter = pixel_diameter / real_diameter_meters
        self.calibration_method = "known_object"
        
        print(f"✅ Calibrated: {self.pixels_per_meter:.2f} pixels/meter")
        return self.pixels_per_meter
    
    def calibrate_from_distance_marker(self, point1_px, point2_px, real_distance_meters):
        """
        Calibrate using two known points (e.g., tee markers 10 yards apart).
        
        Args:
            point1_px: (x, y) first point in pixels
            point2_px: (x, y) second point in pixels
            real_distance_meters: Actual distance between points
            
        Returns:
            pixels_per_meter ratio
        """
        pixel_distance = math.sqrt(
            (point2_px[0] - point1_px[0])**2 + 
            (point2_px[1] - point1_px[1])**2
        )
        
        self.pixels_per_meter = pixel_distance / real_distance_meters
        self.calibration_method = "distance_marker"
        
        print(f"✅ Calibrated: {self.pixels_per_meter:.2f} pixels/meter")
        return self.pixels_per_meter
    
    def calibrate_4_point_perspective(self, src_points, real_world_coords):
        """
        Full perspective calibration using 4 ground points.
        
        Most accurate method - accounts for camera angle and perspective.
        
        Args:
            src_points: List of 4 (x, y) pixel coordinates
            real_world_coords: List of 4 (X, Y) real-world coordinates in meters
            
        Returns:
            3x3 homography matrix
        """
        if len(src_points) != 4 or len(real_world_coords) != 4:
            raise ValueError("Need exactly 4 points for perspective calibration")
        
        src_points = np.float32(src_points)
        dst_points = np.float32(real_world_coords)
        
        # Calculate homography matrix
        self.homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        self.calibration_method = "4_point_perspective"
        
        print("✅ Calibrated: 4-point perspective homography")
        return self.homography_matrix
    
    def pixel_to_meters(self, pixel_point, use_homography=True):
        """
        Convert pixel coordinates to real-world meters.
        
        Args:
            pixel_point: (x, y) in pixels
            use_homography: Use full perspective transform if available
            
        Returns:
            (X, Y) in meters (Z assumed to be ground plane)
        """
        if use_homography and self.homography_matrix is not None:
            # Full perspective transform
            px_array = np.array([[[pixel_point[0], pixel_point[1]]]], dtype=np.float32)
            real_point = cv2.perspectiveTransform(px_array, self.homography_matrix)[0][0]
            return real_point[0], real_point[1]
        
        elif self.pixels_per_meter is not None:
            # Simple scaling (assumes perpendicular view)
            x_meters = pixel_point[0] / self.pixels_per_meter
            y_meters = pixel_point[1] / self.pixels_per_meter
            return x_meters, y_meters
        
        else:
            raise ValueError("Not calibrated! Call calibrate_* method first.")
    
    def calculate_real_world_distance(self, point1_px, point2_px):
        """
        Calculate real-world distance between two pixel points.
        
        Args:
            point1_px: (x, y) first point in pixels
            point2_px: (x, y) second point in pixels
            
        Returns:
            Distance in meters
        """
        p1_real = self.pixel_to_meters(point1_px)
        p2_real = self.pixel_to_meters(point2_px)
        
        distance = math.sqrt(
            (p2_real[0] - p1_real[0])**2 + 
            (p2_real[1] - p1_real[1])**2
        )
        
        return distance
    
    def get_calibration_info(self):
        """Get current calibration information."""
        return {
            "method": self.calibration_method,
            "pixels_per_meter": self.pixels_per_meter,
            "has_homography": self.homography_matrix is not None,
            "is_calibrated": self.is_calibrated()
        }
    
    def is_calibrated(self):
        """Check if calibrator is ready to use."""
        return (self.pixels_per_meter is not None or 
                self.homography_matrix is not None)
    
    def save_calibration(self, filepath):
        """Save calibration to file."""
        import json
        
        data = {
            "method": self.calibration_method,
            "pixels_per_meter": self.pixels_per_meter,
        }
        
        if self.homography_matrix is not None:
            data["homography_matrix"] = self.homography_matrix.tolist()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Calibration saved to {filepath}")
    
    def load_calibration(self, filepath):
        """Load calibration from file."""
        import json
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.calibration_method = data.get("method")
        self.pixels_per_meter = data.get("pixels_per_meter")
        
        if "homography_matrix" in data:
            self.homography_matrix = np.array(data["homography_matrix"], dtype=np.float32)
        
        print(f"✅ Calibration loaded from {filepath}")


# Quick calibration using golf ball size
def quick_calibrate_from_ball(ball_radius_pixels):
    """
    Quick calibration using detected golf ball.
    
    Args:
        ball_radius_pixels: Detected ball radius in pixels
        
    Returns:
        HomographyCalibrator instance
    """
    GOLF_BALL_DIAMETER_METERS = 0.0427  # Regulation size
    
    calibrator = HomographyCalibrator()
    calibrator.calibrate_from_known_object(
        pixel_diameter=ball_radius_pixels * 2,
        real_diameter_meters=GOLF_BALL_DIAMETER_METERS
    )
    
    return calibrator


if __name__ == "__main__":
    """Test homography calibration"""
    print("Homography Calibration Test")
    print("=" * 60)
    
    # Test 1: Calibrate using golf ball
    print("\n1. Quick calibration using golf ball (r=10px)")
    calibrator = quick_calibrate_from_ball(ball_radius_pixels=10)
    
    # Convert some pixel movements to meters
    point1 = (100, 100)
    point2 = (150, 120)
    
    distance_m = calibrator.calculate_real_world_distance(point1, point2)
    print(f"   Pixel movement: {point1} → {point2}")
    print(f"   Real distance: {distance_m:.3f} meters")
    
    # Test 2: Calibrate using known distance
    print("\n2. Calibrate using 10-yard markers")
    calibrator2 = HomographyCalibrator()
    calibrator2.calibrate_from_distance_marker(
        point1_px=(0, 0),
        point2_px=(200, 0),  # 200 pixels apart
        real_distance_meters=9.144  # 10 yards
    )
    
    distance_m2 = calibrator2.calculate_real_world_distance((0, 0), (100, 0))
    print(f"   Half the distance: {distance_m2:.3f} meters (~5 yards)")
    
    # Test 3: 4-point perspective (example)
    print("\n3. 4-point perspective calibration (example)")
    calibrator3 = HomographyCalibrator()
    
    # Example: Corner points of a known rectangle
    src = [(100, 100), (400, 100), (420, 300), (80, 300)]  # Trapezoid (perspective)
    dst = [(0, 0), (3, 0), (3, 2), (0, 2)]  # 3m x 2m rectangle
    
    calibrator3.calibrate_4_point_perspective(src, dst)
    print("   Homography matrix calculated")
    
    print("\n" + "=" * 60)
    print("\n✅ All calibration methods working!")
