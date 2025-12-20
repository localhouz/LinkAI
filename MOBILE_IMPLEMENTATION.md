# Mobile Implementation Guide

Complete guide for porting the Golf Ball Finder to iOS/Android mobile apps.

---

## Architecture Overview

The Python prototype is designed with **mobile-first architecture**:
- ✅ Modular functions that map 1:1 to mobile equivalents
- ✅ Stateful design (tracks ball position between frames)
- ✅ Real-time optimized (30+ FPS capable)
- ✅ Clear separation: Detection → Physics → Rendering

---

## Key File: `live_tracer.py`

This is your **blueprint for mobile**. Every function has a direct mobile equivalent.

### Core Function (Called Every Frame):

```python
def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
    # 1. Detect ball
    # 2. Update tracking state
    # 3. Calculate trajectory (when ready)
    # 4. Draw overlay
    # 5. Return annotated frame + info
```

**Mobile equivalent:** Camera callback function

---

## iOS Implementation (Swift + SwiftUI)

### 1. Camera Setup (AVFoundation)

```swift
import AVFoundation
import Vision

class BallTrackerCamera: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    private var captureSession: AVCaptureSession!
    private var videoOutput: AVCaptureVideoDataOutput!

    func setupCamera() {
        captureSession = AVCaptureSession()
        captureSession.sessionPreset = .high

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera,
                                                   for: .video,
                                                   position: .back) else { return }

        let input = try! AVCaptureDeviceInput(device: camera)
        captureSession.addInput(input)

        videoOutput = AVCaptureVideoDataOutput()
        videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue.global(qos: .userInitiated))
        captureSession.addOutput(videoOutput)

        captureSession.startRunning()
    }

    // MAIN CALLBACK - Called for every frame
    func captureOutput(_ output: AVCaptureOutput,
                      didOutput sampleBuffer: CMSampleBuffer,
                      from connection: AVCaptureConnection) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }

        // Convert to UIImage
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return }
        let frame = UIImage(cgImage: cgImage)

        // Process frame (Python equivalent: tracer.process_frame())
        processFrame(frame)
    }
}
```

### 2. Ball Detection (Vision Framework)

Python `ball_detector.py` → iOS Vision API:

```swift
import Vision

class BallDetector {
    func detectBall(in image: CGImage, completion: @escaping (CGPoint?) -> Void) {
        // Use Vision's object detection or color detection
        let request = VNDetectRectanglesRequest { request, error in
            guard let observations = request.results as? [VNRectangleObservation] else {
                completion(nil)
                return
            }

            // Filter for circular white objects (golf ball)
            // Your custom logic here based on Python detector
            if let ballRect = observations.first {
                let center = CGPoint(x: ballRect.boundingBox.midX,
                                   y: ballRect.boundingBox.midY)
                completion(center)
            } else {
                completion(nil)
            }
        }

        let handler = VNImageRequestHandler(cgImage: image)
        try? handler.perform([request])
    }
}
```

**Alternative: Use CoreML**
Train a custom model for golf ball detection:

```swift
// Export your Python model
// Python: model.export_to_coreml()

import CoreML

let model = try! GolfBallDetector(configuration: MLModelConfiguration())
let prediction = try! model.prediction(image: pixelBuffer)
```

### 3. Physics Calculations

Python `trajectory_predictor.py` → Swift:

```swift
struct TrajectoryCalculator {
    let gravity: Double = 9.81
    let fps: Double = 30.0

    func calculateVelocity(positions: [(x: Double, y: Double, t: Double)]) -> (vx: Double, vy: Double, angle: Double) {
        guard positions.count >= 2 else { return (0, 0, 0) }

        let first = positions.first!
        let last = positions.last!

        let dx = last.x - first.x
        let dy = last.y - first.y
        let dt = last.t - first.t

        let vx = dx / dt
        let vy = dy / dt

        let speed = sqrt(vx * vx + vy * vy)
        let angle = atan2(-vy, vx) * 180 / .pi

        return (vx, vy, angle)
    }

    func predictTrajectory(x0: Double, y0: Double, vx: Double, vy: Double) -> [(x: Double, y: Double)] {
        var points: [(Double, Double)] = []
        let flightTime = abs(2 * vy / gravity)

        for i in 0..<100 {
            let t = Double(i) / 100.0 * flightTime
            let x = x0 + vx * t
            let y = y0 + vy * t + 0.5 * gravity * t * t
            points.append((x, y))
        }

        return points
    }
}
```

