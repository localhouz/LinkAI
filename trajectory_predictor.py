"""
Trajectory Prediction Module
Uses kinematic physics equations to predict ball flight and landing location
"""

import math
import numpy as np
from config import GRAVITY, PIXELS_PER_METER


class TrajectoryPredictor:
    """Calculates ball trajectory using kinematic equations"""

    def __init__(self, fps, pixels_per_meter=PIXELS_PER_METER):
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        self.gravity = GRAVITY

    def estimate_initial_velocity(self, positions):
        """
        Estimates initial velocity and launch angle from tracked positions

        Uses kinematic equations:
        vx(t) = vx0 + ax(t)
        x(t) = x0 + vx0(t) + 1/2*ax(t^2)

        Args:
            positions: List of tuples (x, y, t) where x,y are pixel coords and t is time

        Returns:
            tuple: ((vx, vy), angle_deg, speed)
                vx, vy: velocity components in pixels/sec
                angle_deg: launch angle in degrees
                speed: total velocity magnitude in pixels/sec
        """
        if len(positions) < 2:
            return (0, 0), 0, 0

        # Get first and last positions
        x0, y0, t0 = positions[0]
        x1, y1, t1 = positions[-1]

        # Calculate displacement
        dx = x1 - x0
        dy = y1 - y0
        dt = t1 - t0

        # Avoid division by zero
        if dt == 0:
            return (0, 0), 0, 0

        # Calculate velocity components (pixels/frame → pixels/sec)
        vx = (dx / dt)  # Horizontal velocity
        vy = (dy / dt)  # Vertical velocity (negative is up in screen coordinates)

        # Calculate total speed
        speed = math.hypot(vx, vy)

        # Calculate launch angle (negative vy because screen y increases downward)
        angle_rad = math.atan2(-vy, vx)
        angle_deg = math.degrees(angle_rad)

        return (vx, vy), angle_deg, speed

    def predict_range(self, speed, angle_deg):
        """
        Predicts projectile range using kinematic equation:
        Range = (v^2 * sin(2θ)) / g

        Args:
            speed: Initial velocity magnitude (pixels/sec)
            angle_deg: Launch angle in degrees

        Returns:
            float: Predicted range in pixels
        """
        if speed == 0:
            return 0

        angle_rad = math.radians(angle_deg)

        # Simple projectile motion range (no air resistance)
        range_pixels = (speed ** 2 * math.sin(2 * angle_rad)) / self.gravity

        return range_pixels

    def calculate_trajectory(self, x0, y0, vx, vy, num_points=60):
        """
        Calculates full trajectory path using kinematic equations:
        x(t) = x0 + vx*t
        y(t) = y0 + vy*t + (1/2)*g*t^2

        Args:
            x0, y0: Starting position in pixels
            vx, vy: Initial velocity components (pixels/sec)
            num_points: Number of points to generate

        Returns:
            tuple: (xs, ys) arrays of trajectory coordinates
        """
        # Calculate flight time (when ball returns to ground level)
        # Using: y = y0 + vy*t + 0.5*g*t^2, solve for t when y = y0
        if vy == 0:
            flight_time = 0
        else:
            flight_time = abs(2 * vy / self.gravity)

        # Generate time points
        times = np.linspace(0, flight_time, num=num_points)

        # Calculate positions at each time
        xs = x0 + vx * times
        ys = y0 + vy * times + 0.5 * self.gravity * times**2

        return xs, ys

    def pixel_to_meter(self, pixel_distance):
        """
        Converts pixel distance to meters
        Note: Requires proper camera calibration for accuracy

        Args:
            pixel_distance: Distance in pixels

        Returns:
            float: Distance in meters
        """
        return pixel_distance / self.pixels_per_meter

    def get_landing_zone(self, x0, y0, vx, vy, uncertainty_radius=20):
        """
        Calculates predicted landing zone with uncertainty

        Args:
            x0, y0: Starting position
            vx, vy: Initial velocity
            uncertainty_radius: Radius of uncertainty in pixels

        Returns:
            dict: Landing zone info with center and radius
        """
        # Calculate landing position
        if vy == 0:
            landing_x = x0
            landing_y = y0
        else:
            flight_time = abs(2 * vy / self.gravity)
            landing_x = x0 + vx * flight_time
            landing_y = y0 + vy * flight_time + 0.5 * self.gravity * flight_time**2

        return {
            'center': (int(landing_x), int(landing_y)),
            'radius': uncertainty_radius,
            'distance_pixels': math.hypot(landing_x - x0, landing_y - y0),
            'distance_meters': self.pixel_to_meter(math.hypot(landing_x - x0, landing_y - y0))
        }
