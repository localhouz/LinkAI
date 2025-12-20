import SwiftUI
import ARKit
import RealityKit

// MARK: - Putt Reader AR View (LiDAR)
struct PuttReaderARView: View {
    let onBack: () -> Void
    
    @StateObject private var viewModel = PuttReaderViewModel()
    
    var body: some View {
        ZStack {
            // AR View with LiDAR
            PuttReaderARContainer(viewModel: viewModel)
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
                    
                    // LiDAR Status
                    HStack(spacing: 8) {
                        Image(systemName: viewModel.lidarAvailable ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(viewModel.lidarAvailable ? .green : .red)
                        
                        Text(viewModel.lidarAvailable ? "LiDAR ACTIVE" : "NO LiDAR")
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
                
                // Scan Progress
                if viewModel.isScanning {
                    VStack(spacing: 12) {
                        ProgressView(value: viewModel.scanProgress)
                            .progressViewStyle(LinearProgressViewStyle(tint: .green))
                            .frame(width: 200)
                        
                        Text("Scanning green... \(Int(viewModel.scanProgress * 100))%")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white)
                    }
                    .padding(20)
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(16)
                }
                
                // Break Analysis Results
                if viewModel.analysisComplete {
                    VStack(spacing: 16) {
                        Text("PUTT ANALYSIS")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white.opacity(0.7))
                        
                        HStack(spacing: 24) {
                            VStack(spacing: 4) {
                                Text(String(format: "%.1f", viewModel.breakAmount))
                                    .font(.system(size: 32, weight: .bold, design: .rounded))
                                    .foregroundColor(.white)
                                Text("inches")
                                    .font(.system(size: 12))
                                    .foregroundColor(.white.opacity(0.6))
                            }
                            
                            VStack(spacing: 4) {
                                HStack(spacing: 4) {
                                    Image(systemName: viewModel.breakDirection == .left ? "arrow.left" : "arrow.right")
                                    Text(viewModel.breakDirection.rawValue)
                                }
                                .font(.system(size: 24, weight: .bold))
                                .foregroundColor(viewModel.breakDirection == .left ? .blue : .red)
                                
                                Text("break")
                                    .font(.system(size: 12))
                                    .foregroundColor(.white.opacity(0.6))
                            }
                            
                            VStack(spacing: 4) {
                                Text(String(format: "%.1f", viewModel.slopePercent))
                                    .font(.system(size: 32, weight: .bold, design: .rounded))
                                    .foregroundColor(.white)
                                Text("% slope")
                                    .font(.system(size: 12))
                                    .foregroundColor(.white.opacity(0.6))
                            }
                        }
                        
                        // Recommended Aim Point
                        VStack(spacing: 6) {
                            Text("AIM POINT")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.green)
                            
                            Text(viewModel.aimPointDescription)
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.white)
                        }
                        .padding(.top, 8)
                    }
                    .padding(24)
                    .background(Color.black.opacity(0.85))
                    .cornerRadius(20)
                    .padding(.horizontal, 20)
                }
                
                // Instructions
                if !viewModel.isScanning && !viewModel.analysisComplete {
                    VStack(spacing: 16) {
                        Image(systemName: "camera.viewfinder")
                            .font(.system(size: 40))
                            .foregroundColor(.white.opacity(0.8))
                        
                        Text("Position camera over the green")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.white)
                        
                        Text("Move slowly to scan the surface between ball and hole")
                            .font(.system(size: 13))
                            .foregroundColor(.white.opacity(0.6))
                            .multilineTextAlignment(.center)
                        
                        Button(action: { viewModel.startScan() }) {
                            Text("START SCAN")
                                .font(.system(size: 16, weight: .bold))
                                .foregroundColor(Color(hex: "1B5E20"))
                                .padding(.horizontal, 40)
                                .padding(.vertical, 14)
                                .background(Color.white)
                                .cornerRadius(25)
                        }
                        .padding(.top, 8)
                    }
                    .padding(30)
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(20)
                }
                
                // Reset Button
                if viewModel.analysisComplete {
                    Button(action: { viewModel.reset() }) {
                        Text("NEW SCAN")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 30)
                            .padding(.vertical, 12)
                            .background(Color.white.opacity(0.2))
                            .cornerRadius(20)
                    }
                    .padding(.top, 20)
                }
                
                Spacer().frame(height: 80)
            }
            
            // Legend
            VStack {
                Spacer()
                
                HStack(spacing: 20) {
                    LegendItem(color: .green, label: "Flat")
                    LegendItem(color: .blue, label: "Breaks Left")
                    LegendItem(color: .red, label: "Breaks Right")
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Color.black.opacity(0.7))
                .cornerRadius(12)
            }
            .padding(.bottom, 30)
            .opacity(viewModel.isScanning || viewModel.analysisComplete ? 1 : 0)
        }
    }
}

