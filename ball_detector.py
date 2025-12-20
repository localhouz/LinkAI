"""
Ball Detection Module
Simplified: detect any circular object (any color) and report the first hit.
"""

import cv2
import numpy as np
from config import MIN_BALL_RADIUS


class BallDetector:
    """Detects circular objects in a frame using geometry only (color-agnostic)."""

    def __init__(self, use_preprocessing=True, param1=45, param2=18, min_radius=2, max_radius=60):
        """
        Initialize ball detector with configurable parameters.
        
        Args:
            use_preprocessing: Enable advanced preprocessing pipeline
            param1: Canny edge threshold (higher = stricter edge detection)
            param2: Hough accumulator threshold (lower = more sensitive)
            min_radius: Minimum ball radius in pixels
            max_radius: Maximum ball radius in pixels
        """
        self.use_preprocessing = use_preprocessing
        self.min_radius = max(1, min(min_radius, 100))  # Validate 1-100
        self.max_radius = max(self.min_radius + 1, min(max_radius, 200))  # Validate
        self.param1 = max(10, min(param1, 200))  # Validate 10-200
        self.param2 = max(5, min(param2, 100))   # Validate 5-100
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Log configuration
        print(f"BallDetector initialized: param1={self.param1}, param2={self.param2}, "
              f"radius={self.min_radius}-{self.max_radius}, preprocessing={use_preprocessing}")
    
    def preprocess(self, frame):
        """
        Apply advanced preprocessing for robust detection.
        
        Args:
            frame: BGR image
            
        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if not self.use_preprocessing:
            return cv2.GaussianBlur(gray, (7, 7), 1.5)
        
        # Apply CLAHE to improve contrast in varying lighting
        gray = self.clahe.apply(gray)
        
        # Bilateral filter: edge-preserving noise reduction
        # Keeps edges sharp while smoothing flat regions
        gray = cv2.bilateralFilter(gray, d=5, sigmaColor=75, sigmaSpace=75)
        
        # Gaussian blur to reduce high-frequency noise
        gray = cv2.GaussianBlur(gray, (5, 5), 1.0)
        
        return gray
    
    def calculate_confidence(self, frame, center, radius):
        """
        Calculate confidence score for a detected circle.
        
        Args:
            frame: Original BGR frame
            center: (x, y) center of circle
            radius: Circle radius
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        x, y = center
        r = int(radius)
        
        # Check if circle is fully in frame
        if y - r < 0 or y + r >= frame.shape[0] or x - r < 0 or x + r >= frame.shape[1]:
            return 0.0
        
        # Extract ROI
        roi = frame[y-r:y+r, x-r:x+r]
        if roi.size == 0:
            return 0.0
        
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Factor 1: Circularity (how round is the detection?)
        # Use contours to measure actual circularity
        _, thresh = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        circularity = 0.0
        if contours:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            perimeter = cv2.arcLength(c, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)  # Perfect circle = 1.0
                circularity = min(circularity, 1.0)
        
        # Factor 2: Contrast (edge strength)
        edges = cv2.Canny(gray_roi, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        contrast_score = min(edge_density * 5, 1.0)  # Scale to 0-1
        
        # Factor 3: Size appropriateness (prefer medium-sized circles)
        size_score = 1.0
        if r < 5:
            size_score = 0.3  # Too small, likely noise
        elif r < 10:
            size_score = 0.7  # Small but possible
        elif r > 50:
            size_score = 0.5  # Very large, might be something else
        
        # Weighted combination
        confidence = (
            circularity * 0.5 +      # 50% weight on shape
            contrast_score * 0.3 +   # 30% weight on edges
            size_score * 0.2         # 20% weight on size
        )
        
        return confidence

    def detect_ball(self, frame, return_all=False):
        """
        Detect ball using Hough Circle Transform with confidence scoring.
        
        Args:
            frame: BGR image
            return_all: If True, return all detections with confidence scores
            
        Returns:
            If return_all=False: (center, radius) or (None, 0)
            If return_all=True: List of (center, radius, confidence) tuples
        """
        # Preprocess frame
        gray = self.preprocess(frame)

        # Primary detection with configured parameters
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=20,
            param1=self.param1,
            param2=self.param2,
            minRadius=self.min_radius,
            maxRadius=self.max_radius,
        )

        detections = []
        
        if circles is not None:
            for (x, y, r) in np.round(circles[0, :]).astype("int"):
                if r < self.min_radius:
                    continue
                    
                # Calculate confidence
                confidence = self.calculate_confidence(frame, (int(x), int(y)), r)
                detections.append(((int(x), int(y)), int(r), confidence))
        
        # If no good detections, try backup method with relaxed parameters
        if len(detections) == 0 or (detections and max(d[2] for d in detections) < 0.3):
            backup_circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=15,
                param1=self.param1 - 10,  # More lenient
                param2=self.param2 - 5,   # More sensitive
                minRadius=self.min_radius,
                maxRadius=self.max_radius,
            )
            
            if backup_circles is not None:
                for (x, y, r) in np.round(backup_circles[0, :]).astype("int"):
                    if r < self.min_radius:
                        continue
                    confidence = self.calculate_confidence(frame, (int(x), int(y)), r)
                    # Only add if not already detected
                    if not any(abs(d[0][0] - x) < 10 and abs(d[0][1] - y) < 10 for d in detections):
                        detections.append(((int(x), int(y)), int(r), confidence * 0.8))  # Penalize backup
        
        if return_all:
            # Sort by confidence, return all
            detections.sort(key=lambda d: d[2], reverse=True)
            return detections
        
        # Return best detection above confidence threshold
        if detections:
            detections.sort(key=lambda d: d[2], reverse=True)
            best = detections[0]
            
            # Require minimum confidence of 0.2
            if best[2] >= 0.2:
                center, radius, confidence = best
                print(f"Circle found at {center} radius {radius} (confidence: {confidence:.2f})")
                return center, radius
        
        return None, 0

    def draw_ball(self, frame, center, radius):
        """Draw a circle on the frame (useful for debug images)."""
        if center is not None:
            cv2.circle(frame, center, radius, (0, 255, 0), 2)
            cv2.circle(frame, center, 3, (0, 0, 255), -1)
        return frame