### 4. AR Overlay (SceneKit or Metal)

Python `_draw_overlay()` → iOS SceneKit:

```swift
import SceneKit
import ARKit

class TraceOverlay {
    var sceneView: ARSCNView!
    var traceNode: SCNNode!

    func drawTrace(positions: [CGPoint]) {
        // Create line geometry from positions
        let path = UIBezierPath()
        path.move(to: positions.first!)
        positions.forEach { path.addLine(to: $0) }

        // Convert to 3D scene
        let shape = SCNShape(path: path, extrusionDepth: 0.01)
        shape.firstMaterial?.diffuse.contents = UIColor.cyan

        traceNode = SCNNode(geometry: shape)
        sceneView.scene.rootNode.addChildNode(traceNode)
    }
}
```

**Alternative: Simpler 2D Overlay**

```swift
import SwiftUI

struct CameraOverlay: View {
    @ObservedObject var tracker: BallTracker

    var body: some View {
        ZStack {
            // Camera preview
            CameraPreview(tracker: tracker)

            // Trace overlay
            Path { path in
                guard let first = tracker.ballTrail.first else { return }
                path.move(to: first)
                tracker.ballTrail.forEach { path.addLine(to: $0) }
            }
            .stroke(Color.cyan, lineWidth: 3)

            // Stats overlay
            VStack {
                Spacer()
                HStack {
                    Spacer()
                    if let stats = tracker.stats {
                        VStack(alignment: .trailing) {
                            Text("Speed: \(stats.speed, specifier: "%.0f") px/s")
                            Text("Angle: \(stats.angle, specifier: "%.1f")°")
                        }
                        .padding()
                        .background(Color.black.opacity(0.6))
                        .foregroundColor(.white)
                    }
                }
            }
        }
    }
}
```

### 5. Complete iOS App Structure

```swift
// Main ViewModel
class BallTrackerViewModel: ObservableObject {
    @Published var ballTrail: [CGPoint] = []
    @Published var isTracking = false
    @Published var stats: ShotStats?

    private let detector = BallDetector()
    private let calculator = TrajectoryCalculator()
    private var trajectoryCalculated = false

    // MAIN FUNCTION - Called every frame
    func processFrame(_ image: UIImage) {
        // 1. Detect ball
        detector.detectBall(in: image.cgImage!) { ballCenter in
            guard let center = ballCenter else {
                self.handleBallLost()
                return
            }

            // 2. Update tracking state
            self.updateTrackingState(center)

            // 3. Calculate trajectory if ready
            if self.ballTrail.count >= 5 && !self.trajectoryCalculated {
                self.calculateTrajectory()
            }
        }
    }

    private func updateTrackingState(_ position: CGPoint) {
        if !isTracking {
            isTracking = true
        }
        ballTrail.append(position)
    }

    private func calculateTrajectory() {
        let positions = ballTrail.prefix(10).enumerated().map { (i, point) in
            (x: Double(point.x), y: Double(point.y), t: Double(i) / 30.0)
        }

        let (vx, vy, angle) = calculator.calculateVelocity(positions: positions)

        stats = ShotStats(speed: sqrt(vx*vx + vy*vy) * 30, angle: angle)
        trajectoryCalculated = true
    }

    func reset() {
        ballTrail.removeAll()
        isTracking = false
        trajectoryCalculated = false
        stats = nil
    }
}

struct ShotStats {
    let speed: Double
    let angle: Double
}
```

