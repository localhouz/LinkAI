import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Alert } from 'react-native';
import * as Location from 'expo-location';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

export default function RangefinderScreen({ onBack }) {
    const [location, setLocation] = useState(null);
    const [targets, setTargets] = useState([]);
    const [selectedTarget, setSelectedTarget] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Location permission is required for rangefinder');
                return;
            }

            const loc = await Location.getCurrentPositionAsync({
                accuracy: Location.Accuracy.BestForNavigation
            });
            setLocation(loc.coords);

            // Demo targets (would come from course database)
            setTargets([
                { id: 1, name: 'Front of Green', distance: 145, type: 'green' },
                { id: 2, name: 'Center of Green', distance: 158, type: 'green' },
                { id: 3, name: 'Back of Green', distance: 172, type: 'green' },
                { id: 4, name: 'Bunker Left', distance: 130, type: 'hazard' },
                { id: 5, name: 'Water Right', distance: 110, type: 'hazard' },
                { id: 6, name: 'Layup', distance: 100, type: 'layup' },
            ]);
            setLoading(false);
        })();
    }, []);

    const getTargetColor = (type) => {
        switch (type) {
            case 'green': return '#4CAF50';
            case 'hazard': return '#f44336';
            case 'layup': return '#2196F3';
            default: return '#9E9E9E';
        }
    };

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>GPS Rangefinder</Text>
                <View style={styles.placeholder} />
            </View>

            {/* Main Distance Display */}
            <View style={styles.mainDisplay}>
                <View style={styles.distanceCircle}>
                    <View style={styles.iconCircleContainer}>
                        <MaterialCommunityIcons name="target" size={180} color="rgba(46, 125, 50, 0.4)" />
                    </View>
                    <View style={styles.distanceContent}>
                        <Text style={styles.distanceValue}>
                            {selectedTarget ? selectedTarget.distance : '---'}
                        </Text>
                        <Text style={styles.distanceUnit}>YARDS</Text>
                        <Text style={styles.targetName}>
                            {selectedTarget ? selectedTarget.name : 'Select Target'}
                        </Text>
                    </View>
                </View>
            </View>

            {/* Target List */}
            <View style={styles.targetSection}>
                <Text style={styles.sectionTitle}>TARGETS</Text>
                <ScrollView style={styles.targetList}>
                    {targets.map(target => (
                        <TouchableOpacity
                            key={target.id}
                            style={[
                                styles.targetItem,
                                selectedTarget?.id === target.id && styles.targetItemActive
                            ]}
                            onPress={() => setSelectedTarget(target)}
                        >
                            <View style={[styles.targetDot, { backgroundColor: getTargetColor(target.type) }]} />
                            <View style={styles.targetInfo}>
                                <Text style={styles.targetItemName}>{target.name}</Text>
                                <Text style={styles.targetType}>{target.type.toUpperCase()}</Text>
                            </View>
                            <Text style={styles.targetDistance}>{target.distance}</Text>
                        </TouchableOpacity>
                    ))}
                </ScrollView>
            </View>

            {/* GPS Status */}
            <View style={styles.gpsStatus}>
                <View style={[styles.gpsIndicator, location && styles.gpsActive]} />
                <Text style={styles.gpsText}>
                    {location ? 'GPS Active' : 'Acquiring GPS...'}
                </Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A1612',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: 60,
        paddingHorizontal: 20,
        paddingBottom: 20,
    },
    backButton: {
        padding: 8,
    },
    backButtonText: {
        color: '#FFFFFF',
        fontSize: 16,
    },
    headerTitle: {
        color: '#FFFFFF',
        fontSize: 20,
        fontWeight: 'bold',
    },
    placeholder: {
        width: 60,
    },
    mainDisplay: {
        alignItems: 'center',
        paddingVertical: 30,
    },
    distanceCircle: {
        width: 200,
        height: 200,
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
    },
    iconCircleContainer: {
        position: 'absolute',
        justifyContent: 'center',
        alignItems: 'center',
    },
    distanceContent: {
        position: 'absolute',
        alignItems: 'center',
        zIndex: 1,
    },
    distanceValue: {
        color: '#FFFFFF',
        fontSize: 52,
        fontWeight: 'bold',
    },
    distanceUnit: {
        color: '#4CAF50',
        fontSize: 14,
        fontWeight: 'bold',
        letterSpacing: 2,
    },
    targetName: {
        color: '#AAAAAA',
        fontSize: 12,
        marginTop: 8,
    },
    targetSection: {
        flex: 1,
        paddingHorizontal: 20,
    },
    sectionTitle: {
        color: '#4CAF50',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 1,
        marginBottom: 12,
    },
    targetList: {
        flex: 1,
    },
    targetItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        padding: 16,
        borderRadius: 12,
        marginBottom: 10,
    },
    targetItemActive: {
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
        borderWidth: 1,
        borderColor: '#4CAF50',
    },
    targetDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginRight: 14,
    },
    targetInfo: {
        flex: 1,
    },
    targetItemName: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    targetType: {
        color: '#888888',
        fontSize: 11,
        marginTop: 2,
    },
    targetDistance: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
    },
    gpsStatus: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 20,
        paddingBottom: 40,
    },
    gpsIndicator: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#FF5722',
        marginRight: 8,
    },
    gpsActive: {
        backgroundColor: '#4CAF50',
    },
    gpsText: {
        color: '#888888',
        fontSize: 12,
    },
});
