import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, ImageBackground, ActivityIndicator, Animated, Easing } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useCameraPermissions } from 'expo-camera';
import Svg, { Path, Circle, Rect, G, Polygon } from 'react-native-svg';

// Screens
import SplashScreen from './SplashScreen';
import CalibrationScreen from './CalibrationScreen';
import CaptureScreen from './CaptureScreen';
import ShotSelector from './ARShotSelector';
import SearchZoneMap from './SearchZoneMap';
import CourseSelectScreen from './CourseSelectScreen';
import ActiveRoundScreen from './ActiveRoundScreen';
import StatsScreen from './StatsScreen';
import ProfileScreen from './ProfileScreen';
import RoundsScreen from './RoundsScreen';

const AnimatedPath = Animated.createAnimatedComponent(Path);

// Premium SVG Icon Components
const PlayGolfIcon = ({ size = 32, color = '#2E7D32' }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Rect x="48" y="15" width="4" height="60" fill={color} />
    <Polygon points="52,15 75,28 52,41" fill="#f44336" />
    <Circle cx="50" cy="80" r="12" fill={color} opacity="0.7" />
    <Path d="M 20 85 Q 50 75, 80 85" stroke={color} strokeWidth="3" fill="none" opacity="0.5" />
  </Svg>
);

const ShotTrackerIcon = ({ size = 32, color = '#2E7D32' }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Circle cx="50" cy="50" r="20" fill={color} opacity="0.9" />
    <Circle cx="50" cy="50" r="35" fill="none" stroke={color} strokeWidth="3" strokeDasharray="5,5" />
    <Path d="M 50 10 L 50 25" stroke={color} strokeWidth="3" strokeLinecap="round" />
    <Path d="M 50 75 L 50 90" stroke={color} strokeWidth="3" strokeLinecap="round" />
    <Path d="M 10 50 L 25 50" stroke={color} strokeWidth="3" strokeLinecap="round" />
    <Path d="M 75 50 L 90 50" stroke={color} strokeWidth="3" strokeLinecap="round" />
  </Svg>
);

const SettingsIcon = ({ size = 28, color = '#1B5E20' }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Circle cx="50" cy="50" r="15" fill="none" stroke={color} strokeWidth="6" />
    <Circle cx="50" cy="50" r="30" fill="none" stroke={color} strokeWidth="4" opacity="0.4" />
    <Circle cx="50" cy="15" r="6" fill={color} />
    <Circle cx="50" cy="85" r="6" fill={color} />
    <Circle cx="15" cy="50" r="6" fill={color} />
    <Circle cx="85" cy="50" r="6" fill={color} />
  </Svg>
);

// Navigation Icons
const HomeIcon = ({ size = 24, active }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Path
      d="M 50 20 L 20 50 L 30 50 L 30 80 L 70 80 L 70 50 L 80 50 Z"
      fill={active ? '#3FB950' : '#8B949E'}
    />
  </Svg>
);

const RoundsIcon = ({ size = 24, active }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Rect x="35" y="55" width="4" height="30" fill={active ? '#3FB950' : '#8B949E'} />
    <Polygon points="39,55 55,62 39,69" fill={active ? '#3FB950' : '#8B949E'} />
    <Circle cx="37" cy="30" r="15" fill="none" stroke={active ? '#3FB950' : '#8B949E'} strokeWidth="5" />
  </Svg>
);

const StatsIcon = ({ size = 24, active }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Rect x="20" y="60" width="15" height="25" fill={active ? '#3FB950' : '#8B949E'} />
    <Rect x="42" y="45" width="15" height="40" fill={active ? '#3FB950' : '#8B949E'} />
    <Rect x="64" y="30" width="15" height="55" fill={active ? '#3FB950' : '#8B949E'} />
  </Svg>
);

const ProfileIcon = ({ size = 24, active }) => (
  <Svg width={size} height={size} viewBox="0 0 100 100">
    <Circle cx="50" cy="35" r="18" fill={active ? '#3FB950' : '#8B949E'} />
    <Path d="M 20 85 Q 20 60, 50 60 T 80 85" fill={active ? '#3FB950' : '#8B949E'} />
  </Svg>
);

