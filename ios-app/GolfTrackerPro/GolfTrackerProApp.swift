import SwiftUI
import ARKit
import RealityKit
import CoreML
import Vision

// MARK: - Main App Entry
@main
struct GolfTrackerProApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

// MARK: - Content View
struct ContentView: View {
    @State private var currentMode: AppMode = .home
    
    var body: some View {
        ZStack {
            switch currentMode {
            case .home:
                HomeView(onSelectMode: { mode in
                    currentMode = mode
                })
            case .shotTracker:
                ShotTrackerARView(onBack: { currentMode = .home })
            case .puttReader:
                PuttReaderARView(onBack: { currentMode = .home })
            }
        }
        .preferredColorScheme(.dark)
    }
}

enum AppMode {
    case home
    case shotTracker
    case puttReader
}

// MARK: - Home View
struct HomeView: View {
    let onSelectMode: (AppMode) -> Void
    
    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                colors: [Color(hex: "1B5E20"), Color(hex: "0D3010")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack(spacing: 30) {
                // Header
                VStack(spacing: 8) {
                    Text("LinksAI")
                        .font(.system(size: 36, weight: .bold))
                        .foregroundColor(.white)
                    
                    Text("AI-Powered Golf Companion")
                        .font(.system(size: 16))
                        .foregroundColor(.white.opacity(0.7))
                }
                .padding(.top, 60)
                
                Spacer()
                
                // Feature Cards
                VStack(spacing: 20) {
                    FeatureCard(
                        icon: "scope",
                        title: "AI Shot Tracker",
                        subtitle: "Real-time ball tracking with AR trajectory overlay",
                        badge: "60 FPS",
                        action: { onSelectMode(.shotTracker) }
                    )
                    
                    FeatureCard(
                        icon: "chart.line.downtrend.xyaxis",
                        title: "Putt Reader",
                        subtitle: "LiDAR-powered green analysis with break visualization",
                        badge: "LiDAR",
                        action: { onSelectMode(.puttReader) }
                    )
                }
                .padding(.horizontal, 20)
                
                Spacer()
                
                // Footer
                Text("Requires iPhone Pro for LiDAR features")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.5))
                    .padding(.bottom, 30)
            }
        }
    }
}

// MARK: - Feature Card
struct FeatureCard: View {
    let icon: String
    let title: String
    let subtitle: String
    let badge: String
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                // Icon
                ZStack {
                    Circle()
                        .fill(Color.white.opacity(0.15))
                        .frame(width: 60, height: 60)
                    
                    Image(systemName: icon)
                        .font(.system(size: 26))
                        .foregroundColor(.white)
                }
                
                // Text
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(title)
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(.white)
                        
                        Text(badge)
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(Color(hex: "1B5E20"))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color(hex: "FFD600"))
                            .cornerRadius(10)
                    }
                    
                    Text(subtitle)
                        .font(.system(size: 13))
                        .foregroundColor(.white.opacity(0.7))
                        .lineLimit(2)
                }
                
                Spacer()
                
                Image(systemName: "chevron.right")
                    .foregroundColor(.white.opacity(0.5))
            }
            .padding(20)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.white.opacity(0.1))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(Color.white.opacity(0.2), lineWidth: 1)
                    )
            )
        }
    }
}

// MARK: - Color Extension
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB, red: Double(r) / 255, green: Double(g) / 255, blue: Double(b) / 255, opacity: Double(a) / 255)
    }
}
