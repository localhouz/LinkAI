"""
ML-Based Ball Detector using OpenCV DNN (MobileNet-SSD).

Detects 'sports ball' class (ID 37) in images.
Uses frozen TensorFlow graph to avoid installing tensorflow package.
"""

import cv2
import numpy as np
import os

class MLBallDetector:
    def __init__(self, model_path="models/frozen_inference_graph.pb", config_path="models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt", threshold=0.3):
        """
        Initialize OpenCV DNN detector.
        
        Args:
            model_path: Path to frozen graph .pb file
            config_path: Path to .pbtxt config file (optional)
            threshold: Confidence threshold for detection
        """
        self.threshold = threshold
        self.net = None
        
        # Check if model exists
        if not os.path.exists(model_path):
            print(f"ML Model not found at {model_path}")
            # Fallback to TFLite if that's what we have (but we can't run it without TF)
            return

        try:
            # Load model
            if os.path.exists(config_path):
                self.net = cv2.dnn.readNetFromTensorflow(model_path, config_path)
            else:
                self.net = cv2.dnn.readNetFromTensorflow(model_path)
                
            print(f"MLBallDetector initialized using OpenCV DNN.")
            
        except Exception as e:
            print(f"Failed to load ML model: {e}")
            self.net = None

    def detect_ball(self, frame):
        """
        Detect ball in frame.
        
        Returns:
            (center, radius) tuple or (None, 0)
        """
        if self.net is None:
            return None, 0

        frame_height, frame_width = frame.shape[:2]
        
        # Create blob from image
        # MobileNet-SSD expects 300x300 input, mean subtraction (127.5, 127.5, 127.5) and scale factor 1/127.5
        blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
        
        # Set input
        self.net.setInput(blob)
        
        # Run inference
        detections = self.net.forward()
        
        # detections shape: [1, 1, N, 7]
        # [batch_id, class_id, confidence, left, top, right, bottom]
        
        best_score = 0
        best_box = None
        
        # 'sports ball' is class ID 37 in COCO (1-indexed for SSD usually, so might be 37 or 38)
        # In OpenCV DNN with this model, classes are usually 1-indexed.
        # 1: person, ..., 37: sports ball
        TARGET_CLASS_ID = 37
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.threshold:
                class_id = int(detections[0, 0, i, 1])
                
                if class_id == TARGET_CLASS_ID:
                    if confidence > best_score:
                        best_score = confidence
                        box = detections[0, 0, i, 3:7] * np.array([frame_width, frame_height, frame_width, frame_height])
                        best_box = box.astype("int")
        
        if best_box is not None:
            (startX, startY, endX, endY) = best_box
            
            center_x = int((startX + endX) / 2)
            center_y = int((startY + endY) / 2)
            
            # Approximate radius
            radius = int(max(endX - startX, endY - startY) / 2)
            
            print(f"ML Detection: Ball found at ({center_x}, {center_y}) r={radius}, score={best_score:.2f}")
            return (center_x, center_y), radius

        return None, 0
