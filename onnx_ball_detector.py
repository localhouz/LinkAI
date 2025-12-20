"""
ML-Based Ball Detector using ONNX Runtime with YOLOv8
Works on Windows without DLL issues
"""

import cv2
import numpy as np
# import onnxruntime as ort  # Not needed yet

class ONNXBallDetector:
    def __init__(self, threshold=0.3):
        """
        Initialize ONNX detector with YOLOv8 nano model.
        
        For now, we'll use a simple circle detector as fallback.
        You can later add a proper ONNX model.
        """
        self.threshold = threshold
        print("ONNXBallDetector initialized (using Hough circles for now)")
        print("Note: For better accuracy, download a YOLOv8 ONNX model")
        
    def detect_ball(self, frame):
        """
        Detect ball using Hough Circle Transform.
        
        Returns:
            (center, radius) tuple or (None, 0)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Bilateral filter for noise reduction
        gray = cv2.bilateralFilter(gray, 5, 75, 75)
        gray = cv2.GaussianBlur(gray, (5, 5), 1.0)
        
        # Detect circles
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=20,
            param1=45,
            param2=18,
            minRadius=2,
            maxRadius=60,
        )
        
        if circles is None:
            return None, 0
        
        # Return the first valid circle
        for (x, y, r) in np.round(circles[0, :]).astype("int"):
            if r < 2:
                continue
            if y - r < 0 or y + r >= frame.shape[0] or x - r < 0 or x + r >= frame.shape[1]:
                continue
            print(f"Ball detected at ({x}, {y}) r={r}")
            return (int(x), int(y)), int(r)
        
        return None, 0
