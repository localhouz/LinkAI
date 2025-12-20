"""
Kalman Filter for 2D ball tracking with constant velocity model.

State vector: [x, y, vx, vy]
- x, y: position
- vx, vy: velocity

Measurement vector: [x, y]
- Only position is measured; velocity is inferred
"""

import numpy as np


class KalmanTracker:
    """
    2D Kalman filter for tracking ball position and velocity.
    
    Uses a constant velocity motion model with measurement of position only.
    """
    
    def __init__(self, process_noise=1.0, measurement_noise=10.0, dt=0.15):
        """
        Initialize Kalman filter.
        
        Args:
            process_noise: Process noise variance (motion uncertainty)
            measurement_noise: Measurement noise variance (detection uncertainty)
            dt: Time step between frames (seconds)
        """
        self.dt = dt
        
        # State: [x, y, vx, vy]
        self.x = None  # State vector (will be 4x1)
        
        # State covariance matrix (4x4)
        self.P = None
        
        # State transition matrix (constant velocity model)
        self.F = np.array([
            [1, 0, dt, 0],   # x = x + vx*dt
            [0, 1, 0, dt],   # y = y + vy*dt
            [0, 0, 1, 0],    # vx = vx
            [0, 0, 0, 1]     # vy = vy
        ])
        
        # Measurement matrix (we only measure position)
        self.H = np.array([
            [1, 0, 0, 0],    # measure x
            [0, 1, 0, 0]     # measure y
        ])
        
        # Process noise covariance (4x4)
        # Higher values = trust model less, trust measurements more
        q = process_noise
        self.Q = np.array([
            [q*dt**4/4, 0, q*dt**3/2, 0],
            [0, q*dt**4/4, 0, q*dt**3/2],
            [q*dt**3/2, 0, q*dt**2, 0],
            [0, q*dt**3/2, 0, q*dt**2]
        ])
        
        # Measurement noise covariance (2x2)
        # Higher values = trust measurements less, trust prediction more
        r = measurement_noise
        self.R = np.array([
            [r, 0],
            [0, r]
        ])
        
        self.is_initialized = False
        self.miss_count = 0
        self.max_misses = 6
    
    def predict(self):
        """
        Prediction step: estimate state at next time step.
        
        Returns:
            Predicted state [x, y, vx, vy]
        """
        if not self.is_initialized:
            return None
        
        # Predict state: x = F * x
        self.x = self.F @ self.x
        
        # Predict covariance: P = F * P * F^T + Q
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.x
    
    def update(self, measurement):
        """
        Update step: correct prediction with measurement.
        
        Args:
            measurement: (x, y) tuple or None if no detection
            
        Returns:
            Updated state dict with keys: x, y, vx, vy, r (radius from measurement)
            or None if tracker is lost
        """
        if measurement is None:
            # No detection
            self.miss_count += 1
            
            if self.miss_count >= self.max_misses:
                # Lost track
                self.is_initialized = False
                self.x = None
                self.P = None
                return None
            
            # Still predict even without measurement
            self.predict()
            
            if self.x is not None:
                return {
                    'x': float(self.x[0]),
                    'y': float(self.x[1]),
                    'vx': float(self.x[2]),
                    'vy': float(self.x[3]),
                    'r': 0,
                    'predicted': True
                }
            return None
        
        # Got a detection
        x_meas, y_meas, radius = measurement
        z = np.array([[x_meas], [y_meas]])
        
        if not self.is_initialized:
            # Initialize state with first measurement
            self.x = np.array([[x_meas], [y_meas], [0], [0]])  # zero velocity initially
            self.P = np.eye(4) * 100  # high initial uncertainty
            self.is_initialized = True
            self.miss_count = 0
            
            return {
                'x': float(x_meas),
                'y': float(y_meas),
                'vx': 0.0,
                'vy': 0.0,
                'r': float(radius),
                'predicted': False
            }
        
        # Prediction step
        self.predict()
        
        # Innovation: y = z - H * x
        y_innov = z - self.H @ self.x
        
        # Innovation covariance: S = H * P * H^T + R
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain: K = P * H^T * S^-1
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state: x = x + K * y
        self.x = self.x + K @ y_innov
        
        # Update covariance: P = (I - K * H) * P
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
        self.miss_count = 0
        
        return {
            'x': float(self.x[0]),
            'y': float(self.x[1]),
            'vx': float(self.x[2]),
            'vy': float(self.x[3]),
            'r': float(radius),
            'predicted': False
        }
    
    def get_velocity(self):
        """
        Get current velocity estimate.
        
        Returns:
            (vx, vy) tuple or (0, 0) if not initialized
        """
        if self.is_initialized and self.x is not None:
            return float(self.x[2]), float(self.x[3])
        return 0.0, 0.0
    
    def reset(self):
        """Reset the tracker to uninitialized state."""
        self.x = None
        self.P = None
        self.is_initialized = False
        self.miss_count = 0
