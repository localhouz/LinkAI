import React, { useState, useRef, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, ActivityIndicator, Image } from 'react-native';
import { CameraView } from 'expo-camera';
import * as Location from 'expo-location';
import { Magnetometer, Gyroscope } from 'expo-sensors';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import axios from 'axios';

const API_URL = 'http://192.168.1.168:5000';

export default function CaptureScreen({ onAnalysisComplete, onCancel }) {
    const [isRecording, setIsRecording] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [countdown, setCountdown] = useState(null);
    const [gpsData, setGpsData] = useState(null);
    const [compassHeading, setCompassHeading] = useState(0);
    const [gyroTilt, setGyroTilt] = useState(0);
    const [capturedCount, setCapturedCount] = useState(0);
    const [isMounted, setIsMounted] = useState(true);
    const [showOnboarding, setShowOnboarding] = useState(true);
    const [trackingMode, setTrackingMode] = useState('tripod'); // 'tripod' | 'cart'

    const cameraRef = useRef(null);
    const framesRef = useRef([]);
    const magnetometerSubscription = useRef(null);
    const gyroscopeSubscription = useRef(null);

    useEffect(() => {
        setIsMounted(true);

        // Get GPS location
        (async () => {
            try {
                const { status } = await Location.requestForegroundPermissionsAsync();
                if (status === 'granted') {
                    const location = await Location.getCurrentPositionAsync({});
                    setGpsData({
                        lat: location.coords.latitude,
                        lon: location.coords.longitude
                    });
                }
            } catch (error) {
                console.error('GPS error:', error);
            }
        })();

        // Subscribe to magnetometer
        try {
            magnetometerSubscription.current = Magnetometer.addListener((data) => {
                const { x, y } = data;
                let heading = Math.atan2(y, x) * (180 / Math.PI);
                heading = (heading + 360) % 360;
                setCompassHeading(heading);
            });
            Magnetometer.setUpdateInterval(100);
        } catch (error) {
            console.error('Magnetometer error:', error);
        }

        // Subscribe to gyroscope
        try {
            gyroscopeSubscription.current = Gyroscope.addListener((data) => {
                const tilt = Math.abs(data.x) * (180 / Math.PI);
                setGyroTilt(tilt);
            });
            Gyroscope.setUpdateInterval(100);
        } catch (error) {
            console.error('Gyroscope error:', error);
        }

        return () => {
            setIsMounted(false);
            magnetometerSubscription.current?.remove();
            gyroscopeSubscription.current?.remove();
        };
    }, []);

    const startCountdown = () => {
        let count = 3;
        setCountdown(count);

        const countdownInterval = setInterval(() => {
            count--;
            if (count === 0) {
                clearInterval(countdownInterval);
                setCountdown(null);
                setTimeout(startRecording, 100);
            } else {
                setCountdown(count);
            }
        }, 1000);
    };

    const startRecording = async () => {
        if (!isMounted || !cameraRef.current) {
            Alert.alert('Error', 'Camera not ready');
            return;
        }

        setIsRecording(true);
        framesRef.current = [];
        setCapturedCount(0);
        const maxFrames = 6; // Only 6 frames for reliability

        try {
            // Capture frames SEQUENTIALLY with delays to prevent unmount errors
            for (let i = 0; i < maxFrames; i++) {
                if (!isMounted || !cameraRef.current) {
                    console.log('Stopped - component unmounted');
                    break;
                }

                try {
                    // Wait a bit before each capture
                    if (i > 0) {
                        await new Promise(resolve => setTimeout(resolve, 150));
                    }

                    const photo = await cameraRef.current.takePictureAsync({
                        quality: 0.15,  // Very low quality for speed
                        base64: true,
                        skipProcessing: true,
                    });

                    if (photo && photo.base64) {
                        framesRef.current.push(photo.base64);
                        setCapturedCount(i + 1);
                        console.log(`Captured frame ${i + 1}/${maxFrames}`);
                    }
                } catch (frameError) {
                    console.log(`Frame ${i + 1} skip:`, frameError.message);
                    // Continue to next frame
                }
            }

            console.log(`Total frames captured: ${framesRef.current.length}`);
        } catch (error) {
            console.error('Recording error:', error);
        }

        setIsRecording(false);

        // Wait a moment then analyze
        setTimeout(() => {
            if (isMounted) {
                analyzeShot();
            }
        }, 200);
    };

    const analyzeShot = async () => {
        const capturedFrames = framesRef.current;

        if (capturedFrames.length < 3) {
            Alert.alert('Error', `Only captured ${capturedFrames.length} frames. Need at least 3. Try again.`);
            return;
        }

        if (!gpsData) {
            Alert.alert('Error', 'GPS location not available');
            return;
        }

        setIsAnalyzing(true);

        try {
            console.log(`Sending ${capturedFrames.length} frames to ${API_URL}...`);

            const response = await axios.post(`${API_URL}/api/analyze_shot`, {
                frames: capturedFrames,
                gps: gpsData,
                compass_heading: compassHeading,
                gyro_tilt: gyroTilt,
                tracking_mode: trackingMode
            }, {
                timeout: 90000,  // 90 seconds
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            console.log('Server response received');

            if (response.data) {
                onAnalysisComplete(response.data);
            } else {
                Alert.alert('Error', 'No data from server');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            let errorMessage = 'Server error';

            if (error.code === 'ECONNABORTED') {
                errorMessage = 'Timeout: Server took too long (>90s). Check server logs.';
            } else if (error.response) {
                errorMessage = error.response.data?.error || error.message;
            } else if (error.request) {
                errorMessage = `Cannot connect to ${API_URL}. Is the server running?`;
            } else {
                errorMessage = error.message;
            }

            Alert.alert('Analysis Failed', errorMessage);
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <View style={styles.container}>
            <CameraView
                style={styles.camera}
                ref={cameraRef}
                facing="back"
            />

            {showOnboarding && (
                <View style={styles.onboardingOverlay}>
                    <View style={styles.onboardingCard}>
                        <Text style={styles.onboardingTitle}>AR SETUP GUIDE</Text>

                        {/* Mode Toggle */}
                        <View style={styles.modeToggleContainer}>
                            <TouchableOpacity
                                style={[styles.modeTab, trackingMode === 'tripod' && styles.modeTabActive]}
                                onPress={() => setTrackingMode('tripod')}
                            >
                                <MaterialCommunityIcons
                                    name="cellphone"
                                    size={20}
                                    color={trackingMode === 'tripod' ? '#FFFFFF' : '#8B949E'}
                                    style={{ marginRight: 8 }}
                                />
                                <Text style={[styles.modeTabText, trackingMode === 'tripod' && styles.modeTabTextActive]}>TRIPOD (DTL)</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={[styles.modeTab, trackingMode === 'cart' && styles.modeTabActive]}
                                onPress={() => setTrackingMode('cart')}
                            >
                                <MaterialCommunityIcons
                                    name="golf-cart"
                                    size={22}
                                    color={trackingMode === 'cart' ? '#FFFFFF' : '#8B949E'}
                                    style={{ marginRight: 8 }}
                                />
                                <Text style={[styles.modeTabText, trackingMode === 'cart' && styles.modeTabTextActive]}>CART (SIDE)</Text>
                            </TouchableOpacity>
                        </View>

                        <Image
                            source={trackingMode === 'tripod'
                                ? require('./assets/ar_setup_guide.png')
                                : require('./assets/ar_cart_setup_guide.png')}
                            style={styles.setupImage}
                            resizeMode="cover"
                        />

                        <View style={styles.onboardingSteps}>
                            {trackingMode === 'tripod' ? (
                                <>
                                    <View style={styles.onboardingStep}>
                                        <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>1</Text></View>
                                        <Text style={styles.stepText}>Position phone 6-8 feet directly behind the ball.</Text>
                                    </View>
                                    <View style={styles.onboardingStep}>
                                        <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>2</Text></View>
                                        <Text style={styles.stepText}>Align the red target dot with your golf ball.</Text>
                                    </View>
                                </>
                            ) : (
                                <>
                                    <View style={styles.onboardingStep}>
                                        <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>1</Text></View>
                                        <Text style={styles.stepText}>Mount phone to cart pillar or dash (viewing side-on).</Text>
                                    </View>
                                    <View style={styles.onboardingStep}>
                                        <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>2</Text></View>
                                        <Text style={styles.stepText}>Ensure ball is in the center of the reticle at address.</Text>
                                    </View>
                                </>
                            )}
                            <View style={styles.onboardingStep}>
                                <View style={styles.stepBadge}><Text style={styles.stepBadgeText}>3</Text></View>
                                <Text style={styles.stepText}>Lock target and swing after the countdown.</Text>
                            </View>
                        </View>

                        <TouchableOpacity
                            style={styles.onboardingBtn}
                            onPress={() => setShowOnboarding(false)}
                        >
                            <Text style={styles.onboardingBtnText}>START AR LENS</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            )}

            <View style={styles.overlay}>
                {/* Live AR HUD - Reticle */}
                <View style={styles.reticleContainer}>
                    <View style={styles.reticleCornerTopLeft} />
                    <View style={styles.reticleCornerTopRight} />
                    <View style={styles.reticleCornerBottomLeft} />
                    <View style={styles.reticleCornerBottomRight} />
                    <View style={styles.reticleCenter} />
                </View>

                <View style={styles.statusBox}>
                    <View style={styles.liveIndicator}>
                        <MaterialCommunityIcons name="broadcast" size={16} color="#3FB950" style={{ marginRight: 6 }} />
                        <Text style={styles.liveText}>LIVE AR SCANNING</Text>
                    </View>

                    <Text style={styles.statusText}>
                        {isRecording ? `LOCKING TRACK ${capturedCount}/6` :
                            isAnalyzing ? 'AI PROCESSING...' :
                                countdown ? `IMPACT IN ${countdown}` :
                                    'AR LENS ACTIVE'}
                    </Text>

                    {gpsData && (
                        <Text style={styles.infoText}>
                            GPS: {gpsData.lat.toFixed(4)}, {gpsData.lon.toFixed(4)}
                        </Text>
                    )}

                    <Text style={styles.infoText}>
                        Heading: {compassHeading.toFixed(0)}° | Tilt: {gyroTilt.toFixed(1)}°
                    </Text>
                </View>

                {countdown && (
                    <View style={styles.countdownOverlay}>
                        <Text style={styles.countdownText}>{countdown}</Text>
                    </View>
                )}

                {isAnalyzing && (
                    <View style={styles.loadingOverlay}>
                        <ActivityIndicator size="large" color="#00B4D8" />
                        <Text style={styles.loadingText}>Analyzing...</Text>
                        <Text style={styles.loadingSubtext}>May take up to 90 seconds</Text>
                    </View>
                )}

                {!isRecording && !isAnalyzing && !countdown && (
                    <View style={styles.controls}>
                        <TouchableOpacity
                            style={[styles.recordButton, !gpsData && styles.disabledButton]}
                            onPress={startCountdown}
                            disabled={!gpsData}
                        >
                            <View style={styles.arButtonContent}>
                                <MaterialCommunityIcons
                                    name={gpsData ? "target" : "crosshairs-question"}
                                    size={24}
                                    color="#FFFFFF"
                                    style={{ marginRight: 10 }}
                                />
                                <Text style={styles.recordButtonText}>
                                    {gpsData ? 'LOCK SHOT TARGET' : 'CALIBRATING GPS...'}
                                </Text>
                            </View>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={styles.cancelButton}
                            onPress={onCancel}
                        >
                            <Ionicons name="close-circle-outline" size={20} color="#8B949E" style={{ marginRight: 6 }} />
                            <Text style={styles.cancelButtonText}>Cancel</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {!isRecording && !isAnalyzing && !countdown && (
                    <View style={styles.instructions}>
                        <Text style={styles.instructionText}>
                            Align reticle with ball position{'\n'}
                            Tap LOCK SHOT TARGET{'\n'}
                            Maintain steady aim through impact
                        </Text>
                    </View>
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
    },
    camera: {
        flex: 1,
    },
    overlay: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'space-between',
        paddingVertical: 50,
        paddingHorizontal: 20,
    },
    statusBox: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    statusText: {
        color: '#fff',
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 8,
    },
    infoText: {
        color: '#aaa',
        fontSize: 11,
        marginTop: 4,
    },
    countdownOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    countdownText: {
        color: '#00B4D8',
        fontSize: 120,
        fontWeight: 'bold',
    },
    loadingOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0, 0, 0, 0.92)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        color: '#fff',
        fontSize: 20,
        marginTop: 20,
        fontWeight: '600',
    },
    loadingSubtext: {
        color: '#aaa',
        fontSize: 14,
        marginTop: 10,
    },
    controls: {
        alignItems: 'center',
        marginBottom: 50,
    },
    recordButton: {
        backgroundColor: '#00B4D8',
        paddingHorizontal: 50,
        paddingVertical: 20,
        borderRadius: 50,
        marginBottom: 20,
        shadowColor: '#00B4D8',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.5,
        shadowRadius: 8,
        elevation: 8,
    },
    disabledButton: {
        backgroundColor: '#555',
        shadowOpacity: 0,
    },
    recordButtonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
        letterSpacing: 0.5,
    },
    cancelButton: {
        paddingVertical: 12,
    },
    cancelButtonText: {
        color: '#fff',
        fontSize: 16,
    },
    instructions: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 16,
        borderRadius: 12,
    },
    instructionText: {
        color: '#fff',
        fontSize: 14,
        lineHeight: 24,
        textAlign: 'center',
    },
    reticleContainer: {
        position: 'absolute',
        top: '25%',
        left: '10%',
        right: '10%',
        bottom: '35%',
        justifyContent: 'center',
        alignItems: 'center',
        pointerEvents: 'none',
    },
    reticleCornerTopLeft: {
        position: 'absolute',
        top: 0,
        left: 0,
        width: 40,
        height: 40,
        borderLeftWidth: 2,
        borderTopWidth: 2,
        borderColor: '#00B4D8',
    },
    reticleCornerTopRight: {
        position: 'absolute',
        top: 0,
        right: 0,
        width: 40,
        height: 40,
        borderRightWidth: 2,
        borderTopWidth: 2,
        borderColor: '#00B4D8',
    },
    reticleCornerBottomLeft: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        width: 40,
        height: 40,
        borderLeftWidth: 2,
        borderBottomWidth: 2,
        borderColor: '#00B4D8',
    },
    reticleCornerBottomRight: {
        position: 'absolute',
        bottom: 0,
        right: 0,
        width: 40,
        height: 40,
        borderRightWidth: 2,
        borderBottomWidth: 2,
        borderColor: '#00B4D8',
    },
    reticleCenter: {
        width: 4,
        height: 4,
        borderRadius: 2,
        backgroundColor: '#F85149',
    },
    liveIndicator: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 4,
        borderWidth: 1,
        borderColor: 'rgba(63, 185, 80, 0.3)',
    },
    liveDot: {
        width: 6,
        height: 6,
        borderRadius: 3,
        backgroundColor: '#3FB950',
        marginRight: 6,
    },
    liveText: {
        color: '#3FB950',
        fontSize: 10,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
    arButtonContent: {
        alignItems: 'center',
        justifyContent: 'center',
    },
    // Onboarding Styles
    onboardingOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
        zIndex: 1000,
    },
    onboardingCard: {
        backgroundColor: '#161B22',
        borderRadius: 20,
        width: '100%',
        maxWidth: 340,
        padding: 24,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#30363D',
    },
    onboardingTitle: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
        letterSpacing: 2,
        marginBottom: 20,
    },
    modeToggleContainer: {
        flexDirection: 'row',
        backgroundColor: '#0D1117',
        borderRadius: 8,
        padding: 4,
        marginBottom: 20,
        width: '100%',
    },
    modeTab: {
        flex: 1,
        paddingVertical: 8,
        alignItems: 'center',
        borderRadius: 6,
    },
    modeTabActive: {
        backgroundColor: '#21262D',
        borderWidth: 1,
        borderColor: '#30363D',
    },
    modeTabText: {
        color: '#8B949E',
        fontSize: 10,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
    modeTabTextActive: {
        color: '#3FB950',
    },
    setupImage: {
        width: '100%',
        height: 180,
        borderRadius: 12,
        marginBottom: 24,
        backgroundColor: '#0D1117',
    },
    onboardingSteps: {
        width: '100%',
        marginBottom: 30,
    },
    onboardingStep: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 16,
    },
    stepBadge: {
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: '#238636',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 12,
    },
    stepBadgeText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
    },
    stepText: {
        color: '#8B949E',
        fontSize: 13,
        flex: 1,
        lineHeight: 18,
    },
    onboardingBtn: {
        backgroundColor: '#238636',
        width: '100%',
        paddingVertical: 14,
        borderRadius: 10,
        alignItems: 'center',
    },
    onboardingBtnText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
});
