import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Alert, Dimensions } from 'react-native';
import * as Location from 'expo-location';
import Svg, { Circle, Path, Rect, Line, Polygon, G } from 'react-native-svg';
import MapView, { Marker, Polyline, Circle as MapCircle, Polygon as MapPolygon } from 'react-native-maps';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Backend API URL - change this to your server IP when testing on device
const API_BASE_URL = 'http://192.168.1.168:5000';

export default function ActiveRoundScreen({ course, onEndRound }) {
    const [activeTab, setActiveTab] = useState('map'); // 'map' | 'scorecard' | 'rangefinder'
    const [currentHole, setCurrentHole] = useState(1);
    const [scores, setScores] = useState({});
    const [location, setLocation] = useState(null);
    const [watchId, setWatchId] = useState(null);
    const [courseFeatures, setCourseFeatures] = useState(null);
    const [featuresLoading, setFeaturesLoading] = useState(false);

    // Fetch real course features from backend (greens, tees, fairways, bunkers, water)
    useEffect(() => {
        const fetchCourseFeatures = async () => {
            if (!course.lat || !course.lon) return;

            setFeaturesLoading(true);
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/courses/details?lat=${course.lat}&lon=${course.lon}&radius=2000`
                );
                const data = await response.json();

                if (data.success && data.features) {
                    console.log('Course features loaded:', {
                        holes: data.features.holes?.length || 0,
                        greens: data.features.greens?.length || 0,
                        tees: data.features.tees?.length || 0,
                        fairways: data.features.fairways?.length || 0,
                        bunkers: data.features.bunkers?.length || 0,
                    });
                    setCourseFeatures(data.features);
                }
            } catch (error) {
                console.log('Could not fetch course features:', error.message);
                // Will fall back to simulated positions
            }
            setFeaturesLoading(false);
        };

        fetchCourseFeatures();
    }, [course.lat, course.lon]);

    // Generate hole data for the course
    const generateHoleData = () => {
        const pars = [4, 3, 5, 4, 4, 3, 5, 4, 4, 4, 5, 3, 4, 4, 5, 3, 4, 4];
        const baseYards = [385, 165, 520, 410, 375, 195, 545, 340, 420, 390, 510, 175, 400, 365, 535, 185, 430, 395];

        return pars.map((par, i) => ({
            hole: i + 1,
            par,
            yards: baseYards[i] + Math.floor(Math.random() * 30 - 15),
            handicap: ((i * 7) % 18) + 1,
        }));
    };

    const [holeData] = useState(generateHoleData());
    const [tappedPoint, setTappedPoint] = useState(null);
    const [distanceToTap, setDistanceToTap] = useState(null);

    useEffect(() => {
        startLocationTracking();
        return () => {
            if (watchId) {
                watchId.remove();
            }
        };
    }, []);

    const startLocationTracking = async () => {
        try {
            const { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') return;

            const subscription = await Location.watchPositionAsync(
                {
                    accuracy: Location.Accuracy.BestForNavigation,
                    distanceInterval: 5, // Update every 5 meters
                },
                (loc) => {
                    setLocation(loc.coords);
                }
            );
            setWatchId(subscription);
        } catch (error) {
            console.error('Location error:', error);
        }
    };

    // Calculate distance to a point
    const calculateDistance = (lat1, lon1, lat2, lon2) => {
        const R = 6371000; // Earth radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2;
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c; // Distance in meters
    };

    const metersToYards = (m) => Math.round(m * 1.09361);

    // Simulated targets for current hole (in real app, from course database)
    const getHoleTargets = () => {
        const holeYards = holeData[currentHole - 1].yards;
        return [
            { name: 'Front Green', yards: holeYards - 15, type: 'green' },
            { name: 'Center Green', yards: holeYards, type: 'green' },
            { name: 'Back Green', yards: holeYards + 12, type: 'green' },
            { name: 'Layup', yards: Math.round(holeYards * 0.6), type: 'layup' },
        ];
    };

    // Score functions
    const updateScore = (delta) => {
        const current = scores[currentHole] || holeData[currentHole - 1].par;
        const newScore = Math.max(1, current + delta);
        setScores({ ...scores, [currentHole]: newScore });
    };

    const getScoreLabel = (score, par) => {
        const diff = score - par;
        if (diff <= -2) return { label: 'Eagle', color: '#FFD700' };
        if (diff === -1) return { label: 'Birdie', color: '#2196F3' };
        if (diff === 0) return { label: 'Par', color: '#4CAF50' };
        if (diff === 1) return { label: 'Bogey', color: '#FF9800' };
        if (diff === 2) return { label: 'Double', color: '#f44336' };
        return { label: `+${diff}`, color: '#f44336' };
    };

    const getTotalScore = () => Object.values(scores).reduce((a, b) => a + b, 0);
    const getTotalPar = () => Object.keys(scores).map(h => holeData[h - 1].par).reduce((a, b) => a + b, 0);

    const getScoreVsPar = () => {
        if (Object.keys(scores).length === 0) return '—';
        const diff = getTotalScore() - getTotalPar();
        if (diff === 0) return 'E';
        return diff > 0 ? `+${diff}` : `${diff}`;
    };

    const handleEndRound = () => {
        Alert.alert(
            'End Round?',
            `Finish your round at ${course.name}?`,
            [
                { text: 'Cancel', style: 'cancel' },
                { text: 'End Round', style: 'destructive', onPress: onEndRound }
            ]
        );
    };

    const currentHoleData = holeData[currentHole - 1];
    const currentScore = scores[currentHole] || currentHoleData.par;
    const scoreInfo = getScoreLabel(currentScore, currentHoleData.par);

    // Tab icons
    const ScorecardIcon = ({ active }) => (
        <Svg width={22} height={22} viewBox="0 0 100 100">
            <Rect x="20" y="15" width="60" height="70" rx="5" fill="none" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="6" />
            <Line x1="30" y1="35" x2="70" y2="35" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
            <Line x1="30" y1="50" x2="70" y2="50" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
            <Line x1="30" y1="65" x2="55" y2="65" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
        </Svg>
    );

    const RangefinderIcon = ({ active }) => (
        <Svg width={22} height={22} viewBox="0 0 100 100">
            <Circle cx="50" cy="50" r="35" fill="none" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="6" />
            <Line x1="50" y1="20" x2="50" y2="35" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
            <Line x1="50" y1="65" x2="50" y2="80" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
            <Line x1="20" y1="50" x2="35" y2="50" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
            <Line x1="65" y1="50" x2="80" y2="50" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="4" />
            <Circle cx="50" cy="50" r="8" fill={active ? '#58A6FF' : '#8B949E'} />
        </Svg>
    );

    const MapIcon = ({ active }) => (
        <Svg width={22} height={22} viewBox="0 0 100 100">
            <Path d="M20 25 L40 15 L60 25 L80 15 L80 75 L60 85 L40 75 L20 85 Z"
                fill="none" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="5" />
            <Line x1="40" y1="15" x2="40" y2="75" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="3" />
            <Line x1="60" y1="25" x2="60" y2="85" stroke={active ? '#58A6FF' : '#8B949E'} strokeWidth="3" />
        </Svg>
    );

    // Render Scorecard Tab
    const renderScorecard = () => (
        <ScrollView style={styles.tabContent}>
            {/* Hole Navigation */}
            <View style={styles.holeNav}>
                <TouchableOpacity
                    style={styles.holeNavBtn}
                    onPress={() => setCurrentHole(Math.max(1, currentHole - 1))}
                >
                    <Text style={styles.holeNavText}>◀</Text>
                </TouchableOpacity>

                <View style={styles.holeInfo}>
                    <Text style={styles.holeNumber}>HOLE {currentHole}</Text>
                    <View style={styles.holeStats}>
                        <View style={styles.holeStat}>
                            <Text style={styles.holeStatValue}>{currentHoleData.par}</Text>
                            <Text style={styles.holeStatLabel}>PAR</Text>
                        </View>
                        <View style={styles.holeStat}>
                            <Text style={styles.holeStatValue}>{currentHoleData.yards}</Text>
                            <Text style={styles.holeStatLabel}>YDS</Text>
                        </View>
                        <View style={styles.holeStat}>
                            <Text style={styles.holeStatValue}>{currentHoleData.handicap}</Text>
                            <Text style={styles.holeStatLabel}>HCP</Text>
                        </View>
                    </View>
                </View>

                <TouchableOpacity
                    style={styles.holeNavBtn}
                    onPress={() => setCurrentHole(Math.min(18, currentHole + 1))}
                >
                    <Text style={styles.holeNavText}>▶</Text>
                </TouchableOpacity>
            </View>

            {/* Score Entry */}
            <View style={styles.scoreEntry}>
                <TouchableOpacity style={styles.scoreBtn} onPress={() => updateScore(-1)}>
                    <Text style={styles.scoreBtnText}>−</Text>
                </TouchableOpacity>

                <View style={styles.scoreDisplay}>
                    <Text style={styles.scoreValue}>{currentScore}</Text>
                    <Text style={[styles.scoreLabel, { color: scoreInfo.color }]}>{scoreInfo.label}</Text>
                </View>

                <TouchableOpacity style={styles.scoreBtn} onPress={() => updateScore(1)}>
                    <Text style={styles.scoreBtnText}>+</Text>
                </TouchableOpacity>
            </View>

            {/* Totals */}
            <View style={styles.totalsRow}>
                <View style={styles.totalItem}>
                    <Text style={styles.totalLabel}>THRU</Text>
                    <Text style={styles.totalValue}>{Object.keys(scores).length}</Text>
                </View>
                <View style={styles.totalDivider} />
                <View style={styles.totalItem}>
                    <Text style={styles.totalLabel}>SCORE</Text>
                    <Text style={styles.totalValue}>{getTotalScore() || '—'}</Text>
                </View>
                <View style={styles.totalDivider} />
                <View style={styles.totalItem}>
                    <Text style={styles.totalLabel}>VS PAR</Text>
                    <Text style={[styles.totalValue, styles.vsParValue]}>{getScoreVsPar()}</Text>
                </View>
            </View>

            {/* Hole Grid */}
            <View style={styles.holeGrid}>
                <Text style={styles.gridTitle}>FRONT 9</Text>
                <View style={styles.holesRow}>
                    {holeData.slice(0, 9).map(hole => (
                        <TouchableOpacity
                            key={hole.hole}
                            style={[
                                styles.holeCell,
                                currentHole === hole.hole && styles.holeCellActive
                            ]}
                            onPress={() => setCurrentHole(hole.hole)}
                        >
                            <Text style={styles.holeCellNum}>{hole.hole}</Text>
                            <View style={[
                                styles.holeCellScore,
                                scores[hole.hole] && { backgroundColor: getScoreLabel(scores[hole.hole], hole.par).color }
                            ]}>
                                <Text style={styles.holeCellScoreText}>{scores[hole.hole] || '—'}</Text>
                            </View>
                        </TouchableOpacity>
                    ))}
                </View>

                <Text style={[styles.gridTitle, { marginTop: 16 }]}>BACK 9</Text>
                <View style={styles.holesRow}>
                    {holeData.slice(9, 18).map(hole => (
                        <TouchableOpacity
                            key={hole.hole}
                            style={[
                                styles.holeCell,
                                currentHole === hole.hole && styles.holeCellActive
                            ]}
                            onPress={() => setCurrentHole(hole.hole)}
                        >
                            <Text style={styles.holeCellNum}>{hole.hole}</Text>
                            <View style={[
                                styles.holeCellScore,
                                scores[hole.hole] && { backgroundColor: getScoreLabel(scores[hole.hole], hole.par).color }
                            ]}>
                                <Text style={styles.holeCellScoreText}>{scores[hole.hole] || '—'}</Text>
                            </View>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>
        </ScrollView>
    );

    // Render Rangefinder Tab
    const renderRangefinder = () => {
        const targets = getHoleTargets();

        return (
            <View style={styles.tabContent}>
                {/* Main Distance Display */}
                <View style={styles.rangeDisplay}>
                    <Svg width={180} height={180} viewBox="0 0 180 180">
                        <Circle cx="90" cy="90" r="80" fill="none" stroke="#2E7D32" strokeWidth="8" />
                        <Circle cx="90" cy="90" r="65" fill="none" stroke="#2E7D32" strokeWidth="2" opacity="0.4" />
                    </Svg>
                    <View style={styles.rangeContent}>
                        <Text style={styles.rangeValue}>{currentHoleData.yards}</Text>
                        <Text style={styles.rangeUnit}>YARDS</Text>
                        <Text style={styles.rangeTarget}>to Center</Text>
                    </View>
                </View>

                {/* GPS Status */}
                <View style={styles.gpsStatus}>
                    <View style={[styles.gpsDot, location && styles.gpsDotActive]} />
                    <Text style={styles.gpsText}>
                        {location ? 'GPS Active' : 'Acquiring GPS...'}
                    </Text>
                </View>

                {/* Targets */}
                <View style={styles.targetsSection}>
                    <Text style={styles.targetsTitle}>HOLE {currentHole} TARGETS</Text>
                    {targets.map((target, idx) => (
                        <View key={idx} style={styles.targetRow}>
                            <View style={[
                                styles.targetDot,
                                { backgroundColor: target.type === 'green' ? '#4CAF50' : '#2196F3' }
                            ]} />
                            <Text style={styles.targetName}>{target.name}</Text>
                            <Text style={styles.targetYards}>{target.yards}</Text>
                        </View>
                    ))}
                </View>

                {/* Club Suggestion */}
                <View style={styles.clubSuggestion}>
                    <Text style={styles.clubLabel}>SUGGESTED CLUB</Text>
                    <Text style={styles.clubName}>
                        {currentHoleData.yards > 200 ? 'Driver' :
                            currentHoleData.yards > 170 ? '3 Wood' :
                                currentHoleData.yards > 150 ? '5 Iron' :
                                    currentHoleData.yards > 130 ? '7 Iron' :
                                        currentHoleData.yards > 100 ? '9 Iron' : 'PW'}
                    </Text>
                </View>
            </View>
        );
    };


    // Render Hole Map Tab - Satellite view with real OSM data when available
    const renderHoleMap = () => {
        const holeYards = currentHoleData.yards;
        const par = currentHoleData.par;

        // Course coordinates from Google Places
        const courseLat = course.lat || 36.1775707;
        const courseLon = course.lon || -95.7516411;

        // Calculate distance between two GPS points
        const getDistance = (lat1, lon1, lat2, lon2) => {
            const R = 6371000;
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            return Math.round(R * c * 1.09361); // yards
        };

        // Get real OSM hole data if available
        const osmHole = courseFeatures?.holes?.find(h => h.ref === String(currentHole));
        const hasRealHoleData = osmHole && osmHole.tee_coord && osmHole.green_coord;

        // Real tee/green coordinates from OSM or fallback to course center
        let teeLat, teeLon, greenLat, greenLon;

        if (hasRealHoleData) {
            teeLat = osmHole.tee_coord[0];
            teeLon = osmHole.tee_coord[1];
            greenLat = osmHole.green_coord[0];
            greenLon = osmHole.green_coord[1];
        } else {
            // Fallback - center on course
            teeLat = courseLat;
            teeLon = courseLon;
            greenLat = courseLat;
            greenLon = courseLon;
        }

        // Check if at course
        const distanceToCourse = location
            ? getDistance(location.latitude, location.longitude, courseLat, courseLon)
            : null;
        const isAtCourse = distanceToCourse !== null && distanceToCourse < 1760;

        // Calculate distance to green from player position
        const distanceToGreen = location && hasRealHoleData
            ? getDistance(location.latitude, location.longitude, greenLat, greenLon)
            : null;

        // Handle map tap
        const handleMapPress = (e) => {
            const { latitude, longitude } = e.nativeEvent.coordinate;
            setTappedPoint({ latitude, longitude });

            if (location) {
                const dist = getDistance(location.latitude, location.longitude, latitude, longitude);
                setDistanceToTap(dist);
            }
        };

        // Map region - center on hole if we have data, otherwise course center
        const centerLat = hasRealHoleData ? (teeLat + greenLat) / 2 : courseLat;
        const centerLon = hasRealHoleData ? (teeLon + greenLon) / 2 : courseLon;

        // Zoom based on hole data availability
        const latDelta = hasRealHoleData ? 0.003 : 0.006;
        const lonDelta = hasRealHoleData ? 0.003 : 0.006;

        // Calculate front/center/back of green distances
        const backEdge = distanceToGreen ? distanceToGreen + 15 : holeYards + 15;
        const greenCenter = distanceToGreen || holeYards;
        const frontEdge = distanceToGreen ? distanceToGreen - 12 : holeYards - 12;

        return (
            <View style={styles.gpsContainer}>
                {/* Left Distance Panel - Like Golfshot */}
                <View style={styles.distancePanel}>
                    <View style={styles.distanceItem}>
                        <Text style={styles.distanceLabel}>Hole</Text>
                        <Text style={styles.distanceNumber}>{currentHole}</Text>
                    </View>

                    <View style={styles.distanceDivider} />

                    <View style={styles.distanceItem}>
                        <Text style={styles.distanceLabel}>Back Edge</Text>
                        <Text style={styles.distanceNumber}>{backEdge}</Text>
                    </View>

                    <View style={[styles.distanceItem, styles.distanceHighlight]}>
                        <Text style={[styles.distanceLabel, styles.distanceLabelHighlight]}>Green Center</Text>
                        <Text style={[styles.distanceNumber, styles.distanceNumberHighlight]}>{greenCenter}</Text>
                    </View>

                    <View style={styles.distanceItem}>
                        <Text style={styles.distanceLabel}>Front Edge</Text>
                        <Text style={styles.distanceNumber}>{frontEdge}</Text>
                    </View>

                    <View style={styles.distanceDivider} />

                    <View style={styles.distanceItem}>
                        <Text style={styles.distanceLabel}>Par</Text>
                        <Text style={styles.distanceNumber}>{osmHole?.par || par}</Text>
                    </View>

                    <View style={styles.distanceItem}>
                        <Text style={styles.distanceLabel}>Handicap</Text>
                        <Text style={styles.distanceNumber}>{currentHoleData.handicap}</Text>
                    </View>
                </View>

                {/* Main Map Area */}
                <View style={styles.mapArea}>
                    <MapView
                        style={styles.fullMap}
                        mapType="satellite"
                        region={{
                            latitude: centerLat,
                            longitude: centerLon,
                            latitudeDelta: latDelta,
                            longitudeDelta: lonDelta,
                        }}
                        showsUserLocation={false}
                        showsCompass={false}
                        rotateEnabled={true}
                        pitchEnabled={false}
                        onPress={handleMapPress}
                    >
                        {/* Line from player to green */}
                        {location && hasRealHoleData && (
                            <Polyline
                                coordinates={[
                                    { latitude: location.latitude, longitude: location.longitude },
                                    { latitude: greenLat, longitude: greenLon }
                                ]}
                                strokeColor="#FFFFFF"
                                strokeWidth={2}
                            />
                        )}

                        {/* Line from player to tapped point */}
                        {location && tappedPoint && (
                            <Polyline
                                coordinates={[
                                    { latitude: location.latitude, longitude: location.longitude },
                                    tappedPoint
                                ]}
                                strokeColor="#4CAF50"
                                strokeWidth={2}
                                lineDashPattern={[8, 4]}
                            />
                        )}

                        {/* Green circles - concentric rings like pro apps */}
                        {hasRealHoleData && (
                            <>
                                <MapCircle
                                    center={{ latitude: greenLat, longitude: greenLon }}
                                    radius={25}
                                    fillColor="rgba(76, 175, 80, 0.15)"
                                    strokeColor="rgba(76, 175, 80, 0.5)"
                                    strokeWidth={1}
                                />
                                <MapCircle
                                    center={{ latitude: greenLat, longitude: greenLon }}
                                    radius={15}
                                    fillColor="rgba(76, 175, 80, 0.25)"
                                    strokeColor="rgba(76, 175, 80, 0.7)"
                                    strokeWidth={1}
                                />
                                <MapCircle
                                    center={{ latitude: greenLat, longitude: greenLon }}
                                    radius={5}
                                    fillColor="rgba(76, 175, 80, 0.4)"
                                    strokeColor="#4CAF50"
                                    strokeWidth={2}
                                />
                            </>
                        )}

                        {/* Pin/Flag marker */}
                        {hasRealHoleData && (
                            <Marker
                                coordinate={{ latitude: greenLat, longitude: greenLon }}
                                anchor={{ x: 0.5, y: 1 }}
                            >
                                <View style={styles.flagMarker}>
                                    <View style={styles.flagTriangle} />
                                    <View style={styles.flagPole} />
                                </View>
                            </Marker>
                        )}

                        {/* Player position - blue dot like pro apps */}
                        {location && (
                            <Marker
                                coordinate={{ latitude: location.latitude, longitude: location.longitude }}
                                anchor={{ x: 0.5, y: 0.5 }}
                            >
                                <View style={styles.playerDotOuter}>
                                    <View style={styles.playerDotInner} />
                                </View>
                            </Marker>
                        )}

                        {/* Tapped point marker with distance */}
                        {tappedPoint && (
                            <Marker
                                coordinate={tappedPoint}
                                anchor={{ x: 0.5, y: 0.5 }}
                            >
                                <View style={styles.distanceBadge}>
                                    <Text style={styles.distanceBadgeText}>{distanceToTap}</Text>
                                </View>
                            </Marker>
                        )}

                        {/* OSM Fairways - the hole overlay like GolfLogix */}
                        {courseFeatures?.fairways?.map((fairway, idx) => (
                            fairway.coords && fairway.coords.length > 2 && (
                                <MapPolygon
                                    key={`fairway-${idx}`}
                                    coordinates={fairway.coords.map(c => ({ latitude: c[0], longitude: c[1] }))}
                                    fillColor="rgba(46, 125, 50, 0.45)"
                                    strokeColor="rgba(76, 175, 80, 0.7)"
                                    strokeWidth={1}
                                />
                            )
                        ))}

                        {/* OSM Greens */}
                        {courseFeatures?.greens?.map((green, idx) => (
                            green.coords && green.coords.length > 2 && (
                                <MapPolygon
                                    key={`green-${idx}`}
                                    coordinates={green.coords.map(c => ({ latitude: c[0], longitude: c[1] }))}
                                    fillColor="rgba(76, 175, 80, 0.6)"
                                    strokeColor="#4CAF50"
                                    strokeWidth={2}
                                />
                            )
                        ))}

                        {/* OSM Tees */}
                        {courseFeatures?.tees?.slice(0, 20).map((tee, idx) => (
                            tee.coords && tee.coords.length > 2 && (
                                <MapPolygon
                                    key={`tee-${idx}`}
                                    coordinates={tee.coords.map(c => ({ latitude: c[0], longitude: c[1] }))}
                                    fillColor="rgba(46, 125, 50, 0.5)"
                                    strokeColor="#2E7D32"
                                    strokeWidth={1}
                                />
                            )
                        ))}

                        {/* OSM Bunkers */}
                        {courseFeatures?.bunkers?.slice(0, 15).map((bunker, idx) => (
                            bunker.coords && bunker.coords.length > 2 && (
                                <MapPolygon
                                    key={`bunker-${idx}`}
                                    coordinates={bunker.coords.map(c => ({ latitude: c[0], longitude: c[1] }))}
                                    fillColor="rgba(212, 197, 150, 0.6)"
                                    strokeColor="#c4b486"
                                    strokeWidth={1}
                                />
                            )
                        ))}

                        {/* OSM Water */}
                        {courseFeatures?.water?.slice(0, 8).map((water, idx) => (
                            water.coords && water.coords.length > 2 && (
                                <MapPolygon
                                    key={`water-${idx}`}
                                    coordinates={water.coords.map(c => ({ latitude: c[0], longitude: c[1] }))}
                                    fillColor="rgba(33, 150, 243, 0.5)"
                                    strokeColor="#1976D2"
                                    strokeWidth={1}
                                />
                            )
                        ))}
                    </MapView>

                    {/* Distance overlay on map - center of green */}
                    <View style={styles.mapDistanceOverlay}>
                        <Text style={styles.mapDistanceText}>{greenCenter}</Text>
                    </View>

                    {/* Tap instruction */}
                    <View style={styles.tapHint}>
                        <Text style={styles.tapHintText}>Tap for distance</Text>
                    </View>
                </View>

                {/* Bottom Navigation Bar */}
                <View style={styles.bottomBar}>
                    <TouchableOpacity
                        style={styles.navArrow}
                        onPress={() => { setTappedPoint(null); setDistanceToTap(null); setCurrentHole(Math.max(1, currentHole - 1)); }}
                    >
                        <Text style={styles.navArrowText}>‹</Text>
                    </TouchableOpacity>

                    <View style={styles.holeInfoBar}>
                        <Text style={styles.holeNumberLarge}>{String(currentHole).padStart(2, '0')}</Text>
                        <View style={styles.holeDetails}>
                            <Text style={styles.holeDetailText}>Par {osmHole?.par || par}</Text>
                            <Text style={styles.holeDetailText}>Handicap {currentHoleData.handicap}</Text>
                        </View>
                    </View>

                    <TouchableOpacity
                        style={styles.navArrow}
                        onPress={() => { setTappedPoint(null); setDistanceToTap(null); setCurrentHole(Math.min(18, currentHole + 1)); }}
                    >
                        <Text style={styles.navArrowText}>›</Text>
                    </TouchableOpacity>
                </View>
            </View>
        );
    };

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <View style={styles.headerInfo}>
                    <Text style={styles.courseName} numberOfLines={1}>{course.name}</Text>
                    <Text style={styles.headerHole}>Hole {currentHole} • Par {currentHoleData.par}</Text>
                </View>
                <TouchableOpacity style={styles.endRoundBtn} onPress={handleEndRound}>
                    <Text style={styles.endRoundText}>End</Text>
                </TouchableOpacity>
            </View>

            {/* Tabs */}
            <View style={styles.tabBar}>
                <TouchableOpacity
                    style={[styles.tab, activeTab === 'map' && styles.tabActive]}
                    onPress={() => setActiveTab('map')}
                >
                    <MapIcon active={activeTab === 'map'} />
                    <Text style={[styles.tabText, activeTab === 'map' && styles.tabTextActive]}>
                        Map
                    </Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={[styles.tab, activeTab === 'scorecard' && styles.tabActive]}
                    onPress={() => setActiveTab('scorecard')}
                >
                    <ScorecardIcon active={activeTab === 'scorecard'} />
                    <Text style={[styles.tabText, activeTab === 'scorecard' && styles.tabTextActive]}>
                        Score
                    </Text>
                </TouchableOpacity>

                <TouchableOpacity
                    style={[styles.tab, activeTab === 'rangefinder' && styles.tabActive]}
                    onPress={() => setActiveTab('rangefinder')}
                >
                    <RangefinderIcon active={activeTab === 'rangefinder'} />
                    <Text style={[styles.tabText, activeTab === 'rangefinder' && styles.tabTextActive]}>
                        GPS
                    </Text>
                </TouchableOpacity>
            </View>

            {/* Active Tab Content */}
            {activeTab === 'map' && renderHoleMap()}
            {activeTab === 'scorecard' && renderScorecard()}
            {activeTab === 'rangefinder' && renderRangefinder()}
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
        paddingBottom: 12,
        backgroundColor: '#161B22',
        borderBottomWidth: 1,
        borderBottomColor: '#21262D',
    },
    headerInfo: {
        flex: 1,
    },
    courseName: {
        color: '#F0F6FC',
        fontSize: 17,
        fontWeight: '600',
        letterSpacing: 0.3,
    },
    headerHole: {
        color: '#58A6FF',
        fontSize: 12,
        marginTop: 3,
        fontWeight: '500',
    },
    endRoundBtn: {
        backgroundColor: 'rgba(248, 81, 73, 0.15)',
        paddingHorizontal: 14,
        paddingVertical: 7,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: 'rgba(248, 81, 73, 0.4)',
    },
    endRoundText: {
        color: '#F85149',
        fontSize: 13,
        fontWeight: '600',
    },
    tabBar: {
        flexDirection: 'row',
        backgroundColor: '#161B22',
        paddingVertical: 4,
        paddingHorizontal: 8,
        borderBottomWidth: 1,
        borderBottomColor: '#21262D',
    },
    tab: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 10,
        marginHorizontal: 4,
        borderRadius: 8,
        gap: 6,
    },
    tabActive: {
        backgroundColor: 'rgba(56, 139, 253, 0.15)',
    },
    tabText: {
        color: '#8B949E',
        fontSize: 13,
        fontWeight: '600',
    },
    tabTextActive: {
        color: '#58A6FF',
    },
    tabContent: {
        flex: 1,
    },
    // Scorecard styles
    holeNav: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: '#161B22',
        borderRadius: 12,
        padding: 16,
        marginBottom: 20,
        marginHorizontal: 16,
        marginTop: 16,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    holeNavBtn: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(48, 54, 61, 0.8)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    holeNavText: {
        color: '#F0F6FC',
        fontSize: 18,
    },
    holeInfo: {
        alignItems: 'center',
    },
    holeNumber: {
        color: '#58A6FF',
        fontSize: 13,
        fontWeight: '700',
        letterSpacing: 2,
    },
    holeStats: {
        flexDirection: 'row',
        marginTop: 8,
        gap: 24,
    },
    holeStat: {
        alignItems: 'center',
    },
    holeStatValue: {
        color: '#F0F6FC',
        fontSize: 20,
        fontWeight: '700',
    },
    holeStatLabel: {
        color: '#8B949E',
        fontSize: 10,
        fontWeight: '500',
        marginTop: 2,
    },
    scoreEntry: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 24,
        gap: 28,
        marginHorizontal: 16,
    },
    scoreBtn: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#238636',
        justifyContent: 'center',
        alignItems: 'center',
        shadowColor: '#238636',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
    },
    scoreBtnText: {
        color: '#F0F6FC',
        fontSize: 28,
        fontWeight: '400',
    },
    scoreDisplay: {
        alignItems: 'center',
        width: 110,
    },
    scoreValue: {
        color: '#F0F6FC',
        fontSize: 60,
        fontWeight: '700',
        fontVariant: ['tabular-nums'],
    },
    scoreLabel: {
        fontSize: 13,
        fontWeight: '700',
    },
    totalsRow: {
        flexDirection: 'row',
        justifyContent: 'center',
        backgroundColor: '#161B22',
        borderRadius: 12,
        paddingVertical: 18,
        marginBottom: 24,
        marginHorizontal: 16,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    totalItem: {
        alignItems: 'center',
        paddingHorizontal: 28,
    },
    totalLabel: {
        color: '#8B949E',
        fontSize: 10,
        letterSpacing: 1,
        fontWeight: '600',
    },
    totalValue: {
        color: '#F0F6FC',
        fontSize: 24,
        fontWeight: '700',
        marginTop: 4,
        fontVariant: ['tabular-nums'],
    },
    vsParValue: {
        color: '#3FB950',
    },
    totalDivider: {
        width: 1,
        backgroundColor: '#21262D',
    },
    holeGrid: {
        marginBottom: 20,
        marginHorizontal: 16,
    },
    gridTitle: {
        color: '#58A6FF',
        fontSize: 11,
        fontWeight: '700',
        marginBottom: 10,
        letterSpacing: 1,
    },
    holesRow: {
        flexDirection: 'row',
        gap: 6,
    },
    holeCell: {
        flex: 1,
        aspectRatio: 0.9,
        backgroundColor: '#161B22',
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 4,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    holeCellActive: {
        backgroundColor: 'rgba(56, 139, 253, 0.2)',
        borderWidth: 1,
        borderColor: '#58A6FF',
    },
    holeCellNum: {
        color: '#F0F6FC',
        fontSize: 11,
        fontWeight: '700',
    },
    holeCellScore: {
        marginTop: 4,
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: 'rgba(48, 54, 61, 0.8)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    holeCellScoreText: {
        color: '#F0F6FC',
        fontSize: 11,
        fontWeight: '700',
    },
    // Rangefinder styles
    rangeDisplay: {
        alignItems: 'center',
        justifyContent: 'center',
        marginVertical: 20,
        marginHorizontal: 16,
    },
    rangeContent: {
        position: 'absolute',
        alignItems: 'center',
    },
    rangeValue: {
        color: '#F0F6FC',
        fontSize: 48,
        fontWeight: 'bold',
    },
    rangeUnit: {
        color: '#4CAF50',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 2,
    },
    rangeTarget: {
        color: '#888',
        fontSize: 12,
        marginTop: 4,
    },
    gpsStatus: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 24,
    },
    gpsDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#FF5722',
        marginRight: 8,
    },
    gpsDotActive: {
        backgroundColor: '#4CAF50',
    },
    gpsText: {
        color: '#888',
        fontSize: 12,
    },
    targetsSection: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 16,
        padding: 16,
        marginBottom: 20,
    },
    targetsTitle: {
        color: '#4CAF50',
        fontSize: 12,
        fontWeight: 'bold',
        marginBottom: 12,
    },
    targetRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 10,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.05)',
    },
    targetDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 12,
    },
    targetName: {
        flex: 1,
        color: '#FFF',
        fontSize: 15,
    },
    targetYards: {
        color: '#FFF',
        fontSize: 20,
        fontWeight: 'bold',
    },
    clubSuggestion: {
        backgroundColor: 'rgba(46, 125, 50, 0.2)',
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
    },
    clubLabel: {
        color: '#4CAF50',
        fontSize: 11,
        letterSpacing: 1,
    },
    clubName: {
        color: '#FFF',
        fontSize: 24,
        fontWeight: 'bold',
        marginTop: 4,
    },
    // Hole Map styles
    mapHoleInfo: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
    },
    mapHoleLeft: {},
    mapHoleNumber: {
        color: '#4CAF50',
        fontSize: 14,
        fontWeight: 'bold',
        letterSpacing: 2,
    },
    mapHolePar: {
        color: '#888',
        fontSize: 13,
        marginTop: 2,
    },
    mapDistanceBox: {
        backgroundColor: '#2E7D32',
        borderRadius: 12,
        paddingHorizontal: 16,
        paddingVertical: 10,
        alignItems: 'center',
    },
    mapDistanceValue: {
        color: '#FFF',
        fontSize: 28,
        fontWeight: 'bold',
    },
    mapDistanceLabel: {
        color: 'rgba(255,255,255,0.7)',
        fontSize: 10,
        letterSpacing: 1,
    },
    mapCanvas: {
        borderRadius: 12,
        overflow: 'hidden',
        marginBottom: 16,
        position: 'relative',
    },
    mapDistanceMarker: {
        position: 'absolute',
        backgroundColor: 'rgba(0,0,0,0.7)',
        borderRadius: 8,
        paddingHorizontal: 8,
        paddingVertical: 4,
        alignItems: 'center',
    },
    mapMarkerYards: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: 'bold',
    },
    mapMarkerLabel: {
        color: '#4CAF50',
        fontSize: 9,
    },
    mapDistanceCards: {
        flexDirection: 'row',
        gap: 10,
        marginBottom: 16,
    },
    mapCard: {
        flex: 1,
        borderRadius: 12,
        paddingVertical: 12,
        alignItems: 'center',
    },
    mapCardGreen: {
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
    },
    mapCardLabel: {
        color: '#4CAF50',
        fontSize: 10,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
    mapCardValue: {
        color: '#FFF',
        fontSize: 22,
        fontWeight: 'bold',
        marginTop: 4,
    },
    mapHazards: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 12,
        padding: 16,
    },
    mapHazardsTitle: {
        color: '#FF9800',
        fontSize: 11,
        fontWeight: 'bold',
        letterSpacing: 1,
        marginBottom: 12,
    },
    mapHazardRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 8,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255, 255, 255, 0.05)',
    },
    mapHazardDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 12,
    },
    mapHazardName: {
        flex: 1,
        color: '#FFF',
        fontSize: 14,
    },
    mapHazardYards: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    // New map styles
    mapBadge: {
        position: 'absolute',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        borderRadius: 12,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderWidth: 2,
        borderColor: '#4CAF50',
    },
    mapBadgeSmall: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 8,
        borderColor: '#888',
    },
    mapBadgeText: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
    mapBadgeTextSmall: {
        color: '#FFF',
        fontSize: 12,
        fontWeight: '600',
    },
    mapHoleNav: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 16,
        marginBottom: 30,
        paddingHorizontal: 10,
    },
    mapNavBtn: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        paddingHorizontal: 20,
        paddingVertical: 12,
        borderRadius: 10,
    },
    mapNavText: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: '600',
    },
    mapNavHole: {
        color: '#4CAF50',
        fontSize: 16,
        fontWeight: 'bold',
    },
    // Satellite map styles
    satelliteMapContainer: {
        height: 350,
        borderRadius: 16,
        overflow: 'hidden',
        marginBottom: 16,
        position: 'relative',
    },
    satelliteMap: {
        flex: 1,
    },
    pinMarker: {
        alignItems: 'center',
    },
    pinFlag: {
        width: 18,
        height: 12,
        backgroundColor: '#e53935',
        marginLeft: 1,
    },
    pinPole: {
        width: 2,
        height: 25,
        backgroundColor: '#FFF',
    },
    teeMarker: {
        backgroundColor: '#5d4e37',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        borderWidth: 1,
        borderColor: '#FFF',
    },
    teeMarkerText: {
        color: '#FFF',
        fontSize: 10,
        fontWeight: 'bold',
    },
    playerMarker: {
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: 'rgba(33, 150, 243, 0.3)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    playerDot: {
        width: 14,
        height: 14,
        borderRadius: 7,
        backgroundColor: '#2196F3',
        borderWidth: 2,
        borderColor: '#FFF',
    },
    mapOverlay: {
        position: 'absolute',
        top: 10,
        left: 0,
        right: 0,
        alignItems: 'center',
    },
    distanceOverlayBadge: {
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
        borderWidth: 2,
        borderColor: '#4CAF50',
        alignItems: 'center',
    },
    distanceOverlayValue: {
        color: '#FFF',
        fontSize: 24,
        fontWeight: 'bold',
    },
    distanceOverlayLabel: {
        color: '#4CAF50',
        fontSize: 11,
    },
    gpsIndicator: {
        position: 'absolute',
        bottom: 10,
        left: 10,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 12,
    },
    gpsDotIndicator: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: '#FF5722',
        marginRight: 6,
    },
    gpsIndicatorText: {
        color: '#FFF',
        fontSize: 11,
    },
    gpsDotActive: {
        backgroundColor: '#4CAF50',
    },
    dataSourceIndicator: {
        position: 'absolute',
        bottom: 10,
        right: 10,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 12,
    },
    dataSourceText: {
        color: '#FFF',
        fontSize: 11,
    },
    notAtCourseWarning: {
        backgroundColor: 'rgba(255, 152, 0, 0.9)',
        paddingVertical: 10,
        paddingHorizontal: 16,
        borderRadius: 8,
        marginBottom: 10,
    },
    notAtCourseText: {
        color: '#FFF',
        fontSize: 13,
        textAlign: 'center',
        fontWeight: '500',
    },
    // New SVG hole diagram styles
    holeHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
    },
    holeHeaderNumber: {
        color: '#4CAF50',
        fontSize: 24,
        fontWeight: 'bold',
    },
    holeHeaderDetails: {
        color: 'rgba(255, 255, 255, 0.7)',
        fontSize: 14,
        marginTop: 4,
    },
    holeHeaderDistance: {
        alignItems: 'center',
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
        paddingHorizontal: 16,
        paddingVertical: 10,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#4CAF50',
    },
    holeHeaderDistanceValue: {
        color: '#FFF',
        fontSize: 28,
        fontWeight: 'bold',
    },
    holeHeaderDistanceLabel: {
        color: '#4CAF50',
        fontSize: 11,
        fontWeight: '600',
    },
    holeDiagram: {
        backgroundColor: '#1a3a1a',
        borderRadius: 20,
        overflow: 'hidden',
        marginBottom: 16,
        position: 'relative',
    },
    distanceLabel: {
        position: 'absolute',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        paddingHorizontal: 12,
        paddingVertical: 4,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#4CAF50',
    },
    distanceLabelText: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    distanceLabelSmall: {
        position: 'absolute',
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 8,
    },
    distanceLabelTextSmall: {
        color: '#FFF',
        fontSize: 10,
        fontWeight: '600',
    },
    hazardInfo: {
        backgroundColor: 'rgba(255, 152, 0, 0.1)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: 'rgba(255, 152, 0, 0.3)',
    },
    hazardInfoTitle: {
        color: '#FF9800',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 1,
        marginBottom: 12,
    },
    hazardRow: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingVertical: 8,
    },
    hazardDot: {
        width: 12,
        height: 12,
        borderRadius: 6,
        marginRight: 12,
    },
    hazardName: {
        color: '#FFF',
        fontSize: 14,
        flex: 1,
    },
    hazardDistance: {
        color: '#4CAF50',
        fontSize: 14,
        fontWeight: 'bold',
    },
    tapMarker: {
        backgroundColor: '#4CAF50',
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 16,
        borderWidth: 2,
        borderColor: '#FFF',
    },
    tapMarkerText: {
        color: '#FFF',
        fontSize: 14,
        fontWeight: 'bold',
    },
    mapInstructions: {
        position: 'absolute',
        bottom: 10,
        left: '50%',
        transform: [{ translateX: -80 }],
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
    },
    mapInstructionsText: {
        color: '#FFF',
        fontSize: 12,
    },
    // Tee and pin markers
    teeMarker: {
        backgroundColor: '#2196F3',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        borderWidth: 2,
        borderColor: '#FFF',
    },
    teeMarkerText: {
        color: '#FFF',
        fontSize: 10,
        fontWeight: 'bold',
    },
    pinMarker: {
        alignItems: 'center',
    },
    pinFlag: {
        width: 0,
        height: 0,
        borderLeftWidth: 15,
        borderRightWidth: 0,
        borderBottomWidth: 8,
        borderTopWidth: 8,
        borderLeftColor: '#e53935',
        borderRightColor: 'transparent',
        borderBottomColor: 'transparent',
        borderTopColor: 'transparent',
    },
    pinPole: {
        width: 2,
        height: 20,
        backgroundColor: '#FFF',
        marginTop: -1,
    },
    // Professional GPS Layout Styles
    gpsContainer: {
        flex: 1,
        flexDirection: 'row',
        backgroundColor: '#010409',
    },
    distancePanel: {
        width: 105,
        backgroundColor: '#0D1117',
        paddingVertical: 16,
        paddingHorizontal: 10,
        borderRightWidth: 1,
        borderRightColor: '#21262D',
    },
    distanceItem: {
        alignItems: 'center',
        paddingVertical: 12,
    },
    distanceHighlight: {
        backgroundColor: 'rgba(46, 160, 67, 0.15)',
        marginHorizontal: -10,
        paddingHorizontal: 10,
        borderLeftWidth: 3,
        borderLeftColor: '#3FB950',
        borderRadius: 0,
    },
    distanceLabel: {
        color: '#8B949E',
        fontSize: 9,
        fontWeight: '600',
        textTransform: 'uppercase',
        letterSpacing: 0.8,
    },
    distanceLabelHighlight: {
        color: '#3FB950',
    },
    distanceNumber: {
        color: '#F0F6FC',
        fontSize: 32,
        fontWeight: '700',
        marginTop: 4,
        fontVariant: ['tabular-nums'],
    },
    distanceNumberHighlight: {
        color: '#3FB950',
    },
    distanceDivider: {
        height: 1,
        backgroundColor: '#21262D',
        marginVertical: 10,
        marginHorizontal: -10,
    },
    mapArea: {
        flex: 1,
        position: 'relative',
    },
    fullMap: {
        flex: 1,
    },
    mapDistanceOverlay: {
        position: 'absolute',
        top: '40%',
        left: '50%',
        transform: [{ translateX: -40 }, { translateY: -22 }],
        backgroundColor: 'rgba(13, 17, 23, 0.9)',
        paddingHorizontal: 18,
        paddingVertical: 10,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: 'rgba(48, 54, 61, 0.8)',
    },
    mapDistanceText: {
        color: '#F0F6FC',
        fontSize: 30,
        fontWeight: '700',
        fontVariant: ['tabular-nums'],
    },
    tapHint: {
        position: 'absolute',
        bottom: 65,
        left: '50%',
        transform: [{ translateX: -50 }],
        backgroundColor: 'rgba(13, 17, 23, 0.8)',
        paddingHorizontal: 14,
        paddingVertical: 6,
        borderRadius: 20,
        borderWidth: 1,
        borderColor: 'rgba(48, 54, 61, 0.6)',
    },
    tapHintText: {
        color: '#8B949E',
        fontSize: 11,
        fontWeight: '500',
    },
    bottomBar: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        backgroundColor: 'rgba(13, 17, 23, 0.97)',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingVertical: 14,
        paddingHorizontal: 20,
        paddingBottom: 28,
        borderTopWidth: 1,
        borderTopColor: '#21262D',
    },
    navArrow: {
        width: 48,
        height: 48,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(48, 54, 61, 0.5)',
        borderRadius: 24,
    },
    navArrowText: {
        color: '#F0F6FC',
        fontSize: 28,
        fontWeight: '300',
        marginTop: -2,
    },
    holeInfoBar: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    holeNumberLarge: {
        color: '#F0F6FC',
        fontSize: 42,
        fontWeight: '700',
        marginRight: 14,
        fontVariant: ['tabular-nums'],
    },
    holeDetails: {
        alignItems: 'flex-start',
    },
    holeDetailText: {
        color: '#8B949E',
        fontSize: 13,
        fontWeight: '500',
        lineHeight: 18,
    },
    // Player dot styles
    playerDotOuter: {
        width: 28,
        height: 28,
        borderRadius: 14,
        backgroundColor: 'rgba(56, 139, 253, 0.25)',
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 2,
        borderColor: '#58A6FF',
        shadowColor: '#58A6FF',
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.5,
        shadowRadius: 8,
    },
    playerDotInner: {
        width: 12,
        height: 12,
        borderRadius: 6,
        backgroundColor: '#58A6FF',
    },
    // Distance badge for tapped points
    distanceBadge: {
        backgroundColor: 'rgba(13, 17, 23, 0.95)',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: '#3FB950',
    },
    distanceBadgeText: {
        color: '#F0F6FC',
        fontSize: 15,
        fontWeight: '700',
        fontVariant: ['tabular-nums'],
    },
    // Flag marker styles
    flagMarker: {
        alignItems: 'flex-start',
    },
    flagTriangle: {
        width: 0,
        height: 0,
        borderLeftWidth: 0,
        borderRightWidth: 14,
        borderBottomWidth: 7,
        borderTopWidth: 7,
        borderLeftColor: 'transparent',
        borderRightColor: '#e53935',
        borderBottomColor: 'transparent',
        borderTopColor: 'transparent',
    },
    flagPole: {
        width: 2,
        height: 24,
        backgroundColor: '#FFF',
        marginLeft: 0,
        marginTop: -7,
    },
});