// MARK: - Legend Item
struct LegendItem: View {
    let color: Color
    let label: String
    
    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 10, height: 10)
            Text(label)
                .font(.system(size: 11))
                .foregroundColor(.white)
        }
    }
}

// MARK: - Break Direction
enum BreakDirection: String {
    case left = "LEFT"
    case right = "RIGHT"
    case straight = "STRAIGHT"
}

// MARK: - View Model
class PuttReaderViewModel: ObservableObject {
    @Published var lidarAvailable = false
    @Published var isScanning = false
    @Published var scanProgress: Float = 0
    @Published var analysisComplete = false
    @Published var breakAmount: Float = 0
    @Published var breakDirection: BreakDirection = .straight
    @Published var slopePercent: Float = 0
    @Published var aimPointDescription: String = ""
    @Published var meshNormals: [SIMD3<Float>] = []
    
    init() {
        checkLiDARAvailability()
    }
    
    func checkLiDARAvailability() {
        lidarAvailable = ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh)
    }
    
    func startScan() {
        isScanning = true
        scanProgress = 0
        
        // Simulate scanning progress
        Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { timer in
            self.scanProgress += 0.02
            
            if self.scanProgress >= 1.0 {
                timer.invalidate()
                self.completeScan()
            }
        }
    }
    
    func completeScan() {
        isScanning = false
        analysisComplete = true
        
        // Analyze mesh data (simulated for demo)
        // In production, this would process actual LiDAR mesh normals
        analyzeMesh()
    }
    
    func analyzeMesh() {
        // Simulate analysis based on mesh normals
        // In production, this calculates from actual LiDAR data
        
        // Random break for demo
        let randomBreak = Float.random(in: 1...8)
        breakAmount = randomBreak
        
        let randomDir = Float.random(in: -1...1)
        if randomDir > 0.3 {
            breakDirection = .right
        } else if randomDir < -0.3 {
            breakDirection = .left
        } else {
            breakDirection = .straight
        }
        
        slopePercent = Float.random(in: 0.5...4.0)
        
        // Calculate aim point
        calculateAimPoint()
    }
    
    func calculateAimPoint() {
        switch breakDirection {
        case .left:
            aimPointDescription = "Aim \(Int(breakAmount)) inches right of hole"
        case .right:
            aimPointDescription = "Aim \(Int(breakAmount)) inches left of hole"
        case .straight:
            aimPointDescription = "Aim directly at the hole"
        }
    }
    
    func reset() {
        isScanning = false
        analysisComplete = false
        scanProgress = 0
        breakAmount = 0
        breakDirection = .straight
        slopePercent = 0
        aimPointDescription = ""
        meshNormals.removeAll()
    }
}

// MARK: - AR Container with LiDAR
struct PuttReaderARContainer: UIViewRepresentable {
    @ObservedObject var viewModel: PuttReaderViewModel
    
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        
        // Configure AR session with LiDAR mesh
        let config = ARWorldTrackingConfiguration()
        
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            config.sceneReconstruction = .mesh
            config.environmentTexturing = .automatic
            
