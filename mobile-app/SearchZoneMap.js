import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Alert } from 'react-native';
import MapView, { Circle, Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import * as Location from 'expo-location';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

export default function SearchZoneMap({ shotData, onComplete }) {
    const [userLocation, setUserLocation] = useState(null);
    const [heading, setHeading] = useState(0);
    const [distanceToZone, setDistanceToZone] = useState(null);
    const [isSearching, setIsSearching] = useState(false);

    const {
        name,
        color,
        landing_gps,
        search_zone,
        carry_distance_yards,
        curve_yards
    } = shotData;

    useEffect(() => {
        (async () => {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Location permission is required');
                return;
            }

            const subscription = await Location.watchPositionAsync(
                {
                    accuracy: Location.Accuracy.High,
                    timeInterval: 1000,
                    distanceInterval: 1,
                },
                (location) => {
                    setUserLocation({
                        latitude: location.coords.latitude,
                        longitude: location.coords.longitude,
                    });

                    const distance = calculateDistance(
                        location.coords.latitude,
                        location.coords.longitude,
                        landing_gps.lat,
                        landing_gps.lon
                    );
                    setDistanceToZone(distance);

                    // Auto-enable search mode when entering zone
                    if (distance < search_zone.radius_meters && !isSearching) {
                        setIsSearching(true);
                    }

                    const bearing = calculateBearing(
                        location.coords.latitude,
                        location.coords.longitude,
                        landing_gps.lat,
                        landing_gps.lon
                    );
                    setHeading(bearing);
                }
            );

            return () => subscription.remove();
        })();
    }, []);

    const calculateDistance = (lat1, lon1, lat2, lon2) => {
        const R = 6371000;
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lon2 - lon1) * Math.PI / 180;

        const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        return R * c;
    };

    const calculateBearing = (lat1, lon1, lat2, lon2) => {
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δλ = (lon2 - lon1) * Math.PI / 180;

        const y = Math.sin(Δλ) * Math.cos(φ2);
        const x = Math.cos(φ1) * Math.sin(φ2) -
            Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
        const θ = Math.atan2(y, x);

        return (θ * 180 / Math.PI + 360) % 360;
    };

    const getDirectionText = () => {
        if (!distanceToZone) return 'Locating...';

        const yards = distanceToZone * 1.09361;

        if (distanceToZone < search_zone.radius_meters) {
            return 'IN SEARCH ZONE';
        }

        const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        const index = Math.round(heading / 45) % 8;
        const direction = directions[index];

        return `${yards.toFixed(0)} yards ${direction}`;
    };

    const handleDoneSearching = () => {
        // This is when they've searched and are ready to report results
        onComplete();
    };

    const initialRegion = landing_gps ? {
        latitude: landing_gps.lat,
        longitude: landing_gps.lon,
        latitudeDelta: 0.005,
        longitudeDelta: 0.005,
    } : null;

    const inZone = distanceToZone && distanceToZone < search_zone.radius_meters;

    return (
        <View style={styles.container}>
            {initialRegion && (
                <MapView
                    style={styles.map}
                    provider={PROVIDER_GOOGLE}
                    initialRegion={initialRegion}
                    mapType="satellite"
                    showsUserLocation={true}
                    followsUserLocation={true}
                    showsCompass={true}
                    showsScale={true}
                >
                    <Circle
                        center={{
                            latitude: landing_gps.lat,
                            longitude: landing_gps.lon,
                        }}
                        radius={search_zone.radius_meters}
                        fillColor={`${color}40`}
                        strokeColor={color}
                        strokeWidth={3}
                    />

                    <Marker
                        coordinate={{
                            latitude: landing_gps.lat,
                            longitude: landing_gps.lon,
                        }}
                        title="Predicted Landing"
                        description={`${name} • ${carry_distance_yards.toFixed(0)} yards`}
                    >
                        <View style={[styles.marker, { backgroundColor: color }]}>
                            <MaterialCommunityIcons name="flag-variant" size={20} color="#FFFFFF" />
                        </View>
                    </Marker>

                    {userLocation && (
                        <Polyline
                            coordinates={[
                                userLocation,
                                { latitude: landing_gps.lat, longitude: landing_gps.lon }
                            ]}
                            strokeColor={color}
                            strokeWidth={2}
                            lineDashPattern={[5, 5]}
                        />
                    )}
                </MapView>
            )}

            {/* Info overlay */}
            <View style={styles.infoOverlay}>
                <View style={styles.infoBox}>
                    <Text style={styles.shotName}>{name}</Text>
                    <Text style={styles.shotStats}>
                        {carry_distance_yards < 1
                            ? `${(carry_distance_yards * 3 * 12).toFixed(0)} inches`
                            : `${carry_distance_yards.toFixed(0)} yards`
                        }
                    </Text>
                    <Text style={styles.searchRadius}>
                        Search within {search_zone.radius_yards.toFixed(0)} yards
                    </Text>
                </View>
            </View>

            {/* Navigation overlay */}
            <View style={styles.navigationOverlay}>
                <View style={[
                    styles.directionBox,
                    inZone && styles.directionBoxInZone
                ]}>
                    <Text style={styles.directionText}>
                        {getDirectionText()}
                    </Text>
                </View>
            </View>

            {/* Bottom controls - changes based on location */}
            <View style={styles.bottomControls}>
                {inZone ? (
                    <>
                        <View style={styles.tipBox}>
                            <Text style={styles.tipText}>
                                You're in the search zone! Look around for your ball within {search_zone.radius_yards.toFixed(0)} yards of the flag.
                            </Text>
                        </View>

                        <TouchableOpacity
                            style={styles.doneButton}
                            onPress={handleDoneSearching}
                        >
                            <Text style={styles.doneButtonText}>
                                DONE SEARCHING
                            </Text>
                        </TouchableOpacity>
                    </>
                ) : (
                    <>
                        <View style={styles.instructionBox}>
                            <Text style={styles.instructionTitle}>Navigate to Search Zone</Text>
                            <Text style={styles.instructionText}>
                                Walk toward the flag marker. Distance and direction will update as you move.
                            </Text>
                        </View>

                        <TouchableOpacity
                            style={styles.backButton}
                            onPress={handleDoneSearching}
                        >
                            <Ionicons name="close-circle-outline" size={20} color="#FFFFFF" style={{ marginRight: 8 }} />
                            <Text style={styles.backButtonText}>Cancel</Text>
                        </TouchableOpacity>
                    </>
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
    map: {
        flex: 1,
    },
    infoOverlay: {
        position: 'absolute',
        top: 50,
        left: 15,
        right: 15,
    },
    infoBox: {
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        padding: 16,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#00B4D8',
    },
    shotName: {
        color: '#fff',
        fontSize: 20,
        fontWeight: 'bold',
        marginBottom: 6,
    },
    shotStats: {
        color: '#aaa',
        fontSize: 14,
        marginBottom: 4,
    },
    searchRadius: {
        color: '#00B4D8',
        fontSize: 13,
        marginTop: 4,
    },
    navigationOverlay: {
        position: 'absolute',
        top: '50%',
        left: 0,
        right: 0,
        alignItems: 'center',
    },
    directionBox: {
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        paddingHorizontal: 30,
        paddingVertical: 20,
        borderRadius: 50,
        borderWidth: 3,
        borderColor: '#00B4D8',
    },
    directionBoxInZone: {
        borderColor: '#00e676',
        backgroundColor: 'rgba(0, 230, 118, 0.2)',
    },
    directionText: {
        color: '#fff',
        fontSize: 22,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    marker: {
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 3,
        borderColor: '#fff',
    },
    markerText: {
        fontSize: 20,
    },
    bottomControls: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        padding: 20,
        borderTopWidth: 1,
        borderTopColor: '#333',
    },
    instructionBox: {
        marginBottom: 16,
    },
    instructionTitle: {
        color: '#00B4D8',
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 8,
    },
    instructionText: {
        color: '#AAAAAA',
        fontSize: 14,
        lineHeight: 20,
    },
    tipBox: {
        padding: 14,
        backgroundColor: 'rgba(0, 230, 118, 0.15)',
        borderRadius: 10,
        borderWidth: 1,
        borderColor: '#00e676',
        marginBottom: 16,
    },
    tipText: {
        color: '#00e676',
        fontSize: 14,
        textAlign: 'center',
        lineHeight: 20,
    },
    doneButton: {
        backgroundColor: '#00B4D8',
        paddingVertical: 18,
        borderRadius: 10,
        alignItems: 'center',
    },
    doneButtonText: {
        color: '#FFFFFF',
        fontSize: 17,
        fontWeight: 'bold',
        letterSpacing: 0.5,
    },
    backButton: {
        flexDirection: 'row',
        backgroundColor: '#2A2A2A',
        paddingVertical: 16,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
    },
    backButtonText: {
        color: '#FFFFFF',
        fontSize: 16,
    },
});