---

## Android Implementation (Kotlin)

### 1. Camera Setup (CameraX)

```kotlin
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider

class BallTrackerCamera(private val context: Context) {
    private var imageAnalyzer: ImageAnalysis? = null

    fun setupCamera(lifecycleOwner: LifecycleOwner) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)

        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()

            // Preview
            val preview = Preview.Builder().build()

            // Image analysis (ball detection)
            imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(Executors.newSingleThreadExecutor(), BallDetectorAnalyzer())
                }

            // Bind to lifecycle
            cameraProvider.bindToLifecycle(
                lifecycleOwner,
                CameraSelector.DEFAULT_BACK_CAMERA,
                preview,
                imageAnalyzer
            )
        }, ContextCompat.getMainExecutor(context))
    }
}

// Image analyzer - called for every frame
class BallDetectorAnalyzer : ImageAnalysis.Analyzer {
    override fun analyze(imageProxy: ImageProxy) {
        val bitmap = imageProxy.toBitmap()

        // Process frame (Python equivalent: tracer.process_frame())
        processFrame(bitmap)

        imageProxy.close()
    }
}
```

### 2. Ball Detection (ML Kit or TensorFlow Lite)

```kotlin
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.objects.ObjectDetection

class BallDetector {
    private val detector = ObjectDetection.getClient(options)

    fun detectBall(bitmap: Bitmap, callback: (PointF?) -> Unit) {
        val image = InputImage.fromBitmap(bitmap, 0)

        detector.process(image)
            .addOnSuccessListener { detectedObjects ->
                // Filter for white circular objects (golf ball)
                val ball = detectedObjects.firstOrNull { obj ->
                    // Your logic to identify golf ball
                    obj.boundingBox.width() / obj.boundingBox.height() in 0.8..1.2
                }

                val center = ball?.let {
                    PointF(
                        it.boundingBox.centerX().toFloat(),
                        it.boundingBox.centerY().toFloat()
                    )
                }

                callback(center)
            }
    }
}
```

### 3. Complete Android ViewModel

```kotlin
class BallTrackerViewModel : ViewModel() {
    private val _ballTrail = MutableLiveData<List<PointF>>(emptyList())
    val ballTrail: LiveData<List<PointF>> = _ballTrail

    private val _isTracking = MutableLiveData(false)
    val isTracking: LiveData<Boolean> = _isTracking

    private val _stats = MutableLiveData<ShotStats?>()
    val stats: LiveData<ShotStats?> = _stats

    private val detector = BallDetector()
    private val calculator = TrajectoryCalculator()
    private var trajectoryCalculated = false

    // MAIN FUNCTION - Called every frame
    fun processFrame(bitmap: Bitmap) {
        detector.detectBall(bitmap) { ballCenter ->
            ballCenter?.let {
                updateTrackingState(it)

                if (_ballTrail.value!!.size >= 5 && !trajectoryCalculated) {
                    calculateTrajectory()
                }
            } ?: handleBallLost()
        }
    }

    private fun updateTrackingState(position: PointF) {
        if (_isTracking.value == false) {
            _isTracking.postValue(true)
        }
        _ballTrail.postValue(_ballTrail.value!! + position)
    }

    private fun calculateTrajectory() {
        val positions = _ballTrail.value!!.take(10).mapIndexed { i, point ->
            Triple(point.x.toDouble(), point.y.toDouble(), i / 30.0)
        }

        val (vx, vy, angle) = calculator.calculateVelocity(positions)

        _stats.postValue(ShotStats(
            speed = Math.sqrt(vx * vx + vy * vy) * 30,
            angle = angle
        ))
        trajectoryCalculated = true
    }

    fun reset() {
        _ballTrail.postValue(emptyList())
        _isTracking.postValue(false)
        trajectoryCalculated = false
        _stats.postValue(null)
    }
}

data class ShotStats(val speed: Double, val angle: Double)
```

---

