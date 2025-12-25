import React, { useState, useEffect } from 'react';
import {
    StyleSheet, Text, View, TouchableOpacity, ScrollView,
    Modal, Alert, Dimensions
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { getClubs, recordShotForClub, savePracticeSession } from './services/storage';
import CaptureScreen from './CaptureScreen';

// Safe haptics - won't crash if not installed
let Haptics = null;
try {
    Haptics = require('expo-haptics');
} catch (e) {
    console.log('expo-haptics not available');
}

const triggerHaptic = (type = 'success') => {
    if (!Haptics) return;
    try {
        if (type === 'success') {
            Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        } else if (type === 'impact') {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        } else if (type === 'selection') {
            Haptics.selectionAsync();
        }
    } catch (e) { }
};

const { width: SCREEN_WIDTH } = Dimensions.get('window');


export default function PracticeModeScreen({ onBack }) {
    const [clubs, setClubs] = useState([]);
    const [selectedClub, setSelectedClub] = useState(null);
    const [shots, setShots] = useState([]);
    const [showClubPicker, setShowClubPicker] = useState(false);
    const [sessionStartTime, setSessionStartTime] = useState(Date.now());
    const [showARTracking, setShowARTracking] = useState(false);

    useEffect(() => {
        loadClubs();
    }, []);

    const loadClubs = async () => {
        const loadedClubs = await getClubs();
        setClubs(loadedClubs.filter(c => c.type !== 'putter'));
        if (loadedClubs.length > 0) {
            setSelectedClub(loadedClubs.find(c => c.type === 'iron') || loadedClubs[0]);
        }
    };

    const handleAddShot = (distance, source = 'manual') => {
        if (!selectedClub) return;

        const newShot = {
            id: Date.now().toString(),
            clubId: selectedClub.id,
            clubName: selectedClub.name,
            distance: distance,
            timestamp: Date.now(),
            source: source, // 'manual' or 'ar'
        };

        setShots([newShot, ...shots]);
        recordShotForClub(selectedClub.id, distance);
        triggerHaptic('impact');
    };

    const handleARShotResult = (data) => {
        setShowARTracking(false);
        if (data && data.carry_distance_yards) {
            const distance = Math.round(data.carry_distance_yards);
            handleAddShot(distance, 'ar');
            Alert.alert(
                'Shot Tracked!',
                `${selectedClub?.name || 'Club'}: ${distance} yards`,
                [{ text: 'OK' }]
            );
        }
    };

    const handleEndSession = async () => {
        if (shots.length === 0) {
            onBack();
            return;
        }

        Alert.alert(
            'End Practice Session',
            `Save ${shots.length} shots to your history?`,
            [
                {
                    text: 'Discard',
                    style: 'destructive',
                    onPress: onBack
                },
                {
                    text: 'Save & Exit',
                    onPress: async () => {
                        await savePracticeSession({
                            shots: shots,
                            duration: Date.now() - sessionStartTime,
                        });
                        triggerHaptic('success');
                        onBack();
                    }
                },
            ]
        );
    };

    const getSessionStats = () => {
        if (shots.length === 0) return { count: 0, avg: 0, longest: 0, shortest: 0 };

        const distances = shots.map(s => s.distance);
        return {
            count: shots.length,
            avg: Math.round(distances.reduce((a, b) => a + b, 0) / distances.length),
            longest: Math.max(...distances),
            shortest: Math.min(...distances),
        };
    };

    const getClubStats = () => {
        const clubShots = {};
        shots.forEach(shot => {
            if (!clubShots[shot.clubName]) {
                clubShots[shot.clubName] = [];
            }
            clubShots[shot.clubName].push(shot.distance);
        });

        return Object.entries(clubShots).map(([name, distances]) => ({
            name,
            count: distances.length,
            avg: Math.round(distances.reduce((a, b) => a + b, 0) / distances.length),
        }));
    };

    const stats = getSessionStats();
    const clubStats = getClubStats();

    // Quick distance buttons based on selected club
    const getQuickDistances = () => {
        if (!selectedClub) return [100, 125, 150, 175, 200];
        const base = selectedClub.typicalDistance || 150;
        return [
            Math.round(base * 0.8),
            Math.round(base * 0.9),
            base,
            Math.round(base * 1.05),
            Math.round(base * 1.1),
        ];
    };

    // Show AR Tracking screen when active
    if (showARTracking) {
        return (
            <CaptureScreen
                onClose={() => setShowARTracking(false)}
                onShotAnalyzed={handleARShotResult}
            />
        );
    }

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={handleEndSession} style={styles.backButton}>
                    <Ionicons name="close" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <View style={styles.headerCenter}>
                    <Text style={styles.headerTitle}>Practice Mode</Text>
                    <Text style={styles.headerSubtitle}>
                        {shots.length} shots • {Math.floor((Date.now() - sessionStartTime) / 60000)}m
                    </Text>
                </View>
                <TouchableOpacity onPress={handleEndSession} style={styles.endButton}>
                    <Text style={styles.endButtonText}>End</Text>
                </TouchableOpacity>
            </View>

            <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
                {/* Club Selector */}
                <TouchableOpacity
                    style={styles.clubSelector}
                    onPress={() => setShowClubPicker(true)}
                >
                    <View style={styles.clubSelectorIcon}>
                        <MaterialCommunityIcons name="golf" size={28} color="#3FB950" />
                    </View>
                    <View style={styles.clubSelectorInfo}>
                        <Text style={styles.clubSelectorLabel}>Current Club</Text>
                        <Text style={styles.clubSelectorName}>
                            {selectedClub?.name || 'Select a club'}
                        </Text>
                    </View>
                    <Ionicons name="chevron-down" size={24} color="#8B949E" />
                </TouchableOpacity>

                {/* Quick Add Buttons */}
                <View style={styles.quickAddSection}>
                    <Text style={styles.sectionLabel}>QUICK ADD SHOT</Text>
                    <View style={styles.quickButtons}>
                        {getQuickDistances().map((distance, index) => (
                            <TouchableOpacity
                                key={index}
                                style={[
                                    styles.quickButton,
                                    index === 2 && styles.quickButtonHighlight
                                ]}
                                onPress={() => handleAddShot(distance)}
                            >
                                <Text style={[
                                    styles.quickButtonText,
                                    index === 2 && styles.quickButtonTextHighlight
                                ]}>
                                    {distance}
                                </Text>
                                <Text style={styles.quickButtonUnit}>yds</Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    {/* AR Track Shot Button */}
                    <TouchableOpacity
                        style={styles.arTrackButton}
                        onPress={() => setShowARTracking(true)}
                    >
                        <View style={styles.arTrackIconContainer}>
                            <MaterialCommunityIcons name="camera" size={24} color="#3FB950" />
                        </View>
                        <View style={styles.arTrackInfo}>
                            <Text style={styles.arTrackTitle}>AR Track Shot</Text>
                            <Text style={styles.arTrackSubtitle}>Use camera to track real shot distance</Text>
                        </View>
                        <Ionicons name="chevron-forward" size={20} color="#8B949E" />
                    </TouchableOpacity>
                </View>

                {/* Session Stats */}
                {shots.length > 0 && (
                    <View style={styles.statsSection}>
                        <Text style={styles.sectionLabel}>SESSION STATS</Text>
                        <View style={styles.statsGrid}>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{stats.count}</Text>
                                <Text style={styles.statLabel}>Shots</Text>
                            </View>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{stats.avg}</Text>
                                <Text style={styles.statLabel}>Avg (yds)</Text>
                            </View>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{stats.longest}</Text>
                                <Text style={styles.statLabel}>Longest</Text>
                            </View>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{stats.shortest}</Text>
                                <Text style={styles.statLabel}>Shortest</Text>
                            </View>
                        </View>
                    </View>
                )}

                {/* Club Breakdown */}
                {clubStats.length > 0 && (
                    <View style={styles.breakdownSection}>
                        <Text style={styles.sectionLabel}>BY CLUB</Text>
                        {clubStats.map((club, index) => (
                            <View key={index} style={styles.clubRow}>
                                <View style={styles.clubRowIcon}>
                                    <MaterialCommunityIcons name="golf" size={18} color="#3FB950" />
                                </View>
                                <Text style={styles.clubRowName}>{club.name}</Text>
                                <Text style={styles.clubRowCount}>{club.count} shots</Text>
                                <Text style={styles.clubRowAvg}>{club.avg} yds avg</Text>
                            </View>
                        ))}
                    </View>
                )}

                {/* Recent Shots */}
                {shots.length > 0 && (
                    <View style={styles.recentSection}>
                        <Text style={styles.sectionLabel}>RECENT SHOTS</Text>
                        {shots.slice(0, 10).map((shot, index) => (
                            <View key={shot.id} style={styles.shotRow}>
                                <Text style={styles.shotNumber}>#{shots.length - index}</Text>
                                <Text style={styles.shotClub}>{shot.clubName}</Text>
                                {shot.source === 'ar' && (
                                    <View style={styles.arBadge}>
                                        <Text style={styles.arBadgeText}>AR</Text>
                                    </View>
                                )}
                                <Text style={styles.shotDistance}>{shot.distance} yds</Text>
                            </View>
                        ))}
                    </View>
                )}

                {/* Empty State */}
                {shots.length === 0 && (
                    <View style={styles.emptyState}>
                        <MaterialCommunityIcons name="golf-tee" size={64} color="#21262D" />
                        <Text style={styles.emptyTitle}>Ready to Practice</Text>
                        <Text style={styles.emptyText}>
                            Use quick-add buttons or AR Track Shot to record distances and build your club profile.
                        </Text>
                    </View>
                )}

                <View style={{ height: 100 }} />
            </ScrollView>

            {/* Club Picker Modal */}
            <Modal
                visible={showClubPicker}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setShowClubPicker(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Select Club</Text>
                            <TouchableOpacity onPress={() => setShowClubPicker(false)}>
                                <Ionicons name="close" size={24} color="#8B949E" />
                            </TouchableOpacity>
                        </View>
                        <ScrollView style={styles.clubList}>
                            {clubs.map(club => (
                                <TouchableOpacity
                                    key={club.id}
                                    style={[
                                        styles.clubOption,
                                        selectedClub?.id === club.id && styles.clubOptionActive
                                    ]}
                                    onPress={() => {
                                        setSelectedClub(club);
                                        setShowClubPicker(false);
                                        triggerHaptic('selection');
                                    }}
                                >
                                    <MaterialCommunityIcons
                                        name="golf"
                                        size={24}
                                        color={selectedClub?.id === club.id ? '#3FB950' : '#8B949E'}
                                    />
                                    <Text style={[
                                        styles.clubOptionText,
                                        selectedClub?.id === club.id && styles.clubOptionTextActive
                                    ]}>
                                        {club.name}
                                    </Text>
                                    <Text style={styles.clubOptionDistance}>
                                        {club.typicalDistance} yds
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </ScrollView>
                    </View>
                </View>
            </Modal>
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
        paddingBottom: 16,
        paddingHorizontal: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#21262D',
    },
    backButton: {
        padding: 8,
    },
    headerCenter: {
        alignItems: 'center',
    },
    headerTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    headerSubtitle: {
        fontSize: 12,
        color: '#8B949E',
        marginTop: 2,
    },
    endButton: {
        backgroundColor: '#238636',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 8,
    },
    endButtonText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: 16,
    },
    clubSelector: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#161B22',
        borderRadius: 16,
        padding: 16,
        marginBottom: 24,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    clubSelectorIcon: {
        width: 56,
        height: 56,
        borderRadius: 28,
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 16,
    },
    clubSelectorInfo: {
        flex: 1,
    },
    clubSelectorLabel: {
        fontSize: 12,
        color: '#8B949E',
        marginBottom: 4,
    },
    clubSelectorName: {
        fontSize: 20,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    quickAddSection: {
        marginBottom: 24,
    },
    sectionLabel: {
        fontSize: 12,
        fontWeight: '600',
        color: '#8B949E',
        letterSpacing: 1,
        marginBottom: 12,
    },
    quickButtons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 10,
    },
    quickButton: {
        flex: 1,
        backgroundColor: '#161B22',
        borderRadius: 12,
        paddingVertical: 20,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#21262D',
    },
    quickButtonHighlight: {
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        borderColor: '#3FB950',
    },
    quickButtonText: {
        fontSize: 20,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    quickButtonTextHighlight: {
        color: '#3FB950',
    },
    quickButtonUnit: {
        fontSize: 10,
        color: '#8B949E',
        marginTop: 2,
    },
    arTrackButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#161B22',
        borderRadius: 12,
        padding: 16,
        marginTop: 16,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    arTrackIconContainer: {
        width: 48,
        height: 48,
        borderRadius: 24,
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 14,
    },
    arTrackInfo: {
        flex: 1,
    },
    arTrackTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#F0F6FC',
    },
    arTrackSubtitle: {
        fontSize: 12,
        color: '#8B949E',
        marginTop: 2,
    },
    statsSection: {
        marginBottom: 24,
    },
    statsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 10,
    },
    statCard: {
        width: (SCREEN_WIDTH - 52) / 4,
        backgroundColor: '#161B22',
        borderRadius: 12,
        paddingVertical: 16,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#21262D',
    },
    statValue: {
        fontSize: 24,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    statLabel: {
        fontSize: 10,
        color: '#8B949E',
        marginTop: 4,
    },
    breakdownSection: {
        marginBottom: 24,
    },
    clubRow: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#161B22',
        borderRadius: 10,
        padding: 14,
        marginBottom: 8,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    clubRowIcon: {
        marginRight: 12,
    },
    clubRowName: {
        flex: 1,
        fontSize: 15,
        fontWeight: '600',
        color: '#F0F6FC',
    },
    clubRowCount: {
        fontSize: 13,
        color: '#8B949E',
        marginRight: 16,
    },
    clubRowAvg: {
        fontSize: 14,
        fontWeight: '600',
        color: '#3FB950',
    },
    recentSection: {
        marginBottom: 24,
    },
    shotRow: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#161B22',
        borderRadius: 8,
        padding: 12,
        marginBottom: 6,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    shotNumber: {
        fontSize: 12,
        color: '#8B949E',
        width: 30,
    },
    shotClub: {
        flex: 1,
        fontSize: 14,
        color: '#F0F6FC',
    },
    shotDistance: {
        fontSize: 15,
        fontWeight: '600',
        color: '#3FB950',
    },
    arBadge: {
        backgroundColor: 'rgba(88, 166, 255, 0.2)',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4,
        marginRight: 8,
    },
    arBadgeText: {
        fontSize: 10,
        fontWeight: '700',
        color: '#58A6FF',
    },
    emptyState: {
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: '#F0F6FC',
        marginTop: 16,
        marginBottom: 8,
    },
    emptyText: {
        fontSize: 14,
        color: '#8B949E',
        textAlign: 'center',
        lineHeight: 22,
        paddingHorizontal: 40,
    },
    // Modal styles
    modalOverlay: {
        flex: 1,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        justifyContent: 'flex-end',
    },
    modalContent: {
        backgroundColor: '#161B22',
        borderTopLeftRadius: 24,
        borderTopRightRadius: 24,
        maxHeight: '70%',
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#21262D',
    },
    modalTitle: {
        fontSize: 20,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    clubList: {
        padding: 16,
    },
    clubOption: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        borderRadius: 10,
        marginBottom: 8,
        backgroundColor: '#0D1117',
        borderWidth: 1,
        borderColor: '#21262D',
    },
    clubOptionActive: {
        backgroundColor: 'rgba(63, 185, 80, 0.1)',
        borderColor: '#3FB950',
    },
    clubOptionText: {
        flex: 1,
        fontSize: 16,
        color: '#F0F6FC',
        marginLeft: 12,
    },
    clubOptionTextActive: {
        color: '#3FB950',
        fontWeight: '600',
    },
    clubOptionDistance: {
        fontSize: 14,
        color: '#8B949E',
    },
});