            // Enable mesh visualization
            arView.debugOptions.insert(.showSceneUnderstanding)
        }
        
        arView.session.run(config)
        arView.session.delegate = context.coordinator
        context.coordinator.arView = arView
        context.coordinator.viewModel = viewModel
        
        return arView
    }
    
    func updateUIView(_ arView: ARView, context: Context) {
        if viewModel.analysisComplete {
            context.coordinator.visualizeSlopeGradient(arView: arView)
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator: NSObject, ARSessionDelegate {
        weak var arView: ARView?
        weak var viewModel: PuttReaderViewModel?
        var slopeAnchor: AnchorEntity?
        
        func session(_ session: ARSession, didUpdate frame: ARFrame) {
            guard let viewModel = viewModel, viewModel.isScanning else { return }
            
            // Process mesh anchors during scan
            if let meshAnchors = frame.anchors.compactMap({ $0 as? ARMeshAnchor }) as? [ARMeshAnchor] {
                processMeshAnchors(meshAnchors)
            }
        }
        
        func processMeshAnchors(_ anchors: [ARMeshAnchor]) {
            guard let viewModel = viewModel else { return }
            
            var allNormals: [SIMD3<Float>] = []
            
            for anchor in anchors {
                let geometry = anchor.geometry
                
                // Extract normals from mesh
                let normalsBuffer = geometry.normals
                let normalsPointer = normalsBuffer.buffer.contents().bindMemory(
                    to: SIMD3<Float>.self,
                    capacity: normalsBuffer.count
                )
                
                for i in 0..<normalsBuffer.count {
                    allNormals.append(normalsPointer[i])
                }
            }
            
            DispatchQueue.main.async {
                viewModel.meshNormals = allNormals
            }
        }
        
        func visualizeSlopeGradient(arView: ARView) {
            guard let viewModel = viewModel else { return }
            
            // Remove existing visualization
            if let existing = slopeAnchor {
                arView.scene.removeAnchor(existing)
            }
            
            // Create slope visualization anchor
            let anchor = AnchorEntity(plane: .horizontal)
            slopeAnchor = anchor
            
            // Create grid of indicators based on slope analysis
            let gridSize = 10
            let spacing: Float = 0.1
            
            for x in 0..<gridSize {
                for z in 0..<gridSize {
                    let xPos = Float(x - gridSize/2) * spacing
                    let zPos = Float(z - gridSize/2) * spacing
                    
                    // Determine color based on break direction
                    let color: UIColor
                    switch viewModel.breakDirection {
                    case .left:
                        color = UIColor.blue.withAlphaComponent(0.6)
                    case .right:
                        color = UIColor.red.withAlphaComponent(0.6)
                    case .straight:
                        color = UIColor.green.withAlphaComponent(0.6)
                    }
                    
                    // Create indicator sphere
                    let sphere = ModelEntity(
                        mesh: .generateSphere(radius: 0.015),
                        materials: [SimpleMaterial(color: color, isMetallic: false)]
                    )
                    sphere.position = SIMD3(xPos, 0, zPos)
                    anchor.addChild(sphere)
                }
            }
            
            // Add ideal putt line
            addPuttLine(to: anchor, viewModel: viewModel)
            
            arView.scene.addAnchor(anchor)
        }
        
        func addPuttLine(to anchor: AnchorEntity, viewModel: PuttReaderViewModel) {
            // Draw ideal putt line
            let linePoints = 20
            let breakDir: Float = viewModel.breakDirection == .left ? -1 : (viewModel.breakDirection == .right ? 1 : 0)
            
            for i in 0..<linePoints {
                let t = Float(i) / Float(linePoints - 1)
                let z = t * 2.0 - 1.0 // -1 to 1
                
                // Curved line showing break compensation
                let x = sin(t * .pi) * breakDir * 0.2
                
                let sphere = ModelEntity(
                    mesh: .generateSphere(radius: 0.02),
                    materials: [SimpleMaterial(color: .white, isMetallic: false)]
                )
                sphere.position = SIMD3(x, 0.01, z)
                anchor.addChild(sphere)
            }
        }
    }
}

#Preview {
    PuttReaderARView(onBack: {})
}