## React Native Implementation

### 1. Camera (react-native-vision-camera)

```javascript
import { Camera, useCameraDevices, useFrameProcessor } from 'react-native-vision-camera';
import { runOnJS } from 'react-native-reanimated';

function BallTrackerCamera() {
  const devices = useCameraDevices();
  const device = devices.back;

  // MAIN CALLBACK - Called for every frame
  const frameProcessor = useFrameProcessor((frame) => {
    'worklet';

    // Detect ball (using Vision Camera plugin or custom native module)
    const ballPosition = detectBall(frame);

    if (ballPosition) {
      runOnJS(processFrame)(ballPosition);
    }
  }, []);

  return (
    <Camera
      device={device}
      isActive={true}
      frameProcessor={frameProcessor}
    />
  );
}
```

### 2. Ball Detection (Native Module)

```javascript
// BallDetector.ts
import { NativeModules } from 'react-native';

const { BallDetectorModule } = NativeModules;

export class BallDetector {
  static detectBall(frame): Promise<{x: number, y: number} | null> {
    return BallDetectorModule.detectBall(frame);
  }
}
```

### 3. Tracking State (React Hooks)

```javascript
import { useState, useCallback } from 'react';

function useBallTracker() {
  const [ballTrail, setBallTrail] = useState([]);
  const [isTracking, setIsTracking] = useState(false);
  const [stats, setStats] = useState(null);
  const [trajectoryCalculated, setTrajectoryCalculated] = useState(false);

  // MAIN FUNCTION
  const processFrame = useCallback((ballPosition) => {
    if (!ballPosition) {
      handleBallLost();
      return;
    }

    // Update tracking
    if (!isTracking) {
      setIsTracking(true);
    }

    setBallTrail(prev => [...prev, ballPosition]);

    // Calculate trajectory if ready
    if (ballTrail.length >= 5 && !trajectoryCalculated) {
      calculateTrajectory();
    }
  }, [isTracking, ballTrail, trajectoryCalculated]);

  const calculateTrajectory = () => {
    const positions = ballTrail.slice(0, 10);
    const { vx, vy, angle } = TrajectoryCalculator.calculateVelocity(positions);

    setStats({
      speed: Math.sqrt(vx * vx + vy * vy) * 30,
      angle: angle
    });

    setTrajectoryCalculated(true);
  };

  const reset = () => {
    setBallTrail([]);
    setIsTracking(false);
    setTrajectoryCalculated(false);
    setStats(null);
  };

  return { ballTrail, isTracking, stats, processFrame, reset };
}
```

---

## Performance Optimization Tips

### All Platforms:

1. **Run detection on background thread**
   - iOS: `DispatchQueue.global()`
   - Android: `Executors.newSingleThreadExecutor()`
   - React Native: Worklet thread

2. **Use GPU acceleration**
   - iOS: CoreML, Metal
   - Android: TensorFlow Lite GPU delegate
   - React Native: Native modules with GPU

3. **Optimize frame rate**
   - Process every 2nd or 3rd frame if needed
   - Target 30 FPS minimum

4. **Cache trajectory calculations**
   - Only calculate once per shot
   - Reuse predicted trajectory

---

## Testing Checklist

- [ ] Camera permissions working
- [ ] Real-time frame processing (30+ FPS)
- [ ] Ball detection accurate in various lighting
- [ ] Trace overlay smooth
- [ ] Stats calculated correctly
- [ ] Reset function works
- [ ] Data saves to database
- [ ] Offline mode functional
- [ ] Battery usage acceptable
- [ ] Memory usage stable

---

## Next Steps

1. **Start with iOS or Android** (pick your primary platform)
2. **Implement camera + basic detection first**
3. **Add overlay rendering**
4. **Integrate with existing database/features**
5. **Test extensively on golf course**
6. **Optimize performance**
7. **Add polish (animations, haptics, sounds)**

---

**The Python code is your blueprint - every function maps directly to mobile!**
