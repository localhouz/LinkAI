"""
Golf Ball Finder - Main Application
Tracks golf ball flight and predicts landing location using computer vision and physics
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse
from ball_detector import BallDetector
from trajectory_predictor import TrajectoryPredictor
from config import (
    N_FRAMES_TO_ANALYZE,
    FRAME_SKIP,
    DEBUG_MODE,
    SHOW_VISUALIZATION,
    FPS
)


def main(video_path):
    """
    Main application loop

    Args:
        video_path: Path to golf shot video file
    """
    print("=" * 60)
    print("Golf Ball Finder - Prototype")
    print("=" * 60)
    print(f"Loading video: {video_path}\n")

    # Initialize modules
    detector = BallDetector()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"ERROR: Could not open video file: {video_path}")
        print("Make sure the file exists and is a valid video format.")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    predictor = TrajectoryPredictor(fps)

    print(f"Video FPS: {fps}")
    print(f"Analyzing first {N_FRAMES_TO_ANALYZE} frames with ball detection\n")

    # Storage for detected positions
    positions = []
    frame_count = 0

    # Phase 1: Detect and track ball
    print("Phase 1: Detecting ball...")
    while cap.isOpened() and len(positions) < N_FRAMES_TO_ANALYZE:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Skip frames if configured
        if frame_count % FRAME_SKIP != 0:
            continue

        # Detect ball in current frame
        center, radius = detector.detect_ball(frame)

        if center:
            timestamp = frame_count / fps
            positions.append((center[0], center[1], timestamp))
            print(f"  Frame {frame_count}: Ball detected at {center}, radius={radius}")

            # Draw ball on frame if in debug mode
            if DEBUG_MODE:
                frame = detector.draw_ball(frame, center, radius)

        # Show live detection
        if DEBUG_MODE:
            cv2.imshow("Golf Ball Detection", frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

    # Phase 2: Analyze trajectory
    print(f"\nPhase 2: Analyzing trajectory...")
    print(f"Detected ball in {len(positions)} frames\n")

    if len(positions) < 2:
        print("ERROR: Not enough ball positions detected to calculate trajectory.")
        print("Tips:")
        print("  - Make sure the ball is visible and white/light colored")
        print("  - Try adjusting LOWER_WHITE and UPPER_WHITE in config.py")
        print("  - Ensure good lighting and contrast in the video")
        return

    # Calculate initial velocity and trajectory
    (vx, vy), angle_deg, speed = predictor.estimate_initial_velocity(positions)

    print("=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Initial velocity:")
    print(f"  vx = {vx:.2f} pixels/sec")
    print(f"  vy = {vy:.2f} pixels/sec")
    print(f"  Speed = {speed:.2f} pixels/sec")
    print(f"\nLaunch angle: {angle_deg:.2f} degrees")

    # Predict range
    ball_range = predictor.predict_range(speed, angle_deg)
    print(f"\nPredicted range: {ball_range:.2f} pixels")

    # Get landing zone
    x0, y0, _ = positions[0]
    landing_zone = predictor.get_landing_zone(x0, y0, vx, vy)
    print(f"\nEstimated landing zone:")
    print(f"  Center: {landing_zone['center']}")
    print(f"  Distance: {landing_zone['distance_pixels']:.2f} pixels")
    print(f"  Distance: {landing_zone['distance_meters']:.2f} meters (needs calibration)")
    print("=" * 60)

    # Phase 3: Visualization
    if SHOW_VISUALIZATION:
        print("\nGenerating visualization...")
        visualize_trajectory(positions, predictor, x0, y0, vx, vy, landing_zone)


def visualize_trajectory(positions, predictor, x0, y0, vx, vy, landing_zone):
    """
    Creates a matplotlib visualization of the detected ball path and predicted trajectory

    Args:
        positions: List of detected (x, y, t) positions
        predictor: TrajectoryPredictor instance
        x0, y0: Starting position
        vx, vy: Initial velocity components
        landing_zone: Predicted landing zone dict
    """
    # Extract x and y coordinates from positions
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]

    # Calculate full predicted trajectory
    traj_xs, traj_ys = predictor.calculate_trajectory(x0, y0, vx, vy)

    # Create plot
    plt.figure(figsize=(12, 8))

    # Plot detected ball positions
    plt.plot(xs, ys, 'go-', linewidth=2, markersize=8, label='Detected Ball Path')

    # Plot predicted trajectory
    plt.plot(traj_xs, traj_ys, 'b--', linewidth=2, label='Predicted Trajectory')

    # Plot landing zone
    landing_circle = plt.Circle(
        landing_zone['center'],
        landing_zone['radius'],
        color='red',
        fill=False,
        linewidth=2,
        label='Landing Zone'
    )
    plt.gca().add_patch(landing_circle)
    plt.plot(landing_zone['center'][0], landing_zone['center'][1], 'rx', markersize=15, markeredgewidth=3)

    # Formatting
    plt.gca().invert_yaxis()  # Invert y-axis (image coordinates)
    plt.xlabel('X Position (pixels)', fontsize=12)
    plt.ylabel('Y Position (pixels)', fontsize=12)
    plt.title('Golf Ball Flight Analysis', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.axis('equal')

    print("Close the plot window to exit.")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Golf Ball Finder - Track and predict ball flight')
    parser.add_argument(
        '--video',
        type=str,
        default='golf_shot.mp4',
        help='Path to golf shot video file (default: golf_shot.mp4)'
    )
    args = parser.parse_args()

    main(args.video)
