import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { getStats, getRounds } from './services/storage';

export default function StatsScreen({ onBack }) {
    const [selectedStat, setSelectedStat] = useState('overview');
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        handicap: null,
        roundsPlayed: 0,
        averageScore: null,
        bestScore: null,
        worstScore: null,
        fairwaysHit: null,
        greensInReg: null,
        avgPutts: null,
    });
    const [recentRounds, setRecentRounds] = useState([]);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        setLoading(true);
        try {
            const loadedStats = await getStats();
            const loadedRounds = await getRounds();
            setStats(loadedStats);
            setRecentRounds(loadedRounds.slice(0, 5));
        } catch (error) {
            console.error('Error loading stats:', error);
        }
        setLoading(false);
    };

    // Simple bar chart component
    const BarChart = ({ data, maxValue }) => (
        <View style={styles.barChart}>
            {data.map((item, index) => (
                <View key={index} style={styles.barItem}>
                    <View style={styles.barContainer}>
                        <View
                            style={[
                                styles.bar,
                                { height: `${(item.value / maxValue) * 100}%` }
                            ]}
                        />
                    </View>
                    <Text style={styles.barLabel}>{item.label}</Text>
                </View>
            ))}
        </View>
    );

    // Generate score trend from recent rounds
    const scoreData = recentRounds.slice(0, 5).reverse().map((round, index) => ({
        label: new Date(round.timestamp).toLocaleDateString('en-US', { month: 'short' }),
        value: round.totalScore || 0,
    }));

    if (loading) {
        return (
            <View style={styles.container}>
                <View style={styles.header}>
                    <TouchableOpacity onPress={onBack} style={styles.backButton}>
                        <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                    </TouchableOpacity>
                    <Text style={styles.headerTitle}>Statistics</Text>
                    <View style={styles.placeholder} />
                </View>
                <View style={styles.loadingContainer}>
                    <ActivityIndicator size="large" color="#3FB950" />
                </View>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Statistics</Text>
                <View style={styles.placeholder} />
            </View>

            <ScrollView style={styles.scrollView}>
                {/* Handicap Card */}
                <View style={styles.handicapCard}>
                    <View style={styles.handicapIconContainer}>
                        <MaterialCommunityIcons name="trophy-variant" size={80} color="#FFD700" />
                        <View style={styles.handicapOverlayText}>
                            <Text style={styles.handicapValue}>{stats.handicap ?? '--'}</Text>
                            <Text style={styles.handicapLabel}>HANDICAP</Text>
                        </View>
                    </View>
                    <View style={styles.handicapStats}>
                        <View style={styles.handicapStat}>
                            <Text style={styles.statValue}>{stats.roundsPlayed}</Text>
                            <Text style={styles.statLabel}>Rounds</Text>
                        </View>
                        <View style={styles.handicapStat}>
                            <Text style={styles.statValue}>{stats.averageScore ?? '--'}</Text>
                            <Text style={styles.statLabel}>Avg Score</Text>
                        </View>
                        <View style={styles.handicapStat}>
                            <Text style={styles.statValue}>{stats.bestScore ?? '--'}</Text>
                            <Text style={styles.statLabel}>Best</Text>
                        </View>
                    </View>
                </View>

                {/* Score Trend */}
                {scoreData.length > 0 && (
                    <View style={styles.section}>
                        <Text style={styles.sectionTitle}>SCORE TREND</Text>
                        <View style={styles.chartCard}>
                            <BarChart data={scoreData} maxValue={100} />
                        </View>
                    </View>
                )}

                {/* Performance Stats */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>PERFORMANCE</Text>
                    <View style={styles.performanceGrid}>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.fairwaysHit ?? '--'}%</Text>
                            <Text style={styles.performanceLabel}>Fairways Hit</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: `${stats.fairwaysHit ?? 0}%` }]} />
                            </View>
                        </View>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.greensInReg ?? '--'}%</Text>
                            <Text style={styles.performanceLabel}>Greens in Reg</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: `${stats.greensInReg ?? 0}%` }]} />
                            </View>
                        </View>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.avgPutts ?? '--'}</Text>
                            <Text style={styles.performanceLabel}>Avg Putts</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: stats.avgPutts ? `${Math.max(0, (36 - stats.avgPutts) / 36 * 100)}%` : '0%' }]} />
                            </View>
                        </View>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.worstScore ?? '--'}</Text>
                            <Text style={styles.performanceLabel}>Worst Score</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: '0%' }]} />
                            </View>
                        </View>
                    </View>
                </View>

                {/* Recent Rounds */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>RECENT ROUNDS</Text>
                    {recentRounds.length === 0 ? (
                        <View style={styles.emptyState}>
                            <MaterialCommunityIcons name="golf" size={48} color="#21262D" />
                            <Text style={styles.emptyText}>No rounds played yet</Text>
                            <Text style={styles.emptySubtext}>Complete a round to see your stats here</Text>
                        </View>
                    ) : (
                        recentRounds.map((round, index) => (
                            <View key={index} style={styles.roundItem}>
                                <View style={styles.roundInfo}>
                                    <Text style={styles.roundDate}>
                                        {new Date(round.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                    </Text>
                                    <Text style={styles.roundCourse}>{round.courseName || 'Unknown Course'}</Text>
                                </View>
                                <View style={styles.roundScore}>
                                    <Text style={styles.roundScoreValue}>{round.totalScore || '--'}</Text>
                                    {round.totalScore && round.par && (
                                        <Text style={[
                                            styles.roundScoreDiff,
                                            { color: round.totalScore <= round.par ? '#4CAF50' : '#f44336' }
                                        ]}>
                                            {round.totalScore <= round.par ? `${round.totalScore - round.par}` : `+${round.totalScore - round.par}`}
                                        </Text>
                                    )}
                                </View>
                            </View>
                        ))
                    )}
                </View>

                <View style={{ height: 100 }} />
            </ScrollView>
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
    },
    emptyState: {
        alignItems: 'center',
        paddingVertical: 40,
        backgroundColor: 'rgba(33, 38, 45, 0.5)',
        borderRadius: 12,
    },
    emptyText: {
        color: '#8B949E',
        fontSize: 16,
        marginTop: 12,
    },
    emptySubtext: {
        color: '#484F58',
        fontSize: 13,
        marginTop: 4,
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
    scrollView: {
        flex: 1,
    },
    handicapCard: {
        margin: 20,
        padding: 24,
        backgroundColor: 'rgba(46, 125, 50, 0.15)',
        borderRadius: 20,
        alignItems: 'center',
    },
    handicapIconContainer: {
        width: 140,
        height: 140,
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
    },
    handicapOverlayText: {
        position: 'absolute',
        alignItems: 'center',
        top: '55%',
    },
    handicapValue: {
        color: '#FFFFFF',
        fontSize: 36,
        fontWeight: 'bold',
    },
    handicapLabel: {
        color: '#4CAF50',
        fontSize: 10,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
    handicapStats: {
        flexDirection: 'row',
        marginTop: 24,
        gap: 32,
    },
    handicapStat: {
        alignItems: 'center',
    },
    statValue: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
    },
    statLabel: {
        color: '#888888',
        fontSize: 12,
        marginTop: 4,
    },
    section: {
        paddingHorizontal: 20,
        marginBottom: 24,
    },
    sectionTitle: {
        color: '#4CAF50',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 1,
        marginBottom: 12,
    },
    chartCard: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 16,
        padding: 20,
    },
    barChart: {
        flexDirection: 'row',
        height: 120,
        alignItems: 'flex-end',
        justifyContent: 'space-around',
    },
    barItem: {
        alignItems: 'center',
        flex: 1,
    },
    barContainer: {
        height: 100,
        width: 30,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 4,
        justifyContent: 'flex-end',
        overflow: 'hidden',
    },
    bar: {
        width: '100%',
        backgroundColor: '#4CAF50',
        borderRadius: 4,
    },
    barLabel: {
        color: '#888888',
        fontSize: 11,
        marginTop: 8,
    },
    performanceGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 12,
    },
    performanceCard: {
        width: '48%',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 12,
        padding: 16,
    },
    performanceValue: {
        color: '#FFFFFF',
        fontSize: 28,
        fontWeight: 'bold',
    },
    performanceLabel: {
        color: '#888888',
        fontSize: 12,
        marginTop: 4,
        marginBottom: 12,
    },
    progressBar: {
        height: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 2,
        overflow: 'hidden',
    },
    progressFill: {
        height: '100%',
        backgroundColor: '#4CAF50',
        borderRadius: 2,
    },
    roundItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        padding: 16,
        borderRadius: 12,
        marginBottom: 10,
    },
    roundInfo: {
        flex: 1,
    },
    roundDate: {
        color: '#888888',
        fontSize: 12,
    },
    roundCourse: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
        marginTop: 2,
    },
    roundScore: {
        alignItems: 'flex-end',
    },
    roundScoreValue: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
    },
    roundScoreDiff: {
        fontSize: 14,
        fontWeight: '600',
    },
});
