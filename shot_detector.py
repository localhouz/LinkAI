"""
Auto-Shot Detection Module
Detects golf shots using audio (club impact sound) and motion
"""

import numpy as np
import pyaudio
import wave
from collections import deque
import time
import threading


class ShotDetector:
    """Detects golf shots automatically using audio and optionally motion"""

    def __init__(self, sensitivity: float = 0.7):
        """
        Initialize shot detector

        Args:
            sensitivity: Detection sensitivity (0.0-1.0, higher = more sensitive)
        """
        self.sensitivity = sensitivity
        self.is_listening = False
        self.callback = None

        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100

        # Detection parameters
        self.IMPACT_THRESHOLD = int(5000 * (1.0 / sensitivity))  # Amplitude threshold
        self.SILENCE_DURATION = 1.0  # Seconds of silence before/after impact

        # Ring buffer for audio
        self.audio_buffer = deque(maxlen=int(self.RATE / self.CHUNK * 3))  # 3 seconds

        self.p = None
        self.stream = None

    def start_listening(self, on_shot_detected=None):
        """
        Starts listening for shots

        Args:
            on_shot_detected: Callback function called when shot is detected
                              Signature: on_shot_detected(timestamp, audio_data)
        """
        self.callback = on_shot_detected
        self.is_listening = True

        # Initialize PyAudio
        self.p = pyaudio.PyAudio()

        try:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self._audio_callback
            )

            self.stream.start_stream()
            print("🎤 Shot detector listening...")
            print("Hit a golf ball to test detection")
            print("Press Ctrl+C to stop")

        except Exception as e:
            print(f"Error starting audio stream: {e}")
            print("Make sure you have a microphone connected and permissions enabled")
            self.is_listening = False

    def stop_listening(self):
        """Stops listening for shots"""
        self.is_listening = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.p:
            self.p.terminate()

        print("Shot detector stopped")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for processing audio stream"""
        if not self.is_listening:
            return (in_data, pyaudio.paComplete)

        # Convert audio data to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Add to buffer
        self.audio_buffer.append(audio_data)

        # Check for impact sound
        max_amplitude = np.max(np.abs(audio_data))

        if max_amplitude > self.IMPACT_THRESHOLD:
            # Detected potential shot!
            timestamp = time.time()

            # Get audio context (before and after impact)
            audio_context = np.concatenate(list(self.audio_buffer))

            # Verify it's likely a golf shot (short, sharp sound)
            if self._verify_golf_shot(audio_context):
                print(f"⛳ SHOT DETECTED! (amplitude: {max_amplitude})")

                if self.callback:
                    # Call the callback in a separate thread to avoid blocking audio
                    threading.Thread(
                        target=self.callback,
                        args=(timestamp, audio_context)
                    ).start()

        return (in_data, pyaudio.paContinue)

    def _verify_golf_shot(self, audio_data: np.ndarray) -> bool:
        """
        Verifies that detected sound is likely a golf shot

        Golf shots have characteristic features:
        - Short duration (<0.1 seconds)
        - Sharp attack (sudden increase)
        - Quick decay

        Args:
            audio_data: Audio data array

        Returns:
            bool: True if likely a golf shot
        """
        # Find the peak
        peak_idx = np.argmax(np.abs(audio_data))

        # Check if peak is sharp (not sustained)
        window = 2000  # ~0.05 seconds

        if peak_idx < window or peak_idx > len(audio_data) - window:
            return False

        # Get region around peak
        peak_region = audio_data[peak_idx-window:peak_idx+window]
        peak_amplitude = np.max(np.abs(peak_region))

        # Check if it decays quickly (characteristic of impact)
        post_peak = audio_data[peak_idx:peak_idx+window]
        avg_post = np.mean(np.abs(post_peak))

        decay_ratio = avg_post / peak_amplitude

        # Golf shots typically have decay ratio < 0.3
        return decay_ratio < 0.4

    def test_microphone(self):
        """
        Tests if microphone is working and shows audio levels
        """
        print("Testing microphone...")
        print("Make some noise to test (speak, clap, etc.)")
        print("Press Ctrl+C to stop\n")

        p = pyaudio.PyAudio()

        try:
            stream = p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            print("Microphone active - showing audio levels:")
            print("-" * 50)

            for _ in range(100):  # Test for ~2 seconds
                data = stream.read(self.CHUNK)
                audio_data = np.frombuffer(data, dtype=np.int16)
                level = np.max(np.abs(audio_data))

                # Visual level meter
                bars = int(level / 500)
                print(f"Level: {'█' * min(bars, 50)} {level:6d}", end='\r')

                time.sleep(0.02)

            print("\n" + "-" * 50)
            print("Microphone test complete!")

            stream.stop_stream()
            stream.close()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            p.terminate()


class MotionShotDetector:
    """
    Detects shots using phone accelerometer/gyroscope
    (This would be implemented in the mobile app with native sensors)
    """

    def __init__(self):
        self.threshold = 2.0  # G-force threshold
        self.is_active = False

    def start_monitoring(self):
        """Start monitoring phone motion sensors"""
        print("Motion detection would use phone's accelerometer/gyroscope")
        print("This will be implemented in the mobile app (React Native/Flutter/Swift)")
        print("\nMotion patterns to detect:")
        print("  - Rapid acceleration (backswing)")
        print("  - Sharp deceleration (impact)")
        print("  - Characteristic swing tempo")

    def detect_swing_pattern(self, accel_data):
        """
        Analyzes accelerometer data for golf swing pattern

        Args:
            accel_data: Array of accelerometer readings (x, y, z, timestamp)

        Returns:
            bool: True if swing pattern detected
        """
        # Pseudocode for mobile implementation:
        # 1. Detect rapid acceleration (backswing)
        # 2. Look for peak deceleration (impact)
        # 3. Verify swing tempo (~1-1.5 seconds total)
        # 4. Return True if pattern matches
        pass


# Example usage
if __name__ == "__main__":
    import sys

    print("="*60)
    print("AUTO-SHOT DETECTOR")
    print("="*60)
    print("\nThis module automatically detects golf shots using:")
    print("  1. Audio (microphone) - detects club impact sound")
    print("  2. Motion (mobile only) - detects swing motion")
    print("="*60)

    # Test microphone first
    detector = ShotDetector(sensitivity=0.7)

    print("\nChoose an option:")
    print("  1. Test microphone")
    print("  2. Start shot detection")
    print("  3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == "1":
        detector.test_microphone()

    elif choice == "2":
        def on_shot(timestamp, audio):
            print(f"\n✅ Shot recorded at {time.ctime(timestamp)}")
            print("   (In real app: would start ball tracking now)")

        try:
            detector.start_listening(on_shot_detected=on_shot)

            # Keep running
            while detector.is_listening:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nStopping...")
            detector.stop_listening()

    else:
        print("Exiting...")

    print("\n" + "="*60)
    print("Note: For mobile app, we'll use native audio APIs")
    print("      - iOS: AVAudioEngine")
    print("      - Android: AudioRecord")
    print("="*60)
