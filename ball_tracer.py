"""
TopTracer-Style Ball Tracer
Overlays professional ball flight traces on golf shot videos
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from trajectory_predictor import TrajectoryPredictor
from ball_detector import BallDetector


class BallTracer:
    """
    Creates TopTracer-style video overlays with ball flight traces
    """

    def __init__(self, fps: float = 30):
        self.fps = fps
        self.detector = BallDetector()
        self.predictor = TrajectoryPredictor(fps)

        # Visualization settings
        self.trace_color = (0, 255, 255)  # Cyan (BGR format for OpenCV)
        self.trace_thickness = 3
        self.ball_marker_radius = 8
        self.show_distance = True
        self.show_speed = True
        self.show_apex = True

    def process_video_with_trace(self, input_video: str, output_video: str,
                                 trace_style: str = "toptracer") -> Dict:
        """
        Processes a golf shot video and adds professional ball trace overlay

        Args:
            input_video: Path to input video file
            output_video: Path to output video file
            trace_style: Style of trace ("toptracer", "shottracer", "simple")

        Returns:
            Dict with processing results and statistics
        """
        cap = cv2.VideoCapture(input_video)

        if not cap.isOpened():
            return {"error": f"Could not open video: {input_video}"}

        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or self.fps
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

        print(f"Processing video: {input_video}")
        print(f"Resolution: {width}x{height}, FPS: {fps}, Frames: {total_frames}")

        # Phase 1: Detect ball positions
        print("\nPhase 1: Detecting ball positions...")
        ball_positions = []
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            center, radius = self.detector.detect_ball(frame)

            if center:
                timestamp = frame_count / fps
                ball_positions.append({
                    'frame': frame_count,
                    'position': center,
                    'radius': radius,
                    'timestamp': timestamp
                })

            # Progress indicator
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"  Progress: {progress:.1f}% ({frame_count}/{total_frames} frames)", end='\r')

        print(f"\n  Detected ball in {len(ball_positions)} frames")

        if len(ball_positions) < 2:
            cap.release()
            out.release()
            return {"error": "Not enough ball positions detected"}

        # Phase 2: Calculate trajectory
        print("\nPhase 2: Calculating trajectory...")
        positions_for_calc = [
            (p['position'][0], p['position'][1], p['timestamp'])
            for p in ball_positions[:min(10, len(ball_positions))]
        ]

        (vx, vy), angle, speed = self.predictor.estimate_initial_velocity(positions_for_calc)

        # Generate smooth trajectory curve
        x0, y0 = ball_positions[0]['position']
        traj_x, traj_y = self.predictor.calculate_trajectory(x0, y0, vx, vy, num_points=100)

        trajectory_points = [(int(x), int(y)) for x, y in zip(traj_x, traj_y)
                            if 0 <= x < width and 0 <= y < height]

        print(f"  Initial velocity: {speed:.1f} px/s")
        print(f"  Launch angle: {angle:.1f}°")
        print(f"  Trajectory points: {len(trajectory_points)}")

        # Calculate ball stats
        max_height_idx = np.argmin(traj_y)  # Min Y because screen coords are inverted
        apex_height = abs(traj_y[max_height_idx] - y0)
        apex_distance = abs(traj_x[max_height_idx] - x0)
        total_distance = abs(trajectory_points[-1][0] - x0) if trajectory_points else 0

        # Phase 3: Create traced video
        print("\nPhase 3: Rendering video with trace...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Find if ball is visible in this frame
            current_ball = next((p for p in ball_positions if p['frame'] == frame_count), None)

            # Draw trace up to current ball position
            if current_ball and trace_style == "toptracer":
                frame = self._draw_toptracer_style(
                    frame, ball_positions, trajectory_points,
                    frame_count, speed, angle, total_distance
                )
            elif current_ball and trace_style == "shottracer":
                frame = self._draw_shottracer_style(
                    frame, ball_positions, trajectory_points,
                    frame_count, apex_height, total_distance
                )
            else:
                frame = self._draw_simple_trace(
                    frame, ball_positions, trajectory_points,
                    frame_count
                )

            out.write(frame)

            # Progress indicator
            if frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"  Progress: {progress:.1f}%", end='\r')

        print(f"\n✅ Video processing complete!")

        cap.release()
        out.release()

        return {
            'success': True,
            'output_file': output_video,
            'ball_detections': len(ball_positions),
            'initial_speed': speed,
            'launch_angle': angle,
            'apex_height_pixels': apex_height,
            'total_distance_pixels': total_distance
        }

    def _draw_toptracer_style(self, frame, ball_positions, trajectory,
                              current_frame, speed, angle, distance):
        """
        TopTracer-style overlay: Clean cyan line with animated ball marker
        """
        # Draw trajectory curve (fade effect - more opaque closer to ball)
        current_ball_idx = next((i for i, p in enumerate(ball_positions)
                               if p['frame'] == current_frame), None)

        if current_ball_idx is not None:
            # Draw traced path (where ball has been)
            traced_positions = [p['position'] for p in ball_positions[:current_ball_idx + 1]]

            if len(traced_positions) > 1:
                # Draw smooth curve through detected positions
                points = np.array(traced_positions, dtype=np.int32)

                # Draw thick line with glow effect
                cv2.polylines(frame, [points], False, (100, 100, 100), 5)  # Shadow
                cv2.polylines(frame, [points], False, self.trace_color, self.trace_thickness)

                # Draw current ball position with glow
                current_pos = traced_positions[-1]
                cv2.circle(frame, current_pos, self.ball_marker_radius + 3,
                          (255, 255, 255), -1)  # White glow
                cv2.circle(frame, current_pos, self.ball_marker_radius,
                          self.trace_color, -1)  # Cyan center
                cv2.circle(frame, current_pos, self.ball_marker_radius,
                          (255, 255, 255), 2)  # White border

                # Draw predicted path (dotted line)
                if current_ball_idx < len(ball_positions) - 1:
                    remaining_trajectory = [(int(x), int(y)) for x, y in
                                          zip(trajectory[current_ball_idx:],
                                              trajectory[current_ball_idx:])]
                    self._draw_dotted_line(frame, traced_positions[-1],
                                         trajectory[-1] if trajectory else traced_positions[-1],
                                         self.trace_color, 2)

        # Add info overlay (TopTracer style - bottom left)
        self._draw_info_panel(frame, speed, angle, distance)

        return frame

    def _draw_shottracer_style(self, frame, ball_positions, trajectory,
                               current_frame, apex, distance):
        """
        ShotTracer-style overlay: Thick gradient line with apex marker
        """
        current_ball_idx = next((i for i, p in enumerate(ball_positions)
                               if p['frame'] == current_frame), None)

        if current_ball_idx is not None and current_ball_idx > 0:
            traced_positions = [p['position'] for p in ball_positions[:current_ball_idx + 1]]

            # Draw gradient trail (orange to yellow)
            for i in range(1, len(traced_positions)):
                alpha = i / len(traced_positions)
                color = self._interpolate_color((0, 140, 255), (0, 255, 255), alpha)

                cv2.line(frame, traced_positions[i-1], traced_positions[i],
                        color, self.trace_thickness + 2)

            # Draw ball
            current_pos = traced_positions[-1]
            cv2.circle(frame, current_pos, self.ball_marker_radius, (255, 255, 255), -1)

        return frame

    def _draw_simple_trace(self, frame, ball_positions, trajectory, current_frame):
        """
        Simple trace: Just the line, no fancy effects
        """
        current_ball_idx = next((i for i, p in enumerate(ball_positions)
                               if p['frame'] == current_frame), None)

        if current_ball_idx is not None and current_ball_idx > 0:
            traced_positions = [p['position'] for p in ball_positions[:current_ball_idx + 1]]
            points = np.array(traced_positions, dtype=np.int32)
            cv2.polylines(frame, [points], False, self.trace_color, 2)

            # Draw ball
            cv2.circle(frame, traced_positions[-1], 5, (0, 255, 0), -1)

        return frame

    def _draw_info_panel(self, frame, speed, angle, distance):
        """
        Draws TopTracer-style info panel
        """
        height, width = frame.shape[:2]

        # Semi-transparent panel
        panel_height = 100
        panel_width = 300
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, height - panel_height - 10),
                     (panel_width, height - 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = height - panel_height + 20

        cv2.putText(frame, f"Speed: {speed:.0f} px/s", (20, y_offset),
                   font, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Angle: {angle:.1f} deg", (20, y_offset + 30),
                   font, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Distance: {distance:.0f} px", (20, y_offset + 60),
                   font, 0.6, (255, 255, 255), 2)

    def _draw_dotted_line(self, frame, pt1, pt2, color, thickness):
        """Draws a dotted line"""
        dist = np.linalg.norm(np.array(pt1) - np.array(pt2))
        num_dots = int(dist / 10)

        for i in range(num_dots):
            t = i / num_dots
            x = int(pt1[0] + t * (pt2[0] - pt1[0]))
            y = int(pt1[1] + t * (pt2[1] - pt1[1]))
            if i % 2 == 0:
                cv2.circle(frame, (x, y), thickness, color, -1)

    def _interpolate_color(self, color1, color2, alpha):
        """Interpolates between two colors"""
        return tuple(int(c1 + alpha * (c2 - c1)) for c1, c2 in zip(color1, color2))


# Example usage
if __name__ == "__main__":
    import argparse

    print("="*60)
    print("TOPTRACER-STYLE BALL TRACER")
    print("="*60)

    parser = argparse.ArgumentParser(description='Add professional ball traces to golf videos')
    parser.add_argument('--input', type=str, default='golf_shot.mp4',
                       help='Input video file')
    parser.add_argument('--output', type=str, default='traced_shot.mp4',
                       help='Output video file')
    parser.add_argument('--style', type=str, default='toptracer',
                       choices=['toptracer', 'shottracer', 'simple'],
                       help='Trace style')

    args = parser.parse_args()

    tracer = BallTracer()

    print(f"\nInput: {args.input}")
    print(f"Output: {args.output}")
    print(f"Style: {args.style}\n")

    result = tracer.process_video_with_trace(
        args.input,
        args.output,
        trace_style=args.style
    )

    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
    else:
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"✅ Traced video saved: {result['output_file']}")
        print(f"   Ball detections: {result['ball_detections']} frames")
        print(f"   Initial speed: {result['initial_speed']:.1f} px/s")
        print(f"   Launch angle: {result['launch_angle']:.1f}°")
        print(f"   Total distance: {result['total_distance_pixels']:.0f} pixels")
        print(f"{'='*60}")
        print("\nOpen the output video to see the trace!")
