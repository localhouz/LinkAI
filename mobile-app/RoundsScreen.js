import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { getRounds, deleteRound } from './services/storage';

export default function RoundsScreen({ onBack, onStartRound }) {
    const [activeTab, setActiveTab] = useState('recent');
    const [loading, setLoading] = useState(true);
    const [rounds, setRounds] = useState([]);

    useEffect(() => {
        loadRounds();
    }, []);

    const loadRounds = async () => {
        setLoading(true);
        try {
            const loadedRounds = await getRounds();
            setRounds(loadedRounds);
        } catch (error) {
            console.error('Error loading rounds:', error);
        }
        setLoading(false);
    };

    // Get filtered rounds based on active tab
    const getFilteredRounds = () => {
        if (activeTab === 'best') {
            return [...rounds].sort((a, b) => (a.totalScore || 999) - (b.totalScore || 999)).slice(0, 10);
        }
        return rounds;
    };

    const getScoreDiff = (score, par) => {
        if (!score || !par) return { text: '--', color: '#8B949E' };
        const diff = score - par;
        if (diff === 0) return { text: 'E', color: '#4CAF50' };
        if (diff > 0) return { text: `+${diff}`, color: '#f44336' };
        return { text: `${diff}`, color: '#2196F3' };
    };

    // Flag icon for course
    const FlagIcon = () => (
        <MaterialCommunityIcons name="flag-variant" size={24} color="#4CAF50" />
    );

    const recentRounds = getFilteredRounds();

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>My Rounds</Text>
                <View style={styles.placeholder} />
            </View>

            {/* Tab Bar */}
            <View style={styles.tabBar}>
                <TouchableOpacity
                    style={[styles.tab, activeTab === 'recent' && styles.tabActive]}
                    onPress={() => setActiveTab('recent')}
                >
                    <Text style={[styles.tabText, activeTab === 'recent' && styles.tabTextActive]}>
                        Recent
                    </Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.tab, activeTab === 'best' && styles.tabActive]}
                    onPress={() => setActiveTab('best')}
                >
                    <Text style={[styles.tabText, activeTab === 'best' && styles.tabTextActive]}>
                        Best Scores
                    </Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.tab, activeTab === 'courses' && styles.tabActive]}
                    onPress={() => setActiveTab('courses')}
                >
                    <Text style={[styles.tabText, activeTab === 'courses' && styles.tabTextActive]}>
                        By Course
                    </Text>
                </TouchableOpacity>
            </View>

            {/* Quick Stats */}
            <View style={styles.quickStats}>
                <View style={styles.quickStatItem}>
                    <Text style={styles.quickStatValue}>{rounds.length}</Text>
                    <Text style={styles.quickStatLabel}>Total Rounds</Text>
                </View>
                <View style={styles.quickStatItem}>
                    <Text style={styles.quickStatValue}>
                        {rounds.length > 0
                            ? Math.round(rounds.filter(r => r.totalScore).reduce((sum, r) => sum + r.totalScore, 0) / rounds.filter(r => r.totalScore).length || '--')
                            : '--'
                        }
                    </Text>
                    <Text style={styles.quickStatLabel}>Avg Score</Text>
                </View>
                <View style={styles.quickStatItem}>
                    <Text style={styles.quickStatValue}>
                        {rounds.length > 0 && rounds.some(r => r.totalScore)
                            ? Math.min(...rounds.filter(r => r.totalScore).map(r => r.totalScore))
                            : '--'
                        }
                    </Text>
                    <Text style={styles.quickStatLabel}>Best Round</Text>
                </View>
            </View>

            {/* Rounds List */}
            <ScrollView style={styles.roundsList}>
                {loading ? (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator size="large" color="#3FB950" />
                    </View>
                ) : recentRounds.length === 0 ? (
                    <View style={styles.emptyState}>
                        <MaterialCommunityIcons name="golf" size={64} color="#21262D" />
                        <Text style={styles.emptyText}>No rounds yet</Text>
                        <Text style={styles.emptySubtext}>Start your first round to track your progress</Text>
                    </View>
                ) : (
                    recentRounds.map(round => {
                        const scoreDiff = getScoreDiff(round.totalScore, round.par);
                        const roundDate = round.timestamp
                            ? new Date(round.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                            : 'Unknown Date';

                        // Calculate stats from holes if available
                        let totalPutts = '--';
                        let fairwaysHit = '--';
                        let girCount = '--';

                        if (round.holes) {
                            const holesWithPutts = round.holes.filter(h => h.putts !== undefined);
                            const holesWithFairway = round.holes.filter(h => h.fairwayHit !== undefined);
                            const holesWithGir = round.holes.filter(h => h.greenInReg !== undefined);

                            if (holesWithPutts.length > 0) {
                                totalPutts = holesWithPutts.reduce((sum, h) => sum + h.putts, 0);
                            }
                            if (holesWithFairway.length > 0) {
                                const fwHit = holesWithFairway.filter(h => h.fairwayHit).length;
                                fairwaysHit = `${fwHit}/${holesWithFairway.length}`;
                            }
                            if (holesWithGir.length > 0) {
                                const gir = holesWithGir.filter(h => h.greenInReg).length;
                                girCount = `${gir}/${holesWithGir.length}`;
                            }
                        }

                        return (
                            <TouchableOpacity key={round.id} style={styles.roundCard}>
                                <View style={styles.roundHeader}>
                                    <View style={styles.roundCourseInfo}>
                                        <FlagIcon />
                                        <View style={styles.roundCourseText}>
                                            <Text style={styles.roundCourseName}>{round.courseName || 'Unknown Course'}</Text>
                                            <Text style={styles.roundDate}>{roundDate}</Text>
                                        </View>
                                    </View>
                                    <View style={styles.roundScoreBox}>
                                        <Text style={styles.roundScore}>{round.totalScore || '--'}</Text>
                                        <Text style={[styles.roundScoreDiff, { color: scoreDiff.color }]}>
                                            {scoreDiff.text}
                                        </Text>
                                    </View>
                                </View>

                                <View style={styles.roundStats}>
                                    <View style={styles.roundStatItem}>
                                        <Text style={styles.roundStatValue}>{totalPutts}</Text>
                                        <Text style={styles.roundStatLabel}>Putts</Text>
                                    </View>
                                    <View style={styles.roundStatDivider} />
                                    <View style={styles.roundStatItem}>
                                        <Text style={styles.roundStatValue}>{fairwaysHit}</Text>
                                        <Text style={styles.roundStatLabel}>FW Hit</Text>
                                    </View>
                                    <View style={styles.roundStatDivider} />
                                    <View style={styles.roundStatItem}>
                                        <Text style={styles.roundStatValue}>{girCount}</Text>
                                        <Text style={styles.roundStatLabel}>GIR</Text>
                                    </View>
                                    <View style={styles.roundStatDivider} />
                                    <View style={styles.roundStatItem}>
                                        <Text style={styles.roundStatValue}>{round.holesPlayed || 18}</Text>
                                        <Text style={styles.roundStatLabel}>Holes</Text>
                                    </View>
                                </View>
                            </TouchableOpacity>
                        );
                    })
                )}

                <View style={{ height: 120 }} />
            </ScrollView>

            {/* Start New Round Button */}
            <View style={styles.actionBar}>
                <TouchableOpacity style={styles.startRoundButton} onPress={onStartRound}>
                    <Text style={styles.startRoundText}>START NEW ROUND</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A1612',
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyState: {
        alignItems: 'center',
        paddingVertical: 60,
    },
    emptyText: {
        color: '#8B949E',
        fontSize: 18,
        marginTop: 16,
        fontWeight: '600',
    },
    emptySubtext: {
        color: '#484F58',
        fontSize: 14,
        marginTop: 8,
        textAlign: 'center',
        paddingHorizontal: 40,
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
    tabBar: {
        flexDirection: 'row',
        marginHorizontal: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 12,
        padding: 4,
        marginBottom: 16,
    },
    tab: {
        flex: 1,
        paddingVertical: 10,
        alignItems: 'center',
        borderRadius: 10,
    },
    tabActive: {
        backgroundColor: '#2E7D32',
    },
    tabText: {
        color: '#888888',
        fontSize: 13,
        fontWeight: '600',
    },
    tabTextActive: {
        color: '#FFFFFF',
    },
    quickStats: {
        flexDirection: 'row',
        marginHorizontal: 20,
        backgroundColor: 'rgba(46, 125, 50, 0.15)',
        borderRadius: 16,
        padding: 16,
        marginBottom: 16,
    },
    quickStatItem: {
        flex: 1,
        alignItems: 'center',
    },
    quickStatValue: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
    },
    quickStatLabel: {
        color: '#888888',
        fontSize: 11,
        marginTop: 4,
    },
    roundsList: {
        flex: 1,
        paddingHorizontal: 20,
    },
    roundCard: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 16,
        padding: 16,
        marginBottom: 12,
    },
    roundHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
    },
    roundCourseInfo: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1,
    },
    roundCourseText: {
        marginLeft: 12,
        flex: 1,
    },
    roundCourseName: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    roundDate: {
        color: '#888888',
        fontSize: 12,
        marginTop: 2,
    },
    roundScoreBox: {
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 12,
    },
    roundScore: {
        color: '#FFFFFF',
        fontSize: 28,
        fontWeight: 'bold',
    },
    roundScoreDiff: {
        fontSize: 14,
        fontWeight: '600',
    },
    roundStats: {
        flexDirection: 'row',
        backgroundColor: 'rgba(0, 0, 0, 0.2)',
        borderRadius: 10,
        padding: 12,
    },
    roundStatItem: {
        flex: 1,
        alignItems: 'center',
    },
    roundStatValue: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    roundStatLabel: {
        color: '#666666',
        fontSize: 10,
        marginTop: 2,
    },
    roundStatDivider: {
        width: 1,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    actionBar: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        padding: 20,
        paddingBottom: 40,
        backgroundColor: 'rgba(10, 22, 18, 0.95)',
        borderTopWidth: 1,
        borderTopColor: 'rgba(255, 255, 255, 0.1)',
    },
    startRoundButton: {
        backgroundColor: '#2E7D32',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    startRoundText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
});
