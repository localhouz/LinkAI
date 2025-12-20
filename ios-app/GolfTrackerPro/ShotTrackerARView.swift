import SwiftUI
import ARKit
import RealityKit
import Vision
import CoreML

// MARK: - Shot Tracker AR View
struct ShotTrackerARView: View {
    let onBack: () -> Void
    
    @StateObject private var arViewModel = ShotTrackerViewModel()
    
    var body: some View {
        ZStack {
            // AR View
            ShotTrackerARContainer(viewModel: arViewModel)
                .ignoresSafeArea()
            
            // HUD Overlay
            VStack {
                // Top Bar
                HStack {
                    Button(action: onBack) {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                            Text("Back")
                        }
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.black.opacity(0.5))
                        .cornerRadius(20)
                    }
                    
                    Spacer()
                    
                    // Status Indicator
                    HStack(spacing: 8) {
                        Circle()
                            .fill(arViewModel.isDetecting ? Color.green : Color.red)
                            .frame(width: 10, height: 10)
                        
                        Text(arViewModel.isDetecting ? "TRACKING" : "SEARCHING")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white)
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(16)
                }
                .padding(.horizontal, 20)
                .padding(.top, 60)
                
                Spacer()
                
                // Detection Info
                if arViewModel.ballDetected {
                    VStack(spacing: 12) {
                        // Ball Position
                        HStack(spacing: 20) {
                            StatBox(label: "SPEED", value: String(format: "%.0f", arViewModel.estimatedSpeed), unit: "mph")
                            StatBox(label: "ANGLE", value: String(format: "%.0f", arViewModel.launchAngle), unit: "°")
                            StatBox(label: "DIR", value: String(format: "%.0f", arViewModel.launchDirection), unit: "°")
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 16)
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(16)
                    }
                }
                
                // Archetype Selection (when ball in flight)
                if arViewModel.showArchetypeSelection {
                    ArchetypeSelectionView(
                        onSelect: { archetype in
                            arViewModel.selectArchetype(archetype)
                        }
                    )
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
                
                // Instructions
                if !arViewModel.ballDetected {
                    VStack(spacing: 8) {
                        Image(systemName: "viewfinder")
                            .font(.system(size: 40))
                            .foregroundColor(.white.opacity(0.8))
                        
                        Text("Point camera at golf ball")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.white)
                        
                        Text("Ball will be tracked automatically")
                            .font(.system(size: 13))
                            .foregroundColor(.white.opacity(0.6))
                    }
                    .padding(30)
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(20)
                }
                
                Spacer().frame(height: 80)
            }
        }
    }
}

// MARK: - Stat Box
struct StatBox: View {
    let label: String
    let value: String
    let unit: String
    