export default function App() {
  const [permission, requestPermission] = useCameraPermissions();
  const [currentScreen, setCurrentScreen] = useState('splash');
  const [analysisData, setAnalysisData] = useState(null);
  const [selectedShot, setSelectedShot] = useState(null);
  const [activeNav, setActiveNav] = useState('home');
  const [activeCourse, setActiveCourse] = useState(null);

  // Animation Refs
  const arcAnim = useRef(new Animated.Value(0)).current;
  const contentFadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (currentScreen === 'main') {
      // Reset animations
      arcAnim.setValue(0);
      contentFadeAnim.setValue(0);

      // Start animations sequence
      Animated.parallel([
        Animated.timing(arcAnim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.bezier(0.4, 0, 0.2, 1),
          useNativeDriver: true,
        }),
        Animated.timing(contentFadeAnim, {
          toValue: 1,
          duration: 1200,
          delay: 400,
          useNativeDriver: true,
        })
      ]).start();
    }
  }, [currentScreen]);

  // Navigation handlers
  const handleStartApp = () => setCurrentScreen('main');
  const handleOpenTracker = () => setCurrentScreen('capture');
  const handleOpenCalibration = () => setCurrentScreen('calibration');
  const handleCalibrationComplete = () => setCurrentScreen('main');
  const handleCaptureCancel = () => setCurrentScreen('main');

  // Course & Round handlers
  const handlePlayGolf = () => setCurrentScreen('courseselect');
  const handleStartRound = (course) => {
    setActiveCourse(course);
    setCurrentScreen('activeround');
  };
  const handleEndRound = () => {
    setActiveCourse(null);
    setCurrentScreen('main');
    setActiveNav('home');
  };

  const handleOpenStats = () => { setCurrentScreen('stats'); setActiveNav('stats'); };
  const handleOpenProfile = () => { setCurrentScreen('profile'); setActiveNav('profile'); };
  const handleOpenRounds = () => { setCurrentScreen('rounds'); setActiveNav('rounds'); };

  const handleBackToMain = () => { setCurrentScreen('main'); setActiveNav('home'); };

  const handleAnalysisComplete = (data) => {
    setAnalysisData(data);
    setCurrentScreen('selector');
  };

  const handleShotSelected = (shotKey, shotData) => {
    setSelectedShot({ key: shotKey, data: shotData });
    setCurrentScreen('map');
  };

  const handleSelectorCancel = () => {
    setCurrentScreen('main');
    setAnalysisData(null);
  };

  const handleMapComplete = () => {
    setCurrentScreen('main');
    setAnalysisData(null);
    setSelectedShot(null);
  };

  // Check permissions
  if (!permission) {
    return (
      <ImageBackground
        source={require('./assets/splash.png')}
        style={styles.background}
        resizeMode="cover"
      >
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#FFFFFF" />
        </View>
      </ImageBackground>
    );
  }

  if (!permission.granted) {
    return (
      <ImageBackground
        source={require('./assets/splash.png')}
        style={styles.background}
        resizeMode="cover"
      >
        <View style={styles.permissionContainer}>
          <View style={styles.permissionCard}>
            <Text style={styles.permissionTitle}>Camera Access Required</Text>
            <Text style={styles.permissionText}>
              Enable camera access to use the shot tracker
            </Text>
            <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
              <Text style={styles.permissionButtonText}>Grant Permission</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ImageBackground>
    );
  }

  // Screen routing
  if (currentScreen === 'splash') {
    return <SplashScreen onComplete={handleStartApp} />;
  }

  if (currentScreen === 'calibration') {
    return <CalibrationScreen onComplete={handleCalibrationComplete} onCancel={handleBackToMain} />;
  }

  if (currentScreen === 'capture') {
    return <CaptureScreen onAnalysisComplete={handleAnalysisComplete} onCancel={handleCaptureCancel} />;
  }

  if (currentScreen === 'selector' && analysisData) {
    return <ShotSelector analysisData={analysisData} onSelectShot={handleShotSelected} onCancel={handleSelectorCancel} />;
  }

  if (currentScreen === 'map' && selectedShot) {
    return <SearchZoneMap shotData={selectedShot.data} onComplete={handleMapComplete} />;
  }

  if (currentScreen === 'courseselect') {
    return <CourseSelectScreen onBack={handleBackToMain} onStartRound={handleStartRound} />;
  }

  if (currentScreen === 'activeround' && activeCourse) {
    return <ActiveRoundScreen course={activeCourse} onEndRound={handleEndRound} />;
  }

  if (currentScreen === 'stats') {
    return <StatsScreen onBack={handleBackToMain} />;
  }

  if (currentScreen === 'profile') {
    return <ProfileScreen onBack={handleBackToMain} />;
  }

  if (currentScreen === 'rounds') {
    return <RoundsScreen onBack={handleBackToMain} onStartRound={handlePlayGolf} />;
  }

  // Main Golf App Dashboard
  return (
    <ImageBackground
      source={require('./assets/splash.png')}
      style={styles.background}
      resizeMode="cover"
    >
      <StatusBar style="light" />
      <View style={styles.overlay} />

      {/* Animated Arch Element */}
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <Svg width="100%" height="100%" viewBox="0 0 400 800">
          <AnimatedPath
            d="M -50,450 Q 200,300 450,450"
            fill="none"
            stroke="rgba(63, 185, 80, 0.4)"
            strokeWidth="2"
            strokeDasharray="1000"
            strokeDashoffset={arcAnim.interpolate({
              inputRange: [0, 1],
              outputRange: [1000, 0]
            })}
          />
          <AnimatedPath
            d="M -50,470 Q 200,320 450,470"
            fill="none"
            stroke="rgba(63, 185, 80, 0.2)"
            strokeWidth="1"
            strokeDasharray="1000"
            strokeDashoffset={arcAnim.interpolate({
              inputRange: [0, 1],
              outputRange: [1000, 0]
            })}
          />
        </Svg>
      </View>

      <Animated.View style={{ flex: 1, opacity: contentFadeAnim }}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>LinksAI</Text>
          <Text style={styles.headerSubtitle}>Smart Golf, Powered by AR</Text>
        </View>

        {/* Main Content */}
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>

          {/* Hero Section - Play Golf */}
          <View style={styles.heroSection}>
            <Text style={styles.heroTitle}>TEE OFF</Text>
            <Text style={styles.heroSubtitle}>Elevate Your Game</Text>
          </View>

          {/* Start Round Button */}
          <View style={styles.buttonSection}>
            <TouchableOpacity
              style={styles.heroButton}
              onPress={handlePlayGolf}
              activeOpacity={0.85}
            >
              <Text style={styles.heroButtonText}>START YOUR ROUND</Text>
            </TouchableOpacity>
          </View>

          {/* Quick Stats */}
          <View style={styles.statsRow}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>--</Text>
              <Text style={styles.statLabel}>HANDICAP</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>0</Text>
              <Text style={styles.statLabel}>ROUNDS</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>--</Text>
              <Text style={styles.statLabel}>AVG SCORE</Text>
            </View>
          </View>

          {/* Secondary Features */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>PRACTICE TOOLS</Text>

            <TouchableOpacity style={styles.featureCard} onPress={handleOpenTracker}>
              <View style={styles.featureRow}>
                <View style={styles.featureIconBox}>
                  <ShotTrackerIcon size={40} color="#2E7D32" />
                </View>
                <View style={styles.featureInfo}>
                  <Text style={styles.featureTitle}>Range Shot Tracker</Text>
                  <Text style={styles.featureSubtitle}>
                    Track shots on the practice range with AI ball detection
                  </Text>
                </View>
                <Text style={styles.featureArrow}>›</Text>
              </View>
            </TouchableOpacity>

            <TouchableOpacity style={styles.featureCard} onPress={handleOpenCalibration}>
              <View style={styles.featureRow}>
                <View style={styles.featureIconBox}>
                  <SettingsIcon size={40} color="#2E7D32" />
                </View>
                <View style={styles.featureInfo}>
                  <Text style={styles.featureTitle}>Settings</Text>
                  <Text style={styles.featureSubtitle}>
                    Configure camera, clubs, and preferences
                  </Text>
                </View>
                <Text style={styles.featureArrow}>›</Text>
              </View>
            </TouchableOpacity>
          </View>

          <View style={{ height: 100 }} />
        </ScrollView>

        {/* Bottom Navigation */}
        <View style={styles.bottomNav}>
          <TouchableOpacity style={styles.navItem} onPress={handleBackToMain}>
            <HomeIcon size={26} active={activeNav === 'home'} />
            <Text style={activeNav === 'home' ? styles.navTextActive : styles.navText}>Home</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.navItem} onPress={handleOpenRounds}>
            <RoundsIcon size={26} active={activeNav === 'rounds'} />
            <Text style={activeNav === 'rounds' ? styles.navTextActive : styles.navText}>Rounds</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.navItemCenter} onPress={handlePlayGolf}>
            <View style={styles.navCenterButton}>
              <PlayGolfIcon size={36} color="#FFFFFF" />
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.navItem} onPress={handleOpenStats}>
            <StatsIcon size={26} active={activeNav === 'stats'} />
            <Text style={activeNav === 'stats' ? styles.navTextActive : styles.navText}>Stats</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.navItem} onPress={handleOpenProfile}>
            <ProfileIcon size={26} active={activeNav === 'profile'} />
            <Text style={activeNav === 'profile' ? styles.navTextActive : styles.navText}>Profile</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.55)',
  },
  loadingOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
  },
  permissionCard: {
    backgroundColor: '#161B22',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#21262D',
  },
  permissionTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#F0F6FC',
    marginBottom: 15,
  },
  permissionText: {
    fontSize: 15,
    color: '#8B949E',
    textAlign: 'center',
    marginBottom: 25,
    lineHeight: 22,
  },
  permissionButton: {
    backgroundColor: '#238636',
    paddingHorizontal: 36,
    paddingVertical: 14,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  header: {
    paddingTop: 65,
    paddingBottom: 16,
    paddingHorizontal: 24,
  },
  headerTitle: {
    color: '#FFFFFF',
    fontSize: 34,
    fontWeight: '200',
    letterSpacing: 12,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 6,
  },
  headerSubtitle: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 10,
    marginTop: 4,
    letterSpacing: 5,
    fontWeight: '200',
    textTransform: 'uppercase',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 24,
    paddingTop: 0,
  },
  // Hero Section - Text above the ball
  heroSection: {
    alignItems: 'center',
    paddingTop: 65,
    marginBottom: 120,
  },
  heroTitle: {
    fontSize: 52,
    fontWeight: '200',
    color: '#FFFFFF',
    letterSpacing: 12,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 10,
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.65)',
    letterSpacing: 2,
    fontWeight: '300',
    fontStyle: 'italic',
  },
  // Button Section - below the ball
  buttonSection: {
    alignItems: 'center',
    marginBottom: 28,
  },
  heroButton: {
    backgroundColor: 'rgba(35, 134, 54, 0.85)',
    paddingHorizontal: 52,
    paddingVertical: 16,
    borderRadius: 30,
    borderWidth: 1,
    borderColor: 'rgba(63, 185, 80, 0.5)',
    shadowColor: '#238636',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
  },
  heroButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 2,
  },
  // Stats Row
  statsRow: {
    flexDirection: 'row',
    marginBottom: 32,
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: 'rgba(22, 27, 34, 0.7)',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(48, 54, 61, 0.6)',
  },
  statValue: {
    color: '#F0F6FC',
    fontSize: 24,
    fontWeight: '700',
  },
  statLabel: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 1,
    marginTop: 4,
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: 'rgba(255, 255, 255, 0.5)',
    marginBottom: 14,
    letterSpacing: 1.5,
  },
  featureCard: {
    backgroundColor: 'rgba(22, 27, 34, 0.9)',
    borderRadius: 14,
    padding: 18,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(48, 54, 61, 0.8)',
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  featureIconBox: {
    width: 52,
    height: 52,
    borderRadius: 12,
    backgroundColor: 'rgba(35, 134, 54, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  featureInfo: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#F0F6FC',
    marginBottom: 4,
  },
  featureSubtitle: {
    fontSize: 13,
    color: '#8B949E',
    lineHeight: 18,
  },
  featureArrow: {
    fontSize: 26,
    color: '#3FB950',
    marginLeft: 8,
    fontWeight: '300',
  },
  bottomNav: {
    flexDirection: 'row',
    paddingVertical: 10,
    paddingBottom: 30,
    borderTopWidth: 1,
    borderTopColor: 'rgba(48, 54, 61, 0.6)',
    backgroundColor: 'rgba(13, 17, 23, 0.97)',
  },
  navItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 6,
  },
  navItemCenter: {
    flex: 1,
    alignItems: 'center',
    marginTop: -26,
  },
  navTextActive: {
    fontSize: 10,
    color: '#3FB950',
    fontWeight: '600',
    marginTop: 4,
  },
  navText: {
    fontSize: 10,
    color: '#8B949E',
    marginTop: 4,
  },
  navCenterButton: {
    width: 62,
    height: 62,
    borderRadius: 31,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#0D1117',
    backgroundColor: '#238636',
    shadowColor: '#238636',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 12,
  },
});
