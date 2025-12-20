"""
ML-Based Ball Detector using TensorFlow Lite (MobileNet-SSD).

Detects 'sports ball' class (ID 37) in images using TFLite.
"""

import cv2
import numpy as np
import tensorflow as tf
import os

class MLBallDetectorTFLite:
    def __init__(self, model_path="models/detect.tflite", threshold=0.3):
        """
        Initialize TFLite interpreter.
        
        Args:
            model_path: Path to .tflite model file
            threshold: Confidence threshold for detection
        """
        self.threshold = threshold
        self.interpreter = None
        
        # Load TFLite model and allocate tensors
        try:
            if not os.path.exists(model_path):
                print(f"TFLite model not found at {model_path}")
                return
                
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            
            # Get input and output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            self.input_shape = self.input_details[0]['shape']
            self.input_height = self.input_shape[1]
            self.input_width = self.input_shape[2]
            
            print(f"MLBallDetectorTFLite initialized. Input shape: {self.input_shape}")
            print(f"Input dtype: {self.input_details[0]['dtype']}")
            
        except Exception as e:
            print(f"Failed to load TFLite model: {e}")
            import traceback
            traceback.print_exc()
            self.interpreter = None

    def detect_ball(self, frame):
        """
        Detect ball in frame.
        
        Returns:
            (center, radius) tuple or (None, 0)
        """
        if self.interpreter is None:
            return None, 0

        frame_height, frame_width = frame.shape[:2]
        
        # Resize frame to model input size (usually 300x300)
        input_data = cv2.resize(frame, (self.input_width, self.input_height))
        input_data = np.expand_dims(input_data, axis=0)
        
        # Normalize if required (uint8 models usually don't need it, float models do)
        if self.input_details[0]['dtype'] == np.float32:
            input_data = (np.float32(input_data) - 127.5) / 127.5
        else:
            input_data = np.uint8(input_data)

        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)

        # Run inference
        self.interpreter.invoke()

        # Get outputs
        # For COCO SSD MobileNet TFLite:
        # output_details[0] = boxes [1, 10, 4] (ymin, xmin, ymax, xmax) normalized 0-1
        # output_details[1] = classes [1, 10]
        # output_details[2] = scores [1, 10]
        # output_details[3] = num_detections [1]
        
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]
        
        # Find best "sports ball" detection
        best_score = 0
        best_box = None
        best_confidence = 0
        
        # 'sports ball' in COCO is class ID 37
        # In TFLite models, classes are 1-indexed (1=person, 2=bicycle, etc.)
        # So sports ball should be 37
        TARGET_CLASS_ID = 37.0 
        
        for i in range(len(scores)):
            score = scores[i]
            class_id = classes[i]
            
            # Debug: print all detections above a low threshold
            if score > 0.1:
                print(f"  Detection {i}: class={class_id}, score={score:.2f}")
            
            if score > self.threshold and class_id == TARGET_CLASS_ID:
                if score > best_score:
                    best_score = score
                    best_box = boxes[i]
                    best_confidence = score
        
        if best_box is not None:
            # Convert box (ymin, xmin, ymax, xmax) normalized 0-1 to pixel coordinates
            ymin, xmin, ymax, xmax = best_box
            
            # Scale to original frame size
            x1 = int(xmin * frame_width)
            y1 = int(ymin * frame_height)
            x2 = int(xmax * frame_width)
            y2 = int(ymax * frame_height)
            
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            
            # Approximate radius as half the max dimension
            radius = int(max(x2 - x1, y2 - y1) / 2)
            
            print(f"TFLite Detection: Ball found at ({center_x}, {center_y}) r={radius}, confidence={best_confidence:.2f}")
            return (center_x, center_y), radius

        return None, 0
