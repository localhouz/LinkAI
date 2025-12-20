"""
AR Pin Finder
Real-time AR overlay showing detected pin position with visual markers

Combines:
- pin_detector.py for detection
- ar_ball_finder.py concepts for AR overlay
- Real-time camera view with pin visualization
"""

import cv2
import numpy as np
import math
from typing import Tuple, Optional, Dict
from pin_detector import PinDetector, PinPositionCalculator
from datetime import datetime


class ARPinFinder:
    """
    AR overlay for pin detection and guidance

    Features:
    - Real-time pin detection in camera view
    - Visual markers on detected pin
    - Distance and direction to pin
    - Confidence indicator
    - Hot/cold proximity feedback
    """

    def __init__(self):
        self.pin_detector = PinDetector()
        self.pin_calculator = PinPositionCalculator()

        # AR overlay settings
        self.show_detection_overlay = True
        self.show_distance_overlay = True
        self.show_confidence_meter = True

        # Colors (BGR format)
        self.color_pin_detected = (0, 255, 0)  # Green
        self.color_pin_uncertain = (0, 165, 255)  # Orange
        self.color_info_text = (255, 255, 255)  # White
        self.color_distance_ring = (0, 255, 255)  # Yellow

        # State
        self.last_pin_detection = None
        self.stable_pin_gps = None
        self.user_gps = None
        self.camera_bearing = 0

    def process_frame(self, frame: np.ndarray, user_gps: Tuple[float, float] = None,
                     camera_bearing: float = 0, distance_yards: float = None) -> Tuple[np.ndarray, Dict]:
        """
        Processes a camera frame with AR pin overlay

        Args:
            frame: Camera frame (BGR)
            user_gps: Current user position (lat, lon)
            camera_bearing: Camera compass direction (0-360)
            distance_yards: Distance to pin (if known from rangefinder)

        Returns:
            (annotated_frame, detection_info)
        """
        self.user_gps = user_gps
        self.camera_bearing = camera_bearing

        # Detect pin in frame
        pin_detection = self.pin_detector.detect_pin(frame, debug=False)

        # Create overlay
        overlay = frame.copy()
        info = {}

        if pin_detection:
            self.last_pin_detection = pin_detection

            # Draw pin marker
            self._draw_pin_marker(overlay, pin_detection)

            # Calculate pin GPS if we have user location
            if user_gps and distance_yards:
                pin_gps = self._calculate_pin_gps(
                    pin_detection, user_gps, camera_bearing,
                    frame.shape[1], distance_yards
                )
                self.stable_pin_gps = pin_gps
                info['pin_gps'] = pin_gps

            # Draw info panel
            self._draw_info_panel(overlay, pin_detection, distance_yards)

            # Draw confidence meter
            if self.show_confidence_meter:
                self._draw_confidence_meter(overlay, pin_detection['confidence'])

            info['detected'] = True
            info['confidence'] = pin_detection['confidence']
            info['flag_color'] = pin_detection['flag_color']

        else:
            # No detection - show help text
            self._draw_no_detection_help(overlay)
            info['detected'] = False

        # Draw compass indicator
        self._draw_compass(overlay, camera_bearing)

        return overlay, info

    def _draw_pin_marker(self, frame: np.ndarray, detection: Dict):
        """Draws AR marker on detected pin"""
        pos_x, pos_y = detection['position']
        top_x, top_y = detection['top_position']
        confidence = detection['confidence']

        # Choose color based on confidence
        if confidence > 0.7:
            color = self.color_pin_detected
        else:
            color = self.color_pin_uncertain

        # Draw vertical line on flagstick
        cv2.line(frame, (top_x, top_y), (pos_x, pos_y), color, 4)

        # Draw pulsing circle at flag
        pulse_radius = int(15 + 5 * math.sin(datetime.now().timestamp() * 3))
        cv2.circle(frame, (top_x, top_y), pulse_radius, color, 3)

        # Draw target reticle at flag
        reticle_size = 30
        cv2.line(frame,
                (top_x - reticle_size, top_y),
                (top_x + reticle_size, top_y),
                color, 2)
        cv2.line(frame,
                (top_x, top_y - reticle_size),
                (top_x, top_y + reticle_size),
                color, 2)

        # Draw base circle
        cv2.circle(frame, (pos_x, pos_y), 12, color, -1)

        # Add flag icon at top
        self._draw_flag_icon(frame, top_x, top_y - 20, detection['flag_color'])

        # Draw distance rings (if close)
        if detection['height_pixels'] > 100:  # Pin is relatively close
            self._draw_distance_rings(frame, pos_x, pos_y)

    def _draw_flag_icon(self, frame: np.ndarray, x: int, y: int, flag_color: str):
        """Draws small flag icon above detected pin"""
        # Flag pole
        cv2.line(frame, (x, y), (x, y - 15), (100, 100, 100), 2)

        # Flag triangle
        flag_colors = {
            'red': (0, 0, 255),
            'yellow': (0, 255, 255),
            'white': (255, 255, 255),
            'orange': (0, 165, 255)
        }

        color = flag_colors.get(flag_color, (255, 255, 255))

        pts = np.array([[x, y - 15], [x + 15, y - 10], [x, y - 5]], np.int32)
        cv2.fillPoly(frame, [pts], color)
        cv2.polylines(frame, [pts], True, (0, 0, 0), 1)

    def _draw_distance_rings(self, frame: np.ndarray, x: int, y: int):
        """Draws expanding distance rings around pin base"""
        timestamp = datetime.now().timestamp()

        for i in range(3):
            # Create expanding, fading rings
            phase = (timestamp * 2 + i * 0.5) % 1.5
            radius = int(30 + phase * 40)
            alpha = max(0, 1.0 - phase / 1.5)

            color = tuple(int(c * alpha) for c in self.color_distance_ring)
            cv2.circle(frame, (x, y), radius, color, 2)

    def _draw_info_panel(self, frame: np.ndarray, detection: Dict,
                        distance_yards: float = None):
        """Draws info panel with pin details"""
        height, width = frame.shape[:2]

        # Semi-transparent panel
        panel_height = 120
        panel = np.zeros((panel_height, width, 3), dtype=np.uint8)
        panel[:] = (0, 0, 0)

        # Blend with frame
        alpha = 0.6
        roi = frame[0:panel_height, 0:width]
        cv2.addWeighted(panel, alpha, roi, 1 - alpha, 0, roi)

        # Add text
        y_offset = 30

        # Title
        cv2.putText(frame, "PIN DETECTED", (20, y_offset),
                   cv2.FONT_HERSHEY_BOLD, 0.8, self.color_pin_detected, 2)

        y_offset += 30

        # Confidence
        confidence_pct = int(detection['confidence'] * 100)
        cv2.putText(frame, f"Confidence: {confidence_pct}%", (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color_info_text, 1)

        # Flag color
        cv2.putText(frame, f"Flag: {detection['flag_color'].title()}",
                   (250, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color_info_text, 1)

        y_offset += 25

        # Distance
        if distance_yards:
            cv2.putText(frame, f"Distance: {distance_yards:.0f} yards",
                       (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color_info_text, 1)
        else:
            cv2.putText(frame, "Distance: Use rangefinder",
                       (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        # Pole angle
        angle = detection.get('pole_angle', 0)
        cv2.putText(frame, f"Angle: {angle:.1f}°",
                   (250, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.color_info_text, 1)

    def _draw_confidence_meter(self, frame: np.ndarray, confidence: float):
        """Draws confidence meter bar"""
        height, width = frame.shape[:2]

        # Meter position (bottom right)
        meter_width = 200
        meter_height = 20
        meter_x = width - meter_width - 20
        meter_y = height - 40

        # Background
        cv2.rectangle(frame,
                     (meter_x, meter_y),
                     (meter_x + meter_width, meter_y + meter_height),
                     (50, 50, 50), -1)

        # Confidence bar
        bar_width = int(meter_width * confidence)

        # Color based on confidence level
        if confidence > 0.7:
            bar_color = (0, 255, 0)  # Green
        elif confidence > 0.4:
            bar_color = (0, 165, 255)  # Orange
        else:
            bar_color = (0, 0, 255)  # Red

        cv2.rectangle(frame,
                     (meter_x, meter_y),
                     (meter_x + bar_width, meter_y + meter_height),
                     bar_color, -1)

        # Border
        cv2.rectangle(frame,
                     (meter_x, meter_y),
                     (meter_x + meter_width, meter_y + meter_height),
                     (255, 255, 255), 2)

        # Label
        cv2.putText(frame, "CONFIDENCE",
                   (meter_x, meter_y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def _draw_no_detection_help(self, frame: np.ndarray):
        """Draws help text when no pin detected"""
        height, width = frame.shape[:2]

        # Center text
        text = "Point camera at flagstick"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        text_x = (width - text_size[0]) // 2
        text_y = height - 100

        # Semi-transparent background
        padding = 20
        cv2.rectangle(frame,
                     (text_x - padding, text_y - text_size[1] - padding),
                     (text_x + text_size[0] + padding, text_y + padding),
                     (0, 0, 0), -1)

        cv2.putText(frame, text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

        # Helper icon (camera symbol)
        icon_y = text_y - 80
        cv2.circle(frame, (width // 2, icon_y), 30, (100, 100, 100), 3)
        cv2.rectangle(frame,
                     (width // 2 - 15, icon_y - 10),
                     (width // 2 + 15, icon_y + 10),
                     (100, 100, 100), 2)

    def _draw_compass(self, frame: np.ndarray, bearing: float):
        """Draws compass showing camera direction"""
        height, width = frame.shape[:2]

        # Compass position (top right)
        compass_x = width - 80
        compass_y = 80
        compass_radius = 50

        # Compass circle
        cv2.circle(frame, (compass_x, compass_y), compass_radius,
                  (255, 255, 255), 2)

        # Cardinal directions
        cv2.putText(frame, "N", (compass_x - 8, compass_y - compass_radius - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Bearing needle
        needle_length = compass_radius - 10
        needle_angle_rad = math.radians(bearing - 90)  # -90 to start from top

        needle_end_x = int(compass_x + needle_length * math.cos(needle_angle_rad))
        needle_end_y = int(compass_y + needle_length * math.sin(needle_angle_rad))

        cv2.arrowedLine(frame, (compass_x, compass_y), (needle_end_x, needle_end_y),
                       (0, 0, 255), 3, tipLength=0.3)

        # Bearing text
        cv2.putText(frame, f"{int(bearing)}°",
                   (compass_x - 20, compass_y + compass_radius + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def _calculate_pin_gps(self, detection: Dict, user_gps: Tuple[float, float],
                          camera_bearing: float, frame_width: int,
                          distance_yards: float) -> Tuple[float, float]:
        """Calculates GPS coordinates of detected pin"""
        pin_pixel_x = detection['position'][0]

        pin_gps = self.pin_calculator.calculate_pin_gps(
            user_gps=user_gps,
            camera_bearing=camera_bearing,
            pin_pixel_x=pin_pixel_x,
            frame_width=frame_width,
            camera_fov=60,  # Typical smartphone camera FOV
            distance_yards=distance_yards
        )

        return pin_gps

    def get_stable_pin_detection(self) -> Optional[Dict]:
        """Gets stable pin detection with GPS"""
        stable = self.pin_detector.get_stable_detection()

        if stable and self.stable_pin_gps:
            stable['gps'] = self.stable_pin_gps

        return stable


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("AR PIN FINDER")
    print("Real-time pin detection with AR overlay")
    print("="*60)

    ar_finder = ARPinFinder()

    # Test with webcam or video
    import sys

    if len(sys.argv) > 1:
        # Video file
        video_path = sys.argv[1]
        cap = cv2.VideoCapture(video_path)
        print(f"\nProcessing video: {video_path}")
    else:
        # Webcam
        cap = cv2.VideoCapture(0)
        print("\nUsing webcam - Point at a vertical pole/flagstick")

    if not cap.isOpened():
        print("❌ Could not open camera/video")
        exit()

    print("\nControls:")
    print("  SPACE - Pause/Resume")
    print("  S - Save pin GPS location")
    print("  C - Toggle confidence meter")
    print("  Q - Quit")
    print("\n" + "="*60)

    paused = False
    saved_pins = []

    # Simulate user location and bearing (in production: from phone sensors)
    user_gps = (36.1234, -95.9876)  # Example coordinates
    camera_bearing = 90  # Facing East (would come from compass)
    distance_yards = 150  # Would come from rangefinder or GPS

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                print("\n✅ Video finished")
                break

            # Process frame with AR overlay
            ar_frame, info = ar_finder.process_frame(
                frame,
                user_gps=user_gps,
                camera_bearing=camera_bearing,
                distance_yards=distance_yards
            )

            if info.get('detected'):
                print(f"Pin detected: {info['confidence']:.0%} confidence, "
                      f"flag: {info['flag_color']}")

                if info.get('pin_gps'):
                    lat, lon = info['pin_gps']
                    print(f"  GPS: {lat:.6f}, {lon:.6f}")

        else:
            ar_frame = frame

        # Display
        cv2.imshow('AR Pin Finder (SPACE=pause, S=save, C=confidence, Q=quit)',
                   ar_frame)

        # Controls
        key = cv2.waitKey(1 if not paused else 0) & 0xFF

        if key == ord('q') or key == 27:
            print("\n👋 Quitting...")
            break
        elif key == 32:  # SPACE
            paused = not paused
            print(f"\n{'⏸️  Paused' if paused else '▶️  Resumed'}")
        elif key == ord('s'):  # S - Save
            stable = ar_finder.get_stable_pin_detection()
            if stable:
                saved_pins.append(stable)
                print(f"\n💾 Pin saved! ({len(saved_pins)} total)")
                if stable.get('gps'):
                    print(f"   GPS: {stable['gps'][0]:.6f}, {stable['gps'][1]:.6f}")
            else:
                print("\n⚠️  No stable detection to save")
        elif key == ord('c'):  # C - Toggle confidence meter
            ar_finder.show_confidence_meter = not ar_finder.show_confidence_meter
            print(f"\nConfidence meter: {'ON' if ar_finder.show_confidence_meter else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()

    # Summary
    if saved_pins:
        print("\n" + "="*60)
        print("SAVED PIN LOCATIONS")
        print("="*60)
        print(f"Total pins saved: {len(saved_pins)}")

        for i, pin in enumerate(saved_pins, 1):
            print(f"\nPin {i}:")
            print(f"  Confidence: {pin['confidence']:.0%}")
            print(f"  Flag color: {pin['flag_color']}")
            if pin.get('gps'):
                print(f"  GPS: {pin['gps'][0]:.6f}, {pin['gps'][1]:.6f}")

    print("\n" + "="*60)
    print("Mobile Implementation:")
    print("  - iOS: ARKit + AVFoundation + CoreLocation + CoreMotion")
    print("  - Android: ARCore + Camera2 + Location + SensorManager")
    print("  - React Native: react-native-ar + Vision Camera")
    print("\nFeatures:")
    print("  ✅ Real-time pin detection with AR overlay")
    print("  ✅ Visual markers and confidence indicators")
    print("  ✅ GPS position calculation")
    print("  ✅ Compass and distance display")
    print("="*60)
