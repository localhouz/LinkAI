import React, { useState, useRef } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert, Animated } from 'react-native';
import { CameraView } from 'expo-camera';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

export default function CalibrationScreen({ onComplete, onCancel }) {
    const [isDetecting, setIsDetecting] = useState(false);
    const [detectionCount, setDetectionCount] = useState(0);
    const [ballPosition, setBallPosition] = useState(null);

    const cameraRef = useRef(null);
    const pulseAnim = useRef(new Animated.Value(1)).current;

    // Pulse animation for detection indicator
    React.useEffect(() => {
        if (isDetecting) {
            Animated.loop(
                Animated.sequence([
                    Animated.timing(pulseAnim, {
                        toValue: 1.3,
                        duration: 800,
                        useNativeDriver: true,
                    }),
                    Animated.timing(pulseAnim, {
                        toValue: 1,
                        duration: 800,
                        useNativeDriver: true,
                    }),
                ])
            ).start();
        }
    }, [isDetecting]);

    const handleStartTest = () => {
        setIsDetecting(true);
        setDetectionCount(0);

        // Simulate ball detection for demo
        let count = 0;
        const interval = setInterval(() => {
            count++;
            setDetectionCount(count);

            // Simulate random ball position
            setBallPosition({
                x: 0.3 + Math.random() * 0.4,
                y: 0.3 + Math.random() * 0.4,
            });

            if (count >= 30) {
                clearInterval(interval);
                setIsDetecting(false);
                Alert.alert(
                    'Calibration Test Complete!',
                    `Detected ball in ${count} frames.\n\nCamera is working correctly.`,
                    [{ text: 'OK', onPress: onComplete }]
                );
            }
        }, 100);
    };

    const handleSkip = () => {
        Alert.alert(
            'Skip Calibration?',
            'Camera calibration helps ensure accurate ball detection. You can always test it later.',
            [
                { text: 'Continue Testing', style: 'cancel' },
                { text: 'Skip', onPress: onComplete }
            ]
        );
    };

    return (
        <View style={styles.container}>
            <CameraView style={styles.camera} ref={cameraRef} facing="back" />

            {/* Overlay UI */}
            <View style={styles.overlay}>
                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.title}>Camera Calibration</Text>
                    <Text style={styles.subtitle}>Test ball detection accuracy</Text>
                </View>

                {/* Crosshair/Target Area */}
                <View style={styles.targetContainer}>
                    <View style={styles.targetBox}>
                        {/* Corner brackets */}
                        <View style={[styles.corner, styles.topLeft]} />
                        <View style={[styles.corner, styles.topRight]} />
                        <View style={[styles.corner, styles.bottomLeft]} />
                        <View style={[styles.corner, styles.bottomRight]} />

                        {/* Center crosshair */}
                        <View style={styles.crosshair}>
                            <View style={styles.crosshairH} />
                            <View style={styles.crosshairV} />
                        </View>

                        {/* Detection indicator */}
                        {isDetecting && ballPosition && (
                            <Animated.View
                                style={[
                                    styles.detectionDot,
                                    {
                                        left: `${ballPosition.x * 100}%`,
                                        top: `${ballPosition.y * 100}%`,
                                        transform: [{ scale: pulseAnim }],
                                    }
                                ]}
                            />
                        )}
                    </View>

                    {!isDetecting ? (
                        <Text style={styles.instruction}>
                            Place a golf ball in the target area
                        </Text>
                    ) : (
                        <View style={styles.statusBox}>
                            <View style={styles.statusRow}>
                                <Ionicons name="checkmark-circle" size={18} color="#FFFFFF" style={{ marginRight: 6 }} />
                                <Text style={styles.statusText}>
                                    Detecting... {detectionCount}/30
                                </Text>
                            </View>
                        </View>
                    )}
                </View>

                {/* Info Cards */}
                <View style={styles.infoCards}>
                    <View style={styles.infoCard}>
                        <Ionicons name="camera" size={28} color="#00B4D8" />
                        <Text style={styles.infoTitle}>Camera Check</Text>
                        <Text style={styles.infoText}>Tests if camera can see the ball</Text>
                    </View>

                    <View style={styles.infoCard}>
                        <MaterialCommunityIcons name="target" size={28} color="#00B4D8" />
                        <Text style={styles.infoTitle}>Detection Test</Text>
                        <Text style={styles.infoText}>Verifies tracking accuracy</Text>
                    </View>
                </View>

                {/* Controls */}
                <View style={styles.controls}>
                    {!isDetecting ? (
                        <>
                            <TouchableOpacity
                                style={styles.primaryButton}
                                onPress={handleStartTest}
                            >
                                <Text style={styles.primaryButtonText}>START TEST</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.secondaryButton}
                                onPress={handleSkip}
                            >
                                <Text style={styles.secondaryButtonText}>Skip Calibration</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.tertiaryButton}
                                onPress={onCancel}
                            >
                                <Text style={styles.tertiaryButtonText}>Back</Text>
                            </TouchableOpacity>
                        </>
                    ) : (
                        <View style={styles.testingInfo}>
                            <Text style={styles.testingText}>
                                Testing camera... Keep ball in frame
                            </Text>
                        </View>
                    )}
                </View>
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
    header: {
        alignItems: 'center',
        paddingTop: 10,
    },
    title: {
        color: '#FFFFFF',
        fontSize: 26,
        fontWeight: 'bold',
        marginBottom: 6,
    },
    subtitle: {
        color: '#00B4D8',
        fontSize: 15,
    },
    targetContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    targetBox: {
        width: 280,
        height: 280,
        position: 'relative',
    },
    corner: {
        position: 'absolute',
        width: 40,
        height: 40,
        borderColor: '#00B4D8',
    },
    topLeft: {
        top: 0,
        left: 0,
        borderTopWidth: 3,
        borderLeftWidth: 3,
    },
    topRight: {
        top: 0,
        right: 0,
        borderTopWidth: 3,
        borderRightWidth: 3,
    },
    bottomLeft: {
        bottom: 0,
        left: 0,
        borderBottomWidth: 3,
        borderLeftWidth: 3,
    },
    bottomRight: {
        bottom: 0,
        right: 0,
        borderBottomWidth: 3,
        borderRightWidth: 3,
    },
    crosshair: {
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: 60,
        height: 60,
        marginLeft: -30,
        marginTop: -30,
    },
    crosshairH: {
        position: 'absolute',
        top: '50%',
        left: 0,
        right: 0,
        height: 2,
        backgroundColor: '#00B4D8',
        opacity: 0.5,
    },
    crosshairV: {
        position: 'absolute',
        left: '50%',
        top: 0,
        bottom: 0,
        width: 2,
        backgroundColor: '#00B4D8',
        opacity: 0.5,
    },
    detectionDot: {
        position: 'absolute',
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: '#00e676',
        borderWidth: 3,
        borderColor: '#FFFFFF',
        marginLeft: -12,
        marginTop: -12,
    },
    instruction: {
        color: '#FFFFFF',
        fontSize: 16,
        marginTop: 30,
        textAlign: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        paddingVertical: 12,
        paddingHorizontal: 20,
        borderRadius: 20,
    },
    statusBox: {
        backgroundColor: 'rgba(0, 230, 118, 0.9)',
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 20,
        marginTop: 30,
    },
    statusRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    statusText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    infoCards: {
        flexDirection: 'row',
        gap: 12,
        marginBottom: 20,
    },
    infoCard: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 14,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#2A2A2A',
        alignItems: 'center',
    },
    infoIcon: {
        fontSize: 28,
        marginBottom: 6,
    },
    infoTitle: {
        color: '#00B4D8',
        fontSize: 13,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    infoText: {
        color: '#AAAAAA',
        fontSize: 11,
        textAlign: 'center',
    },
    controls: {
        gap: 12,
    },
    primaryButton: {
        backgroundColor: '#00B4D8',
        paddingVertical: 18,
        borderRadius: 12,
        alignItems: 'center',
        shadowColor: '#00B4D8',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.5,
        shadowRadius: 8,
        elevation: 8,
    },
    primaryButtonText: {
        color: '#FFFFFF',
        fontSize: 17,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
    secondaryButton: {
        backgroundColor: 'rgba(42, 42, 42, 0.9)',
        paddingVertical: 14,
        borderRadius: 10,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#444',
    },
    secondaryButtonText: {
        color: '#FFFFFF',
        fontSize: 15,
    },
    tertiaryButton: {
        paddingVertical: 12,
        alignItems: 'center',
    },
    tertiaryButtonText: {
        color: '#AAAAAA',
        fontSize: 15,
    },
    testingInfo: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        paddingVertical: 20,
        paddingHorizontal: 24,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#00B4D8',
    },
    testingText: {
        color: '#00B4D8',
        fontSize: 16,
        textAlign: 'center',
        fontWeight: '600',
    },
});
