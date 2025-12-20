"""
Live Ball Tracer (Mobile-Ready Architecture)
Designed for easy porting to iOS/Android/React Native
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from collections import deque
from ball_detector import BallDetector
from trajectory_predictor import TrajectoryPredictor
import time


class LiveBallTracer:
    """
    Real-time ball tracer with mobile-ready architecture

    Design principles:
    - Modular: Each function maps to mobile equivalent
    - Stateful: Maintains tracking state between frames
    - Async-ready: Can be ported to async mobile pipelines
    - Optimized: Fast enough for real-time (30+ FPS)
    """

    def __init__(self, fps: float = 30, max_trail_length: int = 60, process_every_n_frames: int = 1):
        self.fps = fps
        self.max_trail_length = max_trail_length
        self.process_every_n_frames = process_every_n_frames  # Skip frames for performance
        self.frame_skip_counter = 0

        # Core modules
        self.detector = BallDetector()
        self.predictor = TrajectoryPredictor(fps)

        # Tracking state
        self.ball_trail = deque(maxlen=max_trail_length)  # Last N ball positions
        self.is_tracking = False
        self.shot_start_time = None
        self.trajectory_calculated = False

        # Trajectory data (calculated once ball stops or goes off screen)
        self.predicted_trajectory = []
        self.initial_velocity = None
        self.launch_angle = None
        self.shot_stats = {}

        # Visual settings
        self.trace_color = (0, 255, 255)  # Cyan
        self.trace_thickness = 3
        self.show_predicted_path = True

        # Performance metrics
        self.frame_times = deque(maxlen=30)

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Processes a single frame (MAIN FUNCTION FOR MOBILE)

        This is the key function that gets called for every camera frame.
        In mobile: Called from camera callback (AVCaptureSession/Camera2)

        Args:
            frame: BGR image from camera

        Returns:
            (annotated_frame, tracking_info)
        """
        start_time = time.time()

        # Frame skipping for performance
        self.frame_skip_counter += 1
        should_detect = (self.frame_skip_counter % self.process_every_n_frames == 0)

        # Step 1: Detect ball in current frame (only every Nth frame)
        ball_center, ball_radius = None, 0
        if should_detect:
            ball_center, ball_radius = self.detector.detect_ball(frame)

        # Step 2: Update tracking state
        if ball_center:
            self._update_tracking_state(ball_center, time.time())
        else:
            self._handle_ball_lost()

        # Step 3: Calculate trajectory if we have enough data
        if len(self.ball_trail) >= 5 and not self.trajectory_calculated:
            self._calculate_trajectory()

        # Step 4: Draw overlay on frame
        annotated_frame = self._draw_overlay(frame.copy())

        # Step 5: Calculate performance metrics
        process_time = (time.time() - start_time) * 1000  # ms
        self.frame_times.append(process_time)

        # Step 6: Return frame and tracking info
        tracking_info = self._get_tracking_info(process_time)

        return annotated_frame, tracking_info

    def _update_tracking_state(self, ball_center: Tuple[int, int], timestamp: float):
        """
        Updates tracking state with new ball position

        Mobile equivalent:
        - iOS: Update @State variables, publish to Combine
        - Android: Update LiveData/StateFlow
        - React Native: setState()
        """
        if not self.is_tracking:
            self.is_tracking = True
            self.shot_start_time = timestamp
            print("🏌️ Shot detected - Tracking started")

        self.ball_trail.append({
            'position': ball_center,
            'timestamp': timestamp
        })

    def _handle_ball_lost(self):
        """
        Handles when ball is not detected (out of frame or landed)

        Mobile: Trigger shot completion callbacks
        """
        if self.is_tracking and len(self.ball_trail) > 10:
            # Ball was tracking and now lost - probably landed
            if not self.trajectory_calculated:
                self._calculate_trajectory()

            # Could trigger "shot complete" event here
            # Mobile: Call completion handler, save to database, etc.

    def _calculate_trajectory(self):
        """
        Calculates full trajectory from tracked positions

        Mobile: Run on background thread to avoid blocking UI
        iOS: DispatchQueue.global()
        Android: Coroutines/WorkManager
        React Native: Web Worker
        """
        if len(self.ball_trail) < 5:
            return

        # Get first N positions for calculation
        positions = [
            (p['position'][0], p['position'][1],
             p['timestamp'] - self.shot_start_time)
            for p in list(self.ball_trail)[:min(10, len(self.ball_trail))]
        ]

        # Calculate physics
        (vx, vy), angle, speed = self.predictor.estimate_initial_velocity(positions)

        # Store results
        self.initial_velocity = (vx, vy)
        self.launch_angle = angle

        # Generate predicted trajectory
        x0, y0 = self.ball_trail[0]['position']
        traj_x, traj_y = self.predictor.calculate_trajectory(x0, y0, vx, vy)

        self.predicted_trajectory = list(zip(traj_x, traj_y))
        self.trajectory_calculated = True

        # Calculate stats
        self.shot_stats = {
            'speed_px_per_sec': speed,
            'launch_angle_deg': angle,
            'max_height': max(abs(y - y0) for _, y in self.predicted_trajectory),
            'total_distance': abs(self.predicted_trajectory[-1][0] - x0)
        }

        print(f"📊 Trajectory calculated: {speed:.0f} px/s @ {angle:.1f}°")

    def _draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Draws trace overlay on frame

        Mobile equivalent:
        - iOS: CAShapeLayer overlays, or SceneKit/Metal rendering
        - Android: Canvas drawing, or OpenGL overlays
        - React Native: SVG/Canvas overlays
        """
        if not self.is_tracking or len(self.ball_trail) == 0:
            return frame

        # Draw ball trail (actual path)
        trail_points = [p['position'] for p in self.ball_trail]

        if len(trail_points) > 1:
            # Draw trail with gradient (newer = brighter)
            for i in range(1, len(trail_points)):
                alpha = i / len(trail_points)
                thickness = int(self.trace_thickness * (0.5 + 0.5 * alpha))

                cv2.line(frame, trail_points[i-1], trail_points[i],
                        self.trace_color, thickness)

            # Draw current ball position with glow
            current_pos = trail_points[-1]
            cv2.circle(frame, current_pos, 12, (255, 255, 255), -1)  # White glow
            cv2.circle(frame, current_pos, 8, self.trace_color, -1)  # Cyan center
            cv2.circle(frame, current_pos, 8, (255, 255, 255), 2)  # White border

        # Draw predicted trajectory (if calculated)
        if self.show_predicted_path and self.trajectory_calculated:
            # Dotted line for prediction
            last_actual = trail_points[-1] if trail_points else (0, 0)

            # Find where predicted trajectory continues from actual
            start_idx = len(trail_points)
            if start_idx < len(self.predicted_trajectory):
                pred_points = [(int(x), int(y))
                              for x, y in self.predicted_trajectory[start_idx:]]

                # Draw dotted line
                for i in range(0, len(pred_points), 8):
                    if i < len(pred_points) - 1:
                        cv2.line(frame, pred_points[i], pred_points[i+1],
                                (200, 200, 200), 2)

        # Draw stats overlay
        self._draw_stats_overlay(frame)

        return frame

    def _draw_stats_overlay(self, frame: np.ndarray):
        """
        Draws real-time stats overlay

        Mobile: Use native UI labels (UILabel, TextView, Text component)
        Better UX than drawing on camera frame
        """
        height, width = frame.shape[:2]

        # Top-right stats panel
        if self.trajectory_calculated:
            stats = [
                f"Speed: {self.shot_stats['speed_px_per_sec']:.0f} px/s",
                f"Angle: {self.shot_stats['launch_angle_deg']:.1f}°",
                f"Distance: {self.shot_stats['total_distance']:.0f} px"
            ]

            y_offset = 30
            for stat in stats:
                # Black background
                (text_width, text_height), _ = cv2.getTextSize(
                    stat, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(frame,
                            (width - text_width - 30, y_offset - 20),
                            (width - 10, y_offset + 5),
                            (0, 0, 0), -1)

                # White text
                cv2.putText(frame, stat,
                          (width - text_width - 20, y_offset),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                y_offset += 35

        # FPS indicator (bottom-right)
        if self.frame_times:
            avg_time = np.mean(self.frame_times)
            current_fps = 1000 / avg_time if avg_time > 0 else 0

            fps_text = f"FPS: {current_fps:.1f}"
            cv2.putText(frame, fps_text, (width - 120, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def _get_tracking_info(self, process_time: float) -> Dict:
        """
        Returns current tracking state as dictionary

        Mobile: Return this to UI layer for display/logging
        """
        return {
            'is_tracking': self.is_tracking,
            'ball_count': len(self.ball_trail),
            'trajectory_ready': self.trajectory_calculated,
            'process_time_ms': process_time,
            'stats': self.shot_stats if self.trajectory_calculated else None
        }

    def reset(self):
        """
        Resets tracking state for next shot

        Mobile: Call this when user taps "New Shot" button
        """
        self.ball_trail.clear()
        self.is_tracking = False
        self.shot_start_time = None
        self.trajectory_calculated = False
        self.predicted_trajectory = []
        self.shot_stats = {}
        print("🔄 Tracking reset")

    def save_shot_data(self) -> Dict:
        """
        Returns complete shot data for saving to database

        Mobile: Save this to CoreData/Room/SQLite
        """
        if not self.trajectory_calculated:
            return {'error': 'No complete shot data'}

        return {
            'timestamp': self.shot_start_time,
            'ball_positions': [
                {'x': p['position'][0], 'y': p['position'][1], 't': p['timestamp']}
                for p in self.ball_trail
            ],
            'trajectory': [{'x': x, 'y': y} for x, y in self.predicted_trajectory],
            'stats': self.shot_stats
        }


def run_live_demo_from_webcam():
    """
    Desktop demo using webcam (for testing)
    Shows how it would work in real-time
    """
    print("="*60)
    print("LIVE BALL TRACER - WEBCAM DEMO")
    print("="*60)
    print("\nThis simulates mobile camera behavior")
    print("Point camera at a white object and move it")
    print("Press 'r' to reset, 'q' to quit\n")

    tracer = LiveBallTracer()
    cap = cv2.VideoCapture(0)  # Webcam

    if not cap.isOpened():
        print("❌ Could not open webcam")
        return

    print("✅ Webcam active - Move a white object to test tracking\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # MAIN CALL: This is what happens every frame on mobile
        annotated_frame, tracking_info = tracer.process_frame(frame)

        # Display
        cv2.imshow('Live Ball Tracer (Mobile Demo)', annotated_frame)

        # Keyboard controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            tracer.reset()

    cap.release()
    cv2.destroyAllWindows()


def run_live_demo_from_video(video_path: str, speed_multiplier: float = 1.0, skip_frames: int = 2):
    """
    Desktop demo using video file (simulates real-time)
    Processes video as if it were live camera feed

    Args:
        video_path: Path to video file
        speed_multiplier: Playback speed (1.0 = normal, 2.0 = 2x, 0.5 = half speed)
        skip_frames: Process every Nth frame (2 = every other frame for 2x speed)
    """
    print("="*60)
    print("LIVE BALL TRACER - VIDEO DEMO")
    print("="*60)
    print(f"\nProcessing: {video_path}")
    print(f"Speed: {speed_multiplier}x (processing every {skip_frames} frame(s))")
    print("\nControls:")
    print("  SPACE - Pause/Resume")
    print("  R - Reset tracking")
    print("  Q or ESC - Quit")
    print("="*60 + "\n")

    tracer = LiveBallTracer(process_every_n_frames=skip_frames)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Could not open video: {video_path}")
        return

    frame_count = 0
    paused = False

    # Calculate wait time based on video FPS and speed multiplier
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    wait_time = max(1, int((1000 / video_fps) / speed_multiplier))

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("\n✅ Video finished")
                break

            frame_count += 1

            # MAIN CALL: Process frame (same as mobile)
            annotated_frame, tracking_info = tracer.process_frame(frame)

            # Print tracking updates
            if tracking_info['is_tracking'] and frame_count % 30 == 0:
                print(f"Frame {frame_count}: Tracking - "
                      f"{tracking_info['ball_count']} positions, "
                      f"{tracking_info['process_time_ms']:.1f}ms/frame, "
                      f"FPS: {1000/tracking_info['process_time_ms']:.1f}")
        else:
            # If paused, just show last frame
            pass

        # Display
        cv2.imshow('Live Ball Tracer (SPACE=pause, R=reset, Q=quit)', annotated_frame)

        # Keyboard controls (with proper wait)
        key = cv2.waitKey(wait_time) & 0xFF

        if key == ord('q') or key == 27:  # Q or ESC
            print("\n👋 Quitting...")
            break
        elif key == ord('r'):  # R
            print("\n🔄 Resetting tracking...")
            tracer.reset()
        elif key == 32:  # SPACE
            paused = not paused
            print(f"\n{'⏸️  Paused' if paused else '▶️  Resumed'}")

    # Final shot data
    if tracer.trajectory_calculated:
        shot_data = tracer.save_shot_data()
        print("\n" + "="*60)
        print("SHOT COMPLETE")
        print("="*60)
        print(f"Ball positions tracked: {len(shot_data['ball_positions'])}")
        print(f"Stats: {shot_data['stats']}")

    cap.release()
    cv2.destroyAllWindows()


# Example usage
if __name__ == "__main__":
    import sys

    print("="*60)
    print("LIVE BALL TRACER")
    print("Mobile-Ready Architecture")
    print("="*60)

    if len(sys.argv) > 1:
        # Process video file
        video_path = sys.argv[1]

        # Optional: speed multiplier
        speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

        # Automatically set frame skip based on speed
        # 1x = process every 2nd frame, 2x = every 3rd, 0.5x = every frame
        skip_frames = max(1, int(2 * speed))

        run_live_demo_from_video(video_path, speed_multiplier=speed, skip_frames=skip_frames)
    else:
        # Use webcam
        print("\nNo video file provided")
        print("Usage: python live_tracer.py <video_file.mp4> [speed_multiplier]")
        print("Example: python live_tracer.py shot.mp4 2.0  (2x speed)")
        print("\nOr use webcam for live testing:\n")

        choice = input("Use webcam? (y/n): ").lower()
        if choice == 'y':
            run_live_demo_from_webcam()
        else:
            print("\nUsage examples:")
            print("  python live_tracer.py your_video.mp4")
            print("  python live_tracer.py your_video.mp4 2.0  (faster)")
            print("  python live_tracer.py your_video.mp4 0.5  (slower)")
