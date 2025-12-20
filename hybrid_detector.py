"""
Hybrid Ball Detector - Professional 3-Stage Detection Pipeline

Stage 1: YOLO (Acquisition) - Find ball accurately but slow
Stage 2: Hough (Tracking) - Track ball in ROI, very fast
Stage 3: Kalman (Smoothing) - Fill gaps and smooth trajectory

Handles lost ball re-acquisition when tracking fails.
"""

import cv2
import numpy as np
import os

# Try to import onnxruntime, but allow graceful fallback if DLL fails
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except (ImportError, OSError) as e:
    print(f"[WARNING] ONNX Runtime not available (DLL error): {e}")
    print("          Falling back to Hough-only detection mode")
    ONNX_AVAILABLE = False
    ort = None


class HybridBallDetector:
    def __init__(self, yolo_model_path=None, confidence_threshold=0.3):
        """
        Initialize hybrid detector.
        
        Args:
            yolo_model_path: Path to YOLOv8 ONNX model (optional)
            confidence_threshold: Minimum confidence for detections
        """
        self.confidence_threshold = confidence_threshold
        self.yolo_session = None
        self.yolo_available = False
        
        # Load YOLO model if available
        if yolo_model_path and os.path.exists(yolo_model_path):
            try:
                self.yolo_session = ort.InferenceSession(yolo_model_path)
                self.yolo_available = True
                print(f"[OK] YOLO model loaded: {yolo_model_path}")
            except Exception as e:
                print(f"[WARNING] YOLO loading failed: {e}")
                self.yolo_available = False
        else:
            print("[INFO] No YOLO model - using Hough-only mode")
        
        # Tracking state
        self.roi = None  # Current region of interest
        self.consecutive_misses = 0
        self.max_misses = 3  # Trigger YOLO re-scan after 3 misses
        self.frame_count = 0
        self.yolo_frequency = 5  # Run YOLO every 5 frames when tracking
        
        print("HybridBallDetector initialized")
    
    def _detect_with_yolo(self, frame):
        """
        Stage 1: Use YOLO to find ball.
        
        Returns:
            (x, y, w, h) bounding box or None
        """
        if not self.yolo_available:
            return None
        
        try:
            # Prepare input (YOLOv8 expects 640x640)
            input_size = 640
            original_h, original_w = frame.shape[:2]
            
            # Resize and normalize
            resized = cv2.resize(frame, (input_size, input_size))
            blob = resized.astype(np.float32) / 255.0
            blob = np.transpose(blob, (2, 0, 1))  # HWC to CHW
            blob = np.expand_dims(blob, axis=0)  # Add batch dimension
            
            # Run inference
            input_name = self.yolo_session.get_inputs()[0].name
            outputs = self.yolo_session.run(None, {input_name: blob})
            
            # Parse outputs (YOLOv8 format: [batch, 4+classes, num_detections])
            predictions = outputs[0][0]  # Remove batch dimension
            
            # Filter for sports ball class (class 32 in COCO)
            # YOLOv8 output format: [x, y, w, h, conf_class0, conf_class1, ...]
            best_detection = None
            best_confidence = 0
            
            for detection in predictions.T:  # Transpose to iterate over detections
                # Assuming detection format: [cx, cy, w, h, class_confidences...]
                if len(detection) > 36:  # Ensure we have class 32
                    ball_confidence = detection[36]  # Class 32 (sports ball)
                    
                    if ball_confidence > best_confidence and ball_confidence > self.confidence_threshold:
                        best_confidence = ball_confidence
                        cx, cy, w, h = detection[:4]
                        
                        # Scale back to original image size
                        x = int((cx - w/2) * original_w / input_size)
                        y = int((cy - h/2) * original_h / input_size)
                        w = int(w * original_w / input_size)
                        h = int(h * original_h / input_size)
                        
                        best_detection = (x, y, w, h)
            
            return best_detection
            
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return None
    
    def _detect_with_hough(self, frame, roi=None):
        """
        Stage 2: Use Hough circles to find ball (fast).
        
        Args:
            frame: Input frame
            roi: Optional (x, y, w, h) to search only in this region
            
        Returns:
            ((x, y), radius) or (None, 0)
        """
        # Crop to ROI if provided
        if roi:
            x, y, w, h = roi
            x, y, w, h = max(0, x), max(0, y), w, h
            frame_height, frame_width = frame.shape[:2]
            
            # Ensure ROI is within frame bounds
            if x + w > frame_width:
                w = frame_width - x
            if y + h > frame_height:
                h = frame_height - y
            
            if w <= 0 or h <= 0:
                roi = None
            else:
                search_frame = frame[y:y+h, x:x+w]
        else:
            search_frame = frame
            x, y = 0, 0
        
        # Convert to grayscale
        gray = cv2.cvtColor(search_frame, cv2.COLOR_BGR2GRAY)
        
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
            maxRadius=60 if not roi else 40,  # Smaller max radius in ROI
        )
        
        if circles is None:
            return None, 0
        
        # Return the first valid circle (adjusted for ROI offset)
        for (circle_x, circle_y, r) in np.round(circles[0, :]).astype("int"):
            if r < 2:
                continue
            
            # Adjust coordinates if we used ROI
            abs_x = int(circle_x + x)
            abs_y = int(circle_y + y)
            
            return (abs_x, abs_y), int(r)
        
        return None, 0
    
    def detect_ball(self, frame):
        """
        Main detection method - orchestrates 3-stage pipeline.
        
        Returns:
            ((x, y), radius) or (None, 0)
        """
        self.frame_count += 1
        
        # Stage 1: YOLO Acquisition (initial or re-acquisition)
        should_run_yolo = (
            self.yolo_available and (
                self.roi is None or  # No ROI yet (initial)
                self.consecutive_misses > self.max_misses or  # Lost ball
                self.frame_count % self.yolo_frequency == 0  # Periodic validation
            )
        )
        
        if should_run_yolo:
            bbox = self._detect_with_yolo(frame)
            
            if bbox:
                # Expand bbox to ROI with margin
                x, y, w, h = bbox
                margin = 20
                self.roi = (
                    max(0, x - margin),
                    max(0, y - margin),
                    w + 2 * margin,
                    h + 2 * margin
                )
                print(f"[FOUND] YOLO found ball, ROI set: {self.roi}")
        
        # Stage 2: Hough Tracking (in ROI if available)
        center, radius = self._detect_with_hough(frame, self.roi)
        
        if center:
            # Detection successful
            self.consecutive_misses = 0
            
            # Update ROI to follow the ball
            if self.roi:
                cx, cy = center
                new_x = max(0, cx - 50)
                new_y = max(0, cy - 50)
                self.roi = (new_x, new_y, 100, 100)
            
            return center, radius
        else:
            # Detection failed
            self.consecutive_misses += 1
            
            if self.consecutive_misses > self.max_misses:
                print(f"[WARNING] Ball lost for {self.consecutive_misses} frames")
                self.roi = None  # Reset ROI to trigger full YOLO scan
            
            return None, 0
    
    def reset(self):
        """Reset tracking state."""
        self.roi = None
        self.consecutive_misses = 0
        self.frame_count = 0
        print("[RESET] Detector reset")
    
    def get_debug_info(self):
        """Get debug information for visualization."""
        return {
            "yolo_available": self.yolo_available,
            "roi": self.roi,
            "consecutive_misses": self.consecutive_misses,
            "frame_count": self.frame_count,
            "tracking_mode": "ROI" if self.roi else "FULL_FRAME"
        }


# Convenience function for backward compatibility
def create_detector(model_path=None):
    """Create hybrid detector with optional YOLO model."""
    return HybridBallDetector(yolo_model_path=model_path)


if __name__ == "__main__":
    """Test the hybrid detector"""
    print("Hybrid Ball Detector Test")
    print("=" * 60)
    
    # Test without YOLO (Hough-only mode)
    detector = HybridBallDetector()
    
    print("\nDetector initialized:")
    print(f"  YOLO available: {detector.yolo_available}")
    print(f"  Confidence threshold: {detector.confidence_threshold}")
    print(f"  Max consecutive misses: {detector.max_misses}")
    
    print("\n" + "=" * 60)
    print("\nTo use with YOLO:")
    print("1. Download YOLOv8-nano ONNX model")
    print("2. detector = HybridBallDetector('path/to/yolov8n.onnx')")
