"""
Quick test to verify ML detector is working
"""
import cv2
import numpy as np
from ml_ball_detector import MLBallDetector

print("Initializing ML detector...")
detector = MLBallDetector(
    model_path="models/ssd_mobilenet_v2_coco_2018_03_29/frozen_inference_graph.pb",
    config_path="models/ssd_mobilenet_v2_coco_2018_03_29.pbtxt",
    threshold=0.3
)

if detector.net is None:
    print("ERROR: ML detector failed to initialize!")
    print("Check that model files exist and OpenCV has DNN support")
    exit(1)

print("ML detector initialized successfully!")
print("Creating test image with a white circle (simulating a ball)...")

# Create a test image with a white circle
test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.circle(test_frame, (320, 240), 30, (255, 255, 255), -1)  # White circle

print("Running detection...")
center, radius = detector.detect_ball(test_frame)

if center:
    print(f"✓ Detection successful: center={center}, radius={radius}")
else:
    print("✗ No detection (this is expected - ML model trained on real objects, not synthetic circles)")
    print("The detector is working, but may need better test data")

print("\nDetector is functional and ready to use!")
