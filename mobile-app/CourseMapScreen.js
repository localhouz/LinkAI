import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, TextInput, Alert, ActivityIndicator } from 'react-native';
import * as Location from 'expo-location';
import Svg, { Path, Circle, Rect, Line, G, Polygon } from 'react-native-svg';

export default function CourseMapScreen({ onBack, onPlayCourse }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [location, setLocation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [nearbyCourses, setNearbyCourses] = useState([]);

    // Calculate distance between two coordinates (Haversine formula)
    const calculateDistance = (lat1, lon1, lat2, lon2) => {
        const R = 3959; // Earth's radius in miles
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    // Demo courses with coordinates (would come from real API)
    const allCourses = [
        { id: 1, name: 'Pebble Beach Golf Links', location: 'Pebble Beach, CA', lat: 36.5681, lon: -121.9486, rating: 4.9, holes: 18, par: 72 },
        { id: 2, name: 'Augusta National Golf Club', location: 'Augusta, GA', lat: 33.5030, lon: -82.0231, rating: 5.0, holes: 18, par: 72 },
        { id: 3, name: 'Torrey Pines South', location: 'La Jolla, CA', lat: 32.9003, lon: -117.2514, rating: 4.8, holes: 18, par: 72 },
        { id: 4, name: 'TPC Sawgrass', location: 'Ponte Vedra Beach, FL', lat: 30.1975, lon: -81.3959, rating: 4.8, holes: 18, par: 72 },
        { id: 5, name: 'Pinehurst No. 2', location: 'Pinehurst, NC', lat: 35.1954, lon: -79.4700, rating: 4.7, holes: 18, par: 72 },
        { id: 6, name: 'Bethpage Black', location: 'Farmingdale, NY', lat: 40.7444, lon: -73.4548, rating: 4.6, holes: 18, par: 71 },
        // Local demo courses that will show as "nearby" for testing
        { id: 7, name: 'Local Golf Club', location: 'Nearby', lat: 0, lon: 0, rating: 4.3, holes: 18, par: 72, isLocal: true },
        { id: 8, name: 'City Municipal Golf', location: 'Nearby', lat: 0, lon: 0, rating: 4.0, holes: 18, par: 71, isLocal: true },
        { id: 9, name: 'Country Club Estates', location: 'Nearby', lat: 0, lon: 0, rating: 4.5, holes: 18, par: 72, isLocal: true },
    ];

    useEffect(() => {
        (async () => {
            try {
                const { status } = await Location.requestForegroundPermissionsAsync();
                if (status !== 'granted') {
                    Alert.alert('Location Required', 'Enable location to find nearby courses');
                    setLoading(false);
                    return;
                }

                const loc = await Location.getCurrentPositionAsync({
                    accuracy: Location.Accuracy.Balanced
                });
                setLocation(loc.coords);

                // Calculate distances and sort by nearest
                const coursesWithDistance = allCourses.map(course => {
                    // For "local" demo courses, place them near the user
                    if (course.isLocal) {
                        const offset = (course.id - 6) * 0.01; // Small offset for demo
                        course.lat = loc.coords.latitude + offset;
                        course.lon = loc.coords.longitude + offset;
                    }

                    const distance = calculateDistance(
                        loc.coords.latitude,
                        loc.coords.longitude,
                        course.lat,
                        course.lon
                    );
                    return { ...course, distance: distance.toFixed(1) };
                });

                // Sort by distance
                coursesWithDistance.sort((a, b) => parseFloat(a.distance) - parseFloat(b.distance));
                setNearbyCourses(coursesWithDistance);
                setLoading(false);

            } catch (error) {
                console.error('Location error:', error);
                setLoading(false);
                // Show all courses without distance if location fails
                setNearbyCourses(allCourses.map(c => ({ ...c, distance: '?' })));
            }
        })();
    }, []);

    const filteredCourses = nearbyCourses.filter(course =>
        course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        course.location.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handlePlayCourse = (course) => {
        if (onPlayCourse) {
            onPlayCourse(course);
        } else {
            Alert.alert(
                'Start Round',
                `Start a new round at ${course.name}?`,
                [
                    { text: 'Cancel', style: 'cancel' },
                    {
                        text: 'Start Round',
                        onPress: () => {
                            // Navigate back and trigger scorecard with course
                            Alert.alert('Round Started', `Playing at ${course.name}`);
                        }
                    }
                ]
            );
        }
    };

    // Simple course hole preview
    const HolePreview = ({ holeNumber }) => (
        <Svg width={60} height={100} viewBox="0 0 60 100">
            {/* Fairway */}
            <Path
                d="M 30 95 Q 25 60, 30 30 Q 35 20, 30 10"
                fill="none"
                stroke="#4CAF50"
                strokeWidth="12"
                strokeLinecap="round"
            />
            {/* Tee box */}
            <Rect x="25" y="88" width="10" height="6" fill="#8B4513" rx="2" />
            {/* Green */}
            <Circle cx="30" cy="12" r="8" fill="#66BB6A" />
            {/* Flag */}
            <Line x1="30" y1="12" x2="30" y2="4" stroke="#1B5E20" strokeWidth="1" />
            <Polygon points="30,4 38,7 30,10" fill="#f44336" />
        </Svg>
    );

    // Location icon
    const LocationIcon = () => (
        <Svg width={16} height={16} viewBox="0 0 100 100">
            <Circle cx="50" cy="50" r="15" fill="#4CAF50" />
            <Circle cx="50" cy="50" r="35" fill="none" stroke="#4CAF50" strokeWidth="4" opacity="0.5" />
            <Circle cx="50" cy="50" r="50" fill="none" stroke="#4CAF50" strokeWidth="2" opacity="0.3" />
        </Svg>
    );

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Course Maps</Text>
                <View style={styles.placeholder} />
            </View>

            {/* Location Status */}
            <View style={styles.locationBar}>
                <View style={styles.locationIndicator}>
                    <LocationIcon />
                    <Text style={styles.locationText}>
                        {loading ? 'Finding your location...' :
                            location ? 'Showing courses near you' : 'Location unavailable'}
                    </Text>
                </View>
            </View>

            {/* Search Bar */}
            <View style={styles.searchContainer}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="Search courses by name or location..."
                    placeholderTextColor="#888888"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                />
            </View>

            {/* Stats */}
            <View style={styles.statsRow}>
                <View style={styles.statBox}>
                    <Text style={styles.statValue}>40,000+</Text>
                    <Text style={styles.statLabel}>Courses</Text>
                </View>
                <View style={styles.statBox}>
                    <Text style={styles.statValue}>195</Text>
                    <Text style={styles.statLabel}>Countries</Text>
                </View>
                <View style={styles.statBox}>
                    <Text style={styles.statValue}>HD</Text>
                    <Text style={styles.statLabel}>Satellite</Text>
                </View>
            </View>

            {/* Course List */}
            {loading ? (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#4CAF50" />
                    <Text style={styles.loadingText}>Finding nearby courses...</Text>
                </View>
            ) : (
                <ScrollView style={styles.courseList}>
                    <Text style={styles.sectionTitle}>
                        {searchQuery ? 'SEARCH RESULTS' : 'NEARBY COURSES'}
                    </Text>

                    {filteredCourses.length === 0 ? (
                        <View style={styles.emptyState}>
                            <Text style={styles.emptyText}>No courses found</Text>
                        </View>
                    ) : (
                        filteredCourses.map(course => (
                            <TouchableOpacity
                                key={course.id}
                                style={[
                                    styles.courseCard,
                                    selectedCourse?.id === course.id && styles.courseCardActive
                                ]}
                                onPress={() => setSelectedCourse(course)}
                            >
                                <View style={styles.coursePreview}>
                                    <HolePreview holeNumber={1} />
                                </View>

                                <View style={styles.courseInfo}>
                                    <View style={styles.courseNameRow}>
                                        <Text style={styles.courseName}>{course.name}</Text>
                                        <View style={styles.distanceBadge}>
                                            <Text style={styles.distanceText}>{course.distance} mi</Text>
                                        </View>
                                    </View>
                                    <Text style={styles.courseLocation}>{course.location}</Text>
                                    <View style={styles.courseStats}>
                                        <View style={styles.courseStat}>
                                            <Text style={styles.courseStatValue}>{course.holes}</Text>
                                            <Text style={styles.courseStatLabel}>Holes</Text>
                                        </View>
                                        <View style={styles.courseStat}>
                                            <Text style={styles.courseStatValue}>{course.par}</Text>
                                            <Text style={styles.courseStatLabel}>Par</Text>
                                        </View>
                                        <View style={styles.courseStat}>
                                            <Text style={styles.courseStatValue}>★ {course.rating}</Text>
                                            <Text style={styles.courseStatLabel}>Rating</Text>
                                        </View>
                                    </View>
                                </View>

                                <View style={styles.courseArrow}>
                                    <Text style={styles.arrowText}>›</Text>
                                </View>
                            </TouchableOpacity>
                        ))
                    )}

                    <View style={{ height: 120 }} />
                </ScrollView>
            )}

            {/* Selected Course Action */}
            {selectedCourse && (
                <View style={styles.actionBar}>
                    <View style={styles.selectedInfo}>
                        <Text style={styles.selectedName}>{selectedCourse.name}</Text>
                        <Text style={styles.selectedDistance}>{selectedCourse.distance} miles away</Text>
                    </View>
                    <TouchableOpacity
                        style={styles.playButton}
                        onPress={() => handlePlayCourse(selectedCourse)}
                    >
                        <Text style={styles.playButtonText}>PLAY NOW</Text>
                    </TouchableOpacity>
                </View>
            )}
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
        paddingBottom: 15,
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
    locationBar: {
        paddingHorizontal: 20,
        marginBottom: 12,
    },
    locationIndicator: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(76, 175, 80, 0.15)',
        padding: 10,
        borderRadius: 10,
    },
    locationText: {
        color: '#4CAF50',
        fontSize: 13,
        marginLeft: 10,
    },
    searchContainer: {
        paddingHorizontal: 20,
        marginBottom: 16,
    },
    searchInput: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 12,
        paddingHorizontal: 16,
        paddingVertical: 14,
        color: '#FFFFFF',
        fontSize: 16,
    },
    statsRow: {
        flexDirection: 'row',
        paddingHorizontal: 20,
        marginBottom: 20,
        gap: 12,
    },
    statBox: {
        flex: 1,
        backgroundColor: 'rgba(46, 125, 50, 0.2)',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    statValue: {
        color: '#4CAF50',
        fontSize: 20,
        fontWeight: 'bold',
    },
    statLabel: {
        color: '#888888',
        fontSize: 11,
        marginTop: 4,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        color: '#888888',
        fontSize: 14,
        marginTop: 16,
    },
    courseList: {
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
    emptyState: {
        alignItems: 'center',
        padding: 40,
    },
    emptyText: {
        color: '#888888',
        fontSize: 16,
    },
    courseCard: {
        flexDirection: 'row',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
        alignItems: 'center',
    },
    courseCardActive: {
        backgroundColor: 'rgba(46, 125, 50, 0.2)',
        borderWidth: 1,
        borderColor: '#4CAF50',
    },
    coursePreview: {
        marginRight: 16,
    },
    courseInfo: {
        flex: 1,
    },
    courseNameRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 4,
    },
    courseName: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
        flex: 1,
    },
    distanceBadge: {
        backgroundColor: 'rgba(76, 175, 80, 0.3)',
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 10,
        marginLeft: 8,
    },
    distanceText: {
        color: '#4CAF50',
        fontSize: 11,
        fontWeight: '600',
    },
    courseLocation: {
        color: '#888888',
        fontSize: 13,
        marginBottom: 10,
    },
    courseStats: {
        flexDirection: 'row',
        gap: 16,
    },
    courseStat: {
        alignItems: 'center',
    },
    courseStatValue: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '600',
    },
    courseStatLabel: {
        color: '#666666',
        fontSize: 10,
    },
    courseArrow: {
        paddingLeft: 10,
    },
    arrowText: {
        color: '#4CAF50',
        fontSize: 28,
    },
    actionBar: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        paddingBottom: 40,
        backgroundColor: 'rgba(10, 22, 18, 0.98)',
        borderTopWidth: 1,
        borderTopColor: 'rgba(255, 255, 255, 0.1)',
    },
    selectedInfo: {
        flex: 1,
    },
    selectedName: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    selectedDistance: {
        color: '#888888',
        fontSize: 12,
        marginTop: 2,
    },
    playButton: {
        backgroundColor: '#2E7D32',
        paddingVertical: 14,
        paddingHorizontal: 28,
        borderRadius: 12,
    },
    playButtonText: {
        color: '#FFFFFF',
        fontSize: 15,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
});
