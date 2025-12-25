import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, TextInput, ActivityIndicator, Alert } from 'react-native';
import * as Location from 'expo-location';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

// Google Places API Key
const GOOGLE_PLACES_API_KEY = 'AIzaSyDlhMcq6aIe3dQk4MHNHkZTg-LDkZAtawo';

export default function CourseSelectScreen({ onBack, onStartRound }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [location, setLocation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [error, setError] = useState(null);

    // Haversine distance calculation
    const calculateDistance = (lat1, lon1, lat2, lon2) => {
        const R = 3959; // Earth radius in miles
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return (R * c).toFixed(1);
    };

    // Fetch nearby golf courses using Google Places API
    const fetchNearbyCourses = async (latitude, longitude) => {
        try {
            const radius = 40234; // 25 miles in meters
            // Use text search with "golf course" keyword + location bias for better results
            const url = `https://maps.googleapis.com/maps/api/place/textsearch/json?query=golf%20course&location=${latitude},${longitude}&radius=${radius}&key=${GOOGLE_PLACES_API_KEY}`;

            console.log('Fetching courses from:', url);
            const response = await fetch(url);
            const data = await response.json();

            console.log('API Response status:', data.status);

            if (data.status === 'OK' && data.results && data.results.length > 0) {
                const coursesWithDistance = data.results.map(place => ({
                    id: place.place_id,
                    name: place.name,
                    address: place.formatted_address || place.vicinity,
                    lat: place.geometry.location.lat,
                    lon: place.geometry.location.lng,
                    rating: place.rating || null,
                    totalRatings: place.user_ratings_total || 0,
                    distance: calculateDistance(latitude, longitude,
                        place.geometry.location.lat, place.geometry.location.lng),
                    isOpen: place.opening_hours?.open_now,
                    priceLevel: place.price_level,
                }));

                // Sort by distance
                coursesWithDistance.sort((a, b) => parseFloat(a.distance) - parseFloat(b.distance));
                return { courses: coursesWithDistance, error: null };
            } else if (data.status === 'ZERO_RESULTS') {
                return { courses: [], error: 'No golf courses found nearby. Try searching by name.' };
            } else {
                return { courses: [], error: `API Error: ${data.status}` };
            }
        } catch (error) {
            console.error('Error fetching courses:', error);
            return { courses: [], error: error.message };
        }
    };

    // Search courses by text query
    const searchCoursesByName = async (query) => {
        if (!query || query.length < 2) return;

        setLoading(true);
        setError(null);

        try {
            const searchTerm = query.toLowerCase().includes('golf') ? query : `${query} golf course`;
            let url = `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${encodeURIComponent(searchTerm)}&type=golf_course&key=${GOOGLE_PLACES_API_KEY}`;

            // Bias towards user location if available
            if (location) {
                url += `&location=${location.latitude},${location.longitude}&radius=80467`; // 50 miles
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.status === 'OK' && data.results) {
                // Filter to only include actual golf courses
                const golfCourses = data.results.filter(place =>
                    (place.types && place.types.includes('golf_course')) ||
                    place.name.toLowerCase().includes('golf')
                );

                const searchResults = golfCourses.map(place => ({
                    id: place.place_id,
                    name: place.name,
                    address: place.formatted_address,
                    lat: place.geometry.location.lat,
                    lon: place.geometry.location.lng,
                    rating: place.rating || null,
                    totalRatings: place.user_ratings_total || 0,
                    distance: location ? calculateDistance(
                        location.latitude, location.longitude,
                        place.geometry.location.lat, place.geometry.location.lng
                    ) : null,
                }));
                setCourses(searchResults);
            } else {
                setError('No courses found matching your search.');
                setCourses([]);
            }
        } catch (err) {
            setError('Search failed. Please try again.');
            console.error('Search error:', err);
        }
        setLoading(false);
    };

    useEffect(() => {
        loadNearbyCourses();
    }, []);

    const loadNearbyCourses = async () => {
        setLoading(true);
        setError(null);
        setSearchQuery('');

        try {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                setError('Location permission required to find nearby courses.');
                setLoading(false);
                return;
            }

            const loc = await Location.getCurrentPositionAsync({
                accuracy: Location.Accuracy.Balanced
            });
            setLocation(loc.coords);

            const result = await fetchNearbyCourses(loc.coords.latitude, loc.coords.longitude);
            setCourses(result.courses);
            if (result.error) {
                setError(result.error);
            }

        } catch (err) {
            console.error('Error:', err);
            setError('Could not get your location. Please try searching by name.');
        }
        setLoading(false);
    };

    const handleStartRound = () => {
        if (selectedCourse && onStartRound) {
            onStartRound(selectedCourse);
        }
    };

    // Icons
    const LocationIcon = () => (
        <MaterialCommunityIcons name="crosshairs-gps" size={18} color="#3FB950" />
    );

    const FlagIcon = () => (
        <MaterialCommunityIcons name="flag-variant" size={24} color="#3FB950" />
    );

    const renderRating = (rating, totalRatings) => {
        if (!rating) return null;
        return (
            <View style={styles.ratingContainer}>
                <Text style={styles.ratingValue}>★ {rating.toFixed(1)}</Text>
                {totalRatings > 0 && (
                    <Text style={styles.ratingCount}>({totalRatings})</Text>
                )}
            </View>
        );
    };

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#58A6FF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Select Course</Text>
                <View style={styles.headerPlaceholder} />
            </View>

            {/* Location Status */}
            <TouchableOpacity style={styles.locationBar} onPress={loadNearbyCourses}>
                <LocationIcon />
                <Text style={styles.locationText}>
                    {loading ? 'Finding courses...' :
                        courses.length > 0 ? `${courses.length} courses found` :
                            'Tap to find nearby courses'}
                </Text>
                <Ionicons name="refresh" size={18} color="#3FB950" />
            </TouchableOpacity>

            {/* Search */}
            <View style={styles.searchSection}>
                <TextInput
                    style={styles.searchInput}
                    placeholder="Search golf courses..."
                    placeholderTextColor="#888"
                    value={searchQuery}
                    onChangeText={setSearchQuery}
                    onSubmitEditing={() => searchCoursesByName(searchQuery)}
                    returnKeyType="search"
                />
                {searchQuery.length > 0 && (
                    <TouchableOpacity
                        style={styles.searchButton}
                        onPress={() => searchCoursesByName(searchQuery)}
                    >
                        <Text style={styles.searchButtonText}>Search</Text>
                    </TouchableOpacity>
                )}
            </View>

            {/* Error Message */}
            {error && (
                <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {/* Course List */}
            {loading ? (
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#4CAF50" />
                    <Text style={styles.loadingText}>Finding golf courses...</Text>
                </View>
            ) : courses.length === 0 ? (
                <View style={styles.emptyContainer}>
                    <Text style={styles.emptyText}>No courses found</Text>
                    <Text style={styles.emptySubtext}>Try searching by name or location</Text>
                </View>
            ) : (
                <ScrollView style={styles.courseList}>
                    {courses.map(course => (
                        <TouchableOpacity
                            key={course.id}
                            style={[
                                styles.courseCard,
                                selectedCourse?.id === course.id && styles.courseCardSelected
                            ]}
                            onPress={() => setSelectedCourse(course)}
                        >
                            <View style={styles.courseIcon}>
                                <FlagIcon />
                            </View>

                            <View style={styles.courseInfo}>
                                <Text style={styles.courseName} numberOfLines={1}>
                                    {course.name}
                                </Text>
                                <Text style={styles.courseAddress} numberOfLines={2}>
                                    {course.address}
                                </Text>

                                <View style={styles.courseStats}>
                                    {course.distance && (
                                        <View style={styles.distanceBadge}>
                                            <Text style={styles.distanceText}>{course.distance} mi</Text>
                                        </View>
                                    )}
                                    {renderRating(course.rating, course.totalRatings)}
                                    {course.isOpen !== undefined && (
                                        <Text style={[
                                            styles.openStatus,
                                            { color: course.isOpen ? '#4CAF50' : '#888' }
                                        ]}>
                                            {course.isOpen ? 'Open' : 'Closed'}
                                        </Text>
                                    )}
                                </View>
                            </View>

                            <View style={styles.selectIndicator}>
                                {selectedCourse?.id === course.id ? (
                                    <View style={styles.selectedDot} />
                                ) : (
                                    <View style={styles.unselectedDot} />
                                )}
                            </View>
                        </TouchableOpacity>
                    ))}

                    <View style={{ height: 140 }} />
                </ScrollView>
            )}

            {/* Start Round Button */}
            {selectedCourse && (
                <View style={styles.actionBar}>
                    <View style={styles.selectedInfo}>
                        <Text style={styles.selectedName} numberOfLines={1}>
                            {selectedCourse.name}
                        </Text>
                        <Text style={styles.selectedDistance}>
                            {selectedCourse.distance ? `${selectedCourse.distance} miles away` : selectedCourse.address}
                        </Text>
                    </View>
                    <TouchableOpacity style={styles.startButton} onPress={handleStartRound}>
                        <Text style={styles.startButtonText}>START ROUND</Text>
                    </TouchableOpacity>
                </View>
            )}
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
        paddingTop: 55,
        paddingHorizontal: 16,
        paddingBottom: 14,
        backgroundColor: '#161B22',
        borderBottomWidth: 1,
        borderBottomColor: '#21262D',
    },
    backButton: {
        padding: 10,
    },
    backText: {
        color: '#58A6FF',
        fontSize: 15,
        fontWeight: '500',
    },
    headerTitle: {
        color: '#F0F6FC',
        fontSize: 18,
        fontWeight: '600',
    },
    headerPlaceholder: {
        width: 60,
    },
    locationBar: {
        flexDirection: 'row',
        alignItems: 'center',
        marginHorizontal: 16,
        marginTop: 16,
        padding: 14,
        backgroundColor: 'rgba(35, 134, 54, 0.1)',
        borderRadius: 10,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: 'rgba(63, 185, 80, 0.3)',
    },
    locationText: {
        color: '#3FB950',
        fontSize: 14,
        marginLeft: 10,
        flex: 1,
        fontWeight: '500',
    },
    refreshText: {
        color: '#3FB950',
        fontSize: 18,
    },
    searchSection: {
        flexDirection: 'row',
        paddingHorizontal: 16,
        marginBottom: 16,
        gap: 10,
    },
    searchInput: {
        flex: 1,
        backgroundColor: '#161B22',
        borderRadius: 10,
        paddingHorizontal: 16,
        paddingVertical: 14,
        color: '#F0F6FC',
        fontSize: 15,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    searchButton: {
        backgroundColor: '#238636',
        paddingHorizontal: 20,
        borderRadius: 10,
        justifyContent: 'center',
    },
    searchButtonText: {
        color: '#FFFFFF',
        fontWeight: '600',
        fontSize: 14,
    },
    errorContainer: {
        marginHorizontal: 16,
        padding: 12,
        backgroundColor: 'rgba(248, 81, 73, 0.1)',
        borderRadius: 10,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: 'rgba(248, 81, 73, 0.3)',
    },
    errorText: {
        color: '#F85149',
        fontSize: 13,
        fontWeight: '500',
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loadingText: {
        color: '#8B949E',
        marginTop: 16,
        fontSize: 14,
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    emptyText: {
        color: '#F0F6FC',
        fontSize: 18,
        fontWeight: '600',
    },
    emptySubtext: {
        color: '#8B949E',
        fontSize: 14,
        marginTop: 8,
    },
    courseList: {
        flex: 1,
        paddingHorizontal: 16,
    },
    courseCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#161B22',
        borderRadius: 14,
        padding: 16,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    courseCardSelected: {
        backgroundColor: 'rgba(35, 134, 54, 0.15)',
        borderWidth: 2,
        borderColor: '#3FB950',
    },
    courseIcon: {
        marginRight: 14,
    },
    courseInfo: {
        flex: 1,
    },
    courseName: {
        color: '#F0F6FC',
        fontSize: 15,
        fontWeight: '600',
        marginBottom: 4,
    },
    courseAddress: {
        color: '#8B949E',
        fontSize: 12,
        marginBottom: 8,
        lineHeight: 17,
    },
    courseStats: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    distanceBadge: {
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 6,
    },
    distanceText: {
        color: '#3FB950',
        fontSize: 11,
        fontWeight: '600',
    },
    ratingContainer: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    ratingValue: {
        color: '#F9D71C',
        fontSize: 12,
        fontWeight: '600',
    },
    ratingCount: {
        color: '#8B949E',
        fontSize: 10,
        marginLeft: 4,
    },
    openStatus: {
        fontSize: 11,
        fontWeight: '600',
    },
    selectIndicator: {
        paddingLeft: 12,
    },
    selectedDot: {
        width: 22,
        height: 22,
        borderRadius: 11,
        backgroundColor: '#3FB950',
    },
    unselectedDot: {
        width: 22,
        height: 22,
        borderRadius: 11,
        borderWidth: 2,
        borderColor: '#30363D',
    },
    actionBar: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        paddingBottom: 36,
        backgroundColor: 'rgba(13, 17, 23, 0.98)',
        borderTopWidth: 1,
        borderTopColor: '#21262D',
    },
    selectedInfo: {
        flex: 1,
        marginRight: 16,
    },
    selectedName: {
        color: '#F0F6FC',
        fontSize: 15,
        fontWeight: '600',
    },
    selectedDistance: {
        color: '#8B949E',
        fontSize: 12,
        marginTop: 3,
    },
    startButton: {
        backgroundColor: '#238636',
        paddingVertical: 14,
        paddingHorizontal: 28,
        borderRadius: 10,
        shadowColor: '#238636',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
    },
    startButtonText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '700',
        letterSpacing: 0.5,
    },
});
