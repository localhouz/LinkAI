"""
Physics-based threshold calculations for golf ball tracking.

This module calculates realistic pixel displacement thresholds based on:
- Ball speed (putt vs chip vs drive)
- Frame rate (FPS)
- Camera field of view and resolution
"""

import math


class TrackingThresholds:
    """
    Calculate physics-based tracking thresholds for ball detection.
    """
    
    # Ball speed ranges (meters/second)
    PUTT_SPEED_MAX = 2.5      # Slow putting speed
    CHIP_SPEED_MAX = 10.0     # Chipping speed
    DRIVE_SPEED_MAX = 70.0    # Full driver swing (156 mph)
    
    def __init__(self, 
                 mode='putt',
                 fps=6.7,
                 frame_width=1280,
                 frame_height=720,
                 fov_degrees_horizontal=60):
        """
        Initialize threshold calculator.
        
        Args:
            mode: 'putt', 'chip', or 'drive'
            fps: Frames per second (detection rate)
            frame_width: Camera frame width in pixels
            frame_height: Camera frame height in pixels
            fov_degrees_horizontal: Camera horizontal field of view
        """
        self.mode = mode
        self.fps = fps
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fov_radians = math.radians(fov_degrees_horizontal)
        
        # Select max speed based on mode
        if mode == 'putt':
            self.max_speed_ms = self.PUTT_SPEED_MAX
        elif mode == 'chip':
            self.max_speed_ms = self.CHIP_SPEED_MAX
        elif mode == 'drive':
            self.max_speed_ms = self.DRIVE_SPEED_MAX
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def meters_to_pixels(self, distance_meters, depth_meters=3.0):
        """
        Convert real-world distance to pixel distance.
        
        Args:
            distance_meters: Distance in meters
            depth_meters: Distance from camera to ball (in meters)
            
        Returns:
            Distance in pixels
        """
        # Calculate meters per pixel at given depth
        # tan(FOV/2) = (width_real/2) / depth
        width_real_meters = 2 * depth_meters * math.tan(self.fov_radians / 2)
        meters_per_pixel = width_real_meters / self.frame_width
        
        return distance_meters / meters_per_pixel
    
    def get_max_displacement_px(self, depth_meters=3.0):
        """
        Calculate maximum realistic pixel displacement per frame.
        
        Args:
            depth_meters: Distance from camera to ball
            
        Returns:
            Maximum pixels the ball can travel in one frame
        """
        # Distance ball can travel in one frame
        time_per_frame = 1.0 / self.fps
        max_distance_meters = self.max_speed_ms * time_per_frame
        
        # Convert to pixels
        max_displacement_px = self.meters_to_pixels(max_distance_meters, depth_meters)
        
        # Add 20% safety margin for measurement uncertainty
        return int(max_displacement_px * 1.2)
    
    def get_stability_threshold_px(self, depth_meters=3.0):
        """
        Calculate stability threshold (ignore micro-movements).
        
        Movements smaller than this are considered jitter.
        
        Args:
            depth_meters: Distance from camera to ball
            
        Returns:
            Stability threshold in pixels
        """
        # Ignore movements smaller than 1cm
        jitter_meters = 0.01
        jitter_px = self.meters_to_pixels(jitter_meters, depth_meters)
        
        # At least 2 pixels to avoid rounding errors
        return max(2, int(jitter_px))
    
    def get_lock_params(self):
        """
        Get lock/drop parameters based on mode.
        
        Returns:
            dict with 'hits_to_lock' and 'misses_to_drop'
        """
        if self.mode == 'putt':
            # Putts are slow and predictable - lock quickly
            return {
                'hits_to_lock': 2,
                'misses_to_drop': 4
            }
        elif self.mode == 'chip':
            # Chips are faster - require more confirmation
            return {
                'hits_to_lock': 3,
                'misses_to_drop': 3
            }
        else:  # drive
            # Drives are very fast - need robust tracking
            return {
                'hits_to_lock': 4,
                'misses_to_drop': 2
            }
    
    def to_dict(self, depth_meters=3.0):
        """
        Get all thresholds as a dictionary.
        
        Args:
            depth_meters: Distance from camera to ball
            
        Returns:
            Dictionary with all calculated thresholds
        """
        lock_params = self.get_lock_params()
        
        return {
            'mode': self.mode,
            'max_speed_ms': self.max_speed_ms,
            'fps': self.fps,
            'depth_meters': depth_meters,
            'max_displacement_px': self.get_max_displacement_px(depth_meters),
            'stability_threshold_px': self.get_stability_threshold_px(depth_meters),
            'hits_to_lock': lock_params['hits_to_lock'],
            'misses_to_drop': lock_params['misses_to_drop'],
        }
    
    def __str__(self):
        """String representation showing calculated thresholds."""
        params = self.to_dict()
        return (
            f"TrackingThresholds(mode={params['mode']}, "
            f"max_disp={params['max_displacement_px']}px, "
            f"stability={params['stability_threshold_px']}px, "
            f"lock={params['hits_to_lock']}, drop={params['misses_to_drop']})"
        )


# Pre-calculated threshold sets for common scenarios
PUTT_THRESHOLDS = TrackingThresholds(mode='putt', fps=6.7, fov_degrees_horizontal=60)
CHIP_THRESHOLDS = TrackingThresholds(mode='chip', fps=6.7, fov_degrees_horizontal=60)
DRIVE_THRESHOLDS = TrackingThresholds(mode='drive', fps=6.7, fov_degrees_horizontal=60)


if __name__ == '__main__':
    # Demo: print calculated thresholds for different modes
    print("=" * 60)
    print("PHYSICS-BASED TRACKING THRESHOLDS")
    print("=" * 60)
    print()
    
    for mode_name, threshold_obj in [
        ('Putt', PUTT_THRESHOLDS),
        ('Chip', CHIP_THRESHOLDS),
        ('Drive', DRIVE_THRESHOLDS)
    ]:
        print(f"{mode_name} Mode:")
        params = threshold_obj.to_dict(depth_meters=3.0)
        for key, value in params.items():
            print(f"  {key}: {value}")
        print()