    var body: some View {
        VStack(spacing: 4) {
            Text(label)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(.white.opacity(0.6))
            
            HStack(alignment: .lastTextBaseline, spacing: 2) {
                Text(value)
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                
                Text(unit)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.white.opacity(0.7))
            }
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Archetype Selection
struct ArchetypeSelectionView: View {
    let onSelect: (ShotArchetype) -> Void
    
    let archetypes: [ShotArchetype] = [
        .highSlice, .mediumSlice, .lowFade,
        .straight,
        .lowDraw, .mediumHook, .highHook
    ]
    
    var body: some View {
        VStack(spacing: 12) {
            Text("SELECT SHOT TYPE")
                .font(.system(size: 12, weight: .bold))
                .foregroundColor(.white.opacity(0.7))
            
            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 10) {
                ForEach(archetypes, id: \.self) { archetype in
                    Button(action: { onSelect(archetype) }) {
                        VStack(spacing: 6) {
                            Image(systemName: archetype.icon)
                                .font(.system(size: 20))
                            
                            Text(archetype.name)
                                .font(.system(size: 11, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(archetype.color.opacity(0.3))
                        .cornerRadius(10)
                        .overlay(
                            RoundedRectangle(cornerRadius: 10)
                                .stroke(archetype.color, lineWidth: 1)
                        )
                    }
                }
            }
        }
        .padding(20)
        .background(Color.black.opacity(0.85))
        .cornerRadius(20)
        .padding(.horizontal, 20)
        .padding(.bottom, 40)
    }
}

// MARK: - Shot Archetype
enum ShotArchetype: String, CaseIterable {
    case highSlice = "High Slice"
    case mediumSlice = "Medium Slice"
    case lowFade = "Low Fade"
    case straight = "Straight"
    case lowDraw = "Low Draw"
    case mediumHook = "Medium Hook"
    case highHook = "High Hook"
    
    var name: String { rawValue }
    
    var icon: String {
        switch self {
        case .highSlice: return "arrow.up.right"
        case .mediumSlice: return "arrow.right"
        case .lowFade: return "arrow.right.circle"
        case .straight: return "arrow.up"
        case .lowDraw: return "arrow.left.circle"
        case .mediumHook: return "arrow.left"
        case .highHook: return "arrow.up.left"
        }
    }
    
    var color: Color {
        switch self {
        case .highSlice, .mediumSlice, .lowFade:
            return Color.red
        case .straight:
            return Color.green
        case .lowDraw, .mediumHook, .highHook:
            return Color.blue
        }
    }
    
    var curveMultiplier: Float {
        switch self {
        case .highSlice: return 3.0
        case .mediumSlice: return 2.0
        case .lowFade: return 1.0
        case .straight: return 0.0
        case .lowDraw: return -1.0
        case .mediumHook: return -2.0
        case .highHook: return -3.0
        }
    }
}

// MARK: - View Model
class ShotTrackerViewModel: ObservableObject {
    @Published var isDetecting = false
    @Published var ballDetected = false
    @Published var ballPosition: CGPoint = .zero
    @Published var estimatedSpeed: Float = 0
    @Published var launchAngle: Float = 0
    @Published var launchDirection: Float = 0
    @Published var showArchetypeSelection = false
    @Published var selectedArchetype: ShotArchetype?
    @Published var trajectoryPoints: [SIMD3<Float>] = []
    
    private var previousBallPositions: [CGPoint] = []
    private var ballInFlight = false
    
    func updateBallPosition(_ position: CGPoint, timestamp: TimeInterval) {
        ballPosition = position
        ballDetected = true
        
        previousBallPositions.append(position)
        if previousBallPositions.count > 10 {
            previousBallPositions.removeFirst()
        }
        
        // Detect launch (ball moving upward rapidly)
        if previousBallPositions.count >= 3 {
            let velocityY = previousBallPositions.last!.y - previousBallPositions[previousBallPositions.count - 3].y
            
            if velocityY < -50 && !ballInFlight {
                // Ball launched!
                ballInFlight = true
                calculateLaunchParameters()
                
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    self.showArchetypeSelection = true
                }
            }
        }
    }
    
    func calculateLaunchParameters() {
        guard previousBallPositions.count >= 2 else { return }
        
        let last = previousBallPositions.last!
        let prev = previousBallPositions[previousBallPositions.count - 2]
        
        let dx = Float(last.x - prev.x)
        let dy = Float(last.y - prev.y)
        
        // Estimate speed (pixels/frame to mph conversion factor)
        let pixelSpeed = sqrt(dx * dx + dy * dy)
        estimatedSpeed = pixelSpeed * 2.5 // Calibration factor
        
        // Launch angle
        launchAngle = atan2(-dy, abs(dx)) * 180 / .pi
        
        // Direction (relative to camera facing)
        launchDirection = atan2(dx, -dy) * 180 / .pi
    }
    
    func selectArchetype(_ archetype: ShotArchetype) {
        selectedArchetype = archetype
        showArchetypeSelection = false
        
        // Generate trajectory points
        generateTrajectory(archetype: archetype)
    }
    
    func generateTrajectory(archetype: ShotArchetype) {
        trajectoryPoints.removeAll()
        
        let speed = estimatedSpeed
        let angle = launchAngle * .pi / 180
        let curve = archetype.curveMultiplier
        
        // Physics simulation
        var vx = speed * cos(angle) * 0.44704 // mph to m/s
        var vy = speed * sin(angle) * 0.44704
        var vz: Float = 0
        
        var x: Float = 0
        var y: Float = 0
        var z: Float = 0
        
        let dt: Float = 0.05
        let g: Float = 9.81
        
        for _ in 0..<200 {
            // Update position
            x += vx * dt
            y += vy * dt
            z += vz * dt
            
            // Gravity
            vy -= g * dt
            
            // Curve (Magnus effect approximation)
            vz += curve * 0.01
            
            // Air resistance
            vx *= 0.995
            vy *= 0.995
            vz *= 0.995
            
            trajectoryPoints.append(SIMD3(x, y, z))
            
            if y < 0 { break }
        }
    }
    
    func reset() {
        ballDetected = false
        ballInFlight = false
        showArchetypeSelection = false
        selectedArchetype = nil
        trajectoryPoints.removeAll()
        previousBallPositions.removeAll()
        estimatedSpeed = 0
        launchAngle = 0
        launchDirection = 0
    }
}

// MARK: - AR Container
struct ShotTrackerARContainer: UIViewRepresentable {
    @ObservedObject var viewModel: ShotTrackerViewModel
    
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        
        // Configure AR session
        let config = ARWorldTrackingConfiguration()
        config.frameSemantics = .personSegmentationWithDepth
        
        arView.session.run(config)
        
        // Setup ball detection
        context.coordinator.setupVision(arView: arView, viewModel: viewModel)
        
        return arView
    }
    
    func updateUIView(_ arView: ARView, context: Context) {
        // Update trajectory visualization
        if let archetype = viewModel.selectedArchetype {
            context.coordinator.drawTrajectory(
                arView: arView,
                points: viewModel.trajectoryPoints,
                color: archetype.color
            )
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject, ARSessionDelegate {
        var visionRequest: VNCoreMLRequest?
        weak var currentARView: ARView?
        weak var viewModel: ShotTrackerViewModel?
        var trajectoryAnchor: AnchorEntity?
        
        func setupVision(arView: ARView, viewModel: ShotTrackerViewModel) {
            self.currentARView = arView
            self.viewModel = viewModel
            arView.session.delegate = self
            
            // Try to load CoreML model (would need actual .mlmodel file)
            // For now, use Vision's built-in object detection
            setupObjectDetection()
        }
        
        func setupObjectDetection() {
            // Using Vision framework for object detection
            // In production, this would load a custom YOLO model
            let request = VNDetectContoursRequest { [weak self] request, error in
                guard let results = request.results as? [VNContoursObservation] else { return }
                
                // Process contours to find ball-like objects
                DispatchQueue.main.async {
                    self?.viewModel?.isDetecting = !results.isEmpty
                }
            }
            
            visionRequest = nil // Placeholder until model is trained
        }
        
        func session(_ session: ARSession, didUpdate frame: ARFrame) {
            // Process each frame for ball detection
            let pixelBuffer = frame.capturedImage
            
            // Run inference (when model is available)
            // For now, simulate detection
            let timestamp = frame.timestamp
            
            // Simulated ball detection for demo
            // In production, this would run CoreML inference
        }
        
        func drawTrajectory(arView: ARView, points: [SIMD3<Float>], color: Color) {
            // Remove existing trajectory
            if let existing = trajectoryAnchor {
                arView.scene.removeAnchor(existing)
            }
            
            guard !points.isEmpty else { return }
            
            // Create new anchor
            let anchor = AnchorEntity(world: .zero)
            trajectoryAnchor = anchor
            
            // Create trajectory line using spheres
            for (index, point) in points.enumerated() {
                let sphere = ModelEntity(
                    mesh: .generateSphere(radius: 0.02),
                    materials: [SimpleMaterial(
                        color: UIColor(color).withAlphaComponent(CGFloat(1.0 - Float(index) / Float(points.count))),
                        isMetallic: false
                    )]
                )
                sphere.position = point
                anchor.addChild(sphere)
            }
            
            arView.scene.addAnchor(anchor)
        }
    }
}

#Preview {
    ShotTrackerARView(onBack: {})
}
