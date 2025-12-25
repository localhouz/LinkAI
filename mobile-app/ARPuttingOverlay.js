import React, { useState, useEffect, useRef } from 'react';
import {
    StyleSheet, Text, View, TouchableOpacity, Animated, Dimensions
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Accelerometer } from 'expo-sensors';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

export default function ARPuttingOverlay({ onClose, distanceToHole = 15 }) {
    const [slopeData, setSlopeData] = useState({ x: 0, y: 0 });
    const [isCalibrating, setIsCalibrating] = useState(true);
    const [breakDirection, setBreakDirection] = useState(null);
    const [breakAmount, setBreakAmount] = useState(0);
    const pulseAnim = useRef(new Animated.Value(1)).current;
    const arrowRotation = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        let subscription;
        const samples = [];
        const CALIBRATION_SAMPLES = 30;

        const startSensor = async () => {
            await Accelerometer.setUpdateInterval(50);

            subscription = Accelerometer.addListener(data => {
                if (isCalibrating) {
                    samples.push(data);
                    if (samples.length >= CALIBRATION_SAMPLES) {
                        // Average the samples for stable reading
                        const avgX = samples.reduce((sum, s) => sum + s.x, 0) / samples.length;
                        const avgY = samples.reduce((sum, s) => sum + s.y, 0) / samples.length;

                        setSlopeData({ x: avgX, y: avgY });
                        calculateBreak(avgX, avgY);
                        setIsCalibrating(false);
                    }
                } else {
                    // Continuous slow update
                    setSlopeData(prev => ({
                        x: prev.x * 0.9 + data.x * 0.1,
                        y: prev.y * 0.9 + data.y * 0.1,
                    }));
                }
            });
        };

        startSensor();

        return () => {
            subscription?.remove();
        };
    }, [isCalibrating]);

    useEffect(() => {
        // Pulsing animation
        Animated.loop(
            Animated.sequence([
                Animated.timing(pulseAnim, {
                    toValue: 1.2,
                    duration: 1000,
                    useNativeDriver: true,
                }),
                Animated.timing(pulseAnim, {
                    toValue: 1,
                    duration: 1000,
                    useNativeDriver: true,
                }),
            ])
        ).start();
    }, []);

    const calculateBreak = (x, y) => {
        // Convert accelerometer data to slope percentage
        // x = left/right tilt, y = forward/back tilt
        const slopePercent = Math.sqrt(x * x + y * y) * 10; // Approximate percentage
        const angle = Math.atan2(x, y) * (180 / Math.PI);

        setBreakAmount(Math.min(slopePercent, 5).toFixed(1));

        // Determine break direction
        if (slopePercent < 0.3) {
            setBreakDirection('flat');
        } else if (x > 0.05) {
            setBreakDirection('right');
        } else if (x < -0.05) {
            setBreakDirection('left');
        } else if (y > 0.05) {
            setBreakDirection('uphill');
        } else {
            setBreakDirection('downhill');
        }

        // Animate arrow rotation
        Animated.timing(arrowRotation, {
            toValue: angle,
            duration: 500,
            useNativeDriver: true,
        }).start();
    };

    const recalibrate = () => {
        setIsCalibrating(true);
        setBreakDirection(null);
    };

    const getBreakMessage = () => {
        switch (breakDirection) {
            case 'flat': return 'Flat Putt';
            case 'left': return `Breaks Left ${breakAmount}%`;
            case 'right': return `Breaks Right ${breakAmount}%`;
            case 'uphill': return `Uphill ${breakAmount}%`;
            case 'downhill': return `Downhill ${breakAmount}%`;
            default: return 'Reading...';
        }
    };

    const getAimAdvice = () => {
        if (!breakDirection || breakDirection === 'flat') return 'Aim straight at the hole';

        const cups = Math.ceil(parseFloat(breakAmount) * distanceToHole / 5);

        switch (breakDirection) {
            case 'left': return `Aim ${cups} cup${cups > 1 ? 's' : ''} to the right`;
            case 'right': return `Aim ${cups} cup${cups > 1 ? 's' : ''} to the left`;
            case 'uphill': return 'Hit firm, putt will be slower';
            case 'downhill': return 'Hit soft, putt will be fast';
            default: return '';
        }
    };

    const spin = arrowRotation.interpolate({
        inputRange: [-180, 180],
        outputRange: ['-180deg', '180deg'],
    });

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onClose} style={styles.closeButton}>
                    <Ionicons name="close" size={28} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>AR Putt Read</Text>
                <TouchableOpacity onPress={recalibrate} style={styles.recalibrateBtn}>
                    <Ionicons name="refresh" size={22} color="#3FB950" />
                </TouchableOpacity>
            </View>

            {/* Main Visualization */}
            <View style={styles.visualContainer}>
                {isCalibrating ? (
                    <View style={styles.calibratingView}>
                        <Animated.View style={[styles.calibratingCircle, { transform: [{ scale: pulseAnim }] }]}>
                            <MaterialCommunityIcons name="golf" size={48} color="#3FB950" />
                        </Animated.View>
                        <Text style={styles.calibratingText}>Place phone on green</Text>
                        <Text style={styles.calibratingSubtext}>Reading slope...</Text>
                    </View>
                ) : (
                    <View style={styles.readingView}>
                        {/* Grid Lines */}
                        <View style={styles.gridContainer}>
                            {[...Array(7)].map((_, i) => (
                                <View key={`h${i}`} style={[styles.gridLine, styles.gridHorizontal, { top: `${(i + 1) * 12.5}%` }]} />
                            ))}
                            {[...Array(7)].map((_, i) => (
                                <View key={`v${i}`} style={[styles.gridLine, styles.gridVertical, { left: `${(i + 1) * 12.5}%` }]} />
                            ))}
                        </View>

                        {/* Hole Target */}
                        <View style={styles.holeTarget}>
                            <View style={styles.holeFlagpole} />
                            <MaterialCommunityIcons name="flag-variant" size={24} color="#F85149" style={styles.holeFlag} />
                            <View style={styles.holeCircle} />
                        </View>

                        {/* Break Arrow */}
                        {breakDirection && breakDirection !== 'flat' && (
                            <Animated.View style={[styles.breakArrow, { transform: [{ rotate: spin }] }]}>
                                <Ionicons name="arrow-up" size={80} color="#3FB950" />
                            </Animated.View>
                        )}

                        {/* Ball Position */}
                        <View style={styles.ballPosition}>
                            <View style={styles.ball} />
                        </View>
                    </View>
                )}
            </View>

            {/* Reading Panel */}
            {!isCalibrating && (
                <View style={styles.readingPanel}>
                    <View style={styles.slopeIndicator}>
                        <Text style={styles.slopeLabel}>BREAK</Text>
                        <Text style={styles.slopeValue}>{getBreakMessage()}</Text>
                    </View>

                    <View style={styles.adviceCard}>
                        <MaterialCommunityIcons name="lightbulb-on" size={20} color="#FFD700" />
                        <Text style={styles.adviceText}>{getAimAdvice()}</Text>
                    </View>

                    <View style={styles.distanceRow}>
                        <View style={styles.distanceStat}>
                            <Text style={styles.distanceValue}>{distanceToHole}</Text>
                            <Text style={styles.distanceLabel}>ft to hole</Text>
                        </View>
                        <View style={styles.distanceStat}>
                            <Text style={styles.distanceValue}>{breakAmount}%</Text>
                            <Text style={styles.distanceLabel}>slope</Text>
                        </View>
                    </View>
                </View>
            )}

            {/* Disclaimer */}
            <Text style={styles.disclaimer}>
                Place phone flat on green surface for best results
            </Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0D1117',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: 60,
        paddingHorizontal: 20,
        paddingBottom: 16,
    },
    closeButton: {
        padding: 8,
    },
    headerTitle: {
        color: '#F0F6FC',
        fontSize: 18,
        fontWeight: '700',
    },
    recalibrateBtn: {
        padding: 8,
    },
    visualContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    calibratingView: {
        alignItems: 'center',
    },
    calibratingCircle: {
        width: 120,
        height: 120,
        borderRadius: 60,
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#3FB950',
    },
    calibratingText: {
        color: '#F0F6FC',
        fontSize: 20,
        fontWeight: '600',
        marginTop: 24,
    },
    calibratingSubtext: {
        color: '#8B949E',
        fontSize: 14,
        marginTop: 8,
    },
    readingView: {
        width: SCREEN_WIDTH - 40,
        height: SCREEN_WIDTH - 40,
        backgroundColor: '#1a3d1a',
        borderRadius: 20,
        position: 'relative',
        overflow: 'hidden',
        borderWidth: 2,
        borderColor: '#2d5a2d',
    },
    gridContainer: {
        ...StyleSheet.absoluteFillObject,
    },
    gridLine: {
        position: 'absolute',
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    gridHorizontal: {
        left: 0,
        right: 0,
        height: 1,
    },
    gridVertical: {
        top: 0,
        bottom: 0,
        width: 1,
    },
    holeTarget: {
        position: 'absolute',
        top: '25%',
        left: '50%',
        marginLeft: -15,
        alignItems: 'center',
    },
    holeFlagpole: {
        width: 2,
        height: 40,
        backgroundColor: '#888',
        position: 'absolute',
        bottom: 15,
    },
    holeFlag: {
        position: 'absolute',
        bottom: 35,
        left: 2,
    },
    holeCircle: {
        width: 30,
        height: 30,
        borderRadius: 15,
        backgroundColor: '#111',
        borderWidth: 2,
        borderColor: '#333',
    },
    breakArrow: {
        position: 'absolute',
        top: '40%',
        left: '50%',
        marginLeft: -40,
        marginTop: -40,
    },
    ballPosition: {
        position: 'absolute',
        bottom: '20%',
        left: '50%',
        marginLeft: -10,
    },
    ball: {
        width: 20,
        height: 20,
        borderRadius: 10,
        backgroundColor: '#FFFFFF',
        borderWidth: 1,
        borderColor: '#DDD',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.3,
        shadowRadius: 3,
    },
    readingPanel: {
        padding: 20,
        backgroundColor: '#161B22',
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
    },
    slopeIndicator: {
        alignItems: 'center',
        marginBottom: 16,
    },
    slopeLabel: {
        color: '#8B949E',
        fontSize: 12,
        fontWeight: '600',
        letterSpacing: 2,
    },
    slopeValue: {
        color: '#3FB950',
        fontSize: 28,
        fontWeight: '700',
        marginTop: 4,
    },
    adviceCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 215, 0, 0.1)',
        padding: 16,
        borderRadius: 12,
        marginBottom: 16,
        gap: 12,
    },
    adviceText: {
        color: '#F0F6FC',
        fontSize: 15,
        flex: 1,
    },
    distanceRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
    },
    distanceStat: {
        alignItems: 'center',
    },
    distanceValue: {
        color: '#F0F6FC',
        fontSize: 24,
        fontWeight: '700',
    },
    distanceLabel: {
        color: '#8B949E',
        fontSize: 12,
        marginTop: 4,
    },
    disclaimer: {
        color: '#484F58',
        fontSize: 11,
        textAlign: 'center',
        paddingBottom: 40,
        paddingHorizontal: 40,
    },
});
