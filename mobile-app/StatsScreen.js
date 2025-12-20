import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView } from 'react-native';
import Svg, { Circle, Path, Rect, Line, G } from 'react-native-svg';

export default function StatsScreen({ onBack }) {
    const [selectedStat, setSelectedStat] = useState('overview');

    // Demo stats data
    const stats = {
        handicap: 12.4,
        roundsPlayed: 24,
        avgScore: 84,
        bestScore: 78,
        fairwaysHit: 58,
        greensInReg: 42,
        avgPutts: 31.2,
        upAndDown: 45,
    };

    const recentRounds = [
        { date: 'Dec 5', course: 'Sample GC', score: 82, par: 72 },
        { date: 'Dec 1', course: 'Local CC', score: 85, par: 71 },
        { date: 'Nov 28', course: 'Mountain View', score: 79, par: 72 },
        { date: 'Nov 24', course: 'Sample GC', score: 88, par: 72 },
        { date: 'Nov 20', course: 'Lakeside', score: 84, par: 70 },
    ];

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

    const scoreData = [
        { label: 'Dec', value: 82 },
        { label: 'Nov', value: 84 },
        { label: 'Oct', value: 86 },
        { label: 'Sep', value: 88 },
        { label: 'Aug', value: 85 },
    ];

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Statistics</Text>
                <View style={styles.placeholder} />
            </View>

            <ScrollView style={styles.scrollView}>
                {/* Handicap Card */}
                <View style={styles.handicapCard}>
                    <View style={styles.handicapCircle}>
                        <Svg width={140} height={140} viewBox="0 0 140 140">
                            <Circle cx="70" cy="70" r="60" fill="none" stroke="#1B5E20" strokeWidth="8" />
                            <Circle
                                cx="70" cy="70" r="60"
                                fill="none"
                                stroke="#4CAF50"
                                strokeWidth="8"
                                strokeLinecap="round"
                                strokeDasharray={`${(1 - stats.handicap / 36) * 377} 377`}
                                transform="rotate(-90 70 70)"
                            />
                        </Svg>
                        <View style={styles.handicapContent}>
                            <Text style={styles.handicapValue}>{stats.handicap}</Text>
                            <Text style={styles.handicapLabel}>HANDICAP</Text>
                        </View>
                    </View>
                    <View style={styles.handicapStats}>
                        <View style={styles.handicapStat}>
                            <Text style={styles.statValue}>{stats.roundsPlayed}</Text>
                            <Text style={styles.statLabel}>Rounds</Text>
                        </View>
                        <View style={styles.handicapStat}>
                            <Text style={styles.statValue}>{stats.avgScore}</Text>
                            <Text style={styles.statLabel}>Avg Score</Text>
                        </View>
                        <View style={styles.handicapStat}>
                            <Text style={styles.statValue}>{stats.bestScore}</Text>
                            <Text style={styles.statLabel}>Best</Text>
                        </View>
                    </View>
                </View>

                {/* Score Trend */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>SCORE TREND</Text>
                    <View style={styles.chartCard}>
                        <BarChart data={scoreData} maxValue={100} />
                    </View>
                </View>

                {/* Performance Stats */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>PERFORMANCE</Text>
                    <View style={styles.performanceGrid}>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.fairwaysHit}%</Text>
                            <Text style={styles.performanceLabel}>Fairways Hit</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: `${stats.fairwaysHit}%` }]} />
                            </View>
                        </View>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.greensInReg}%</Text>
                            <Text style={styles.performanceLabel}>Greens in Reg</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: `${stats.greensInReg}%` }]} />
                            </View>
                        </View>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.avgPutts}</Text>
                            <Text style={styles.performanceLabel}>Avg Putts</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: `${(36 - stats.avgPutts) / 36 * 100}%` }]} />
                            </View>
                        </View>
                        <View style={styles.performanceCard}>
                            <Text style={styles.performanceValue}>{stats.upAndDown}%</Text>
                            <Text style={styles.performanceLabel}>Up & Down</Text>
                            <View style={styles.progressBar}>
                                <View style={[styles.progressFill, { width: `${stats.upAndDown}%` }]} />
                            </View>
                        </View>
                    </View>
                </View>

                {/* Recent Rounds */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>RECENT ROUNDS</Text>
                    {recentRounds.map((round, index) => (
                        <View key={index} style={styles.roundItem}>
                            <View style={styles.roundInfo}>
                                <Text style={styles.roundDate}>{round.date}</Text>
                                <Text style={styles.roundCourse}>{round.course}</Text>
                            </View>
                            <View style={styles.roundScore}>
                                <Text style={styles.roundScoreValue}>{round.score}</Text>
                                <Text style={[
                                    styles.roundScoreDiff,
                                    { color: round.score <= round.par ? '#4CAF50' : '#f44336' }
                                ]}>
                                    {round.score <= round.par ? `${round.score - round.par}` : `+${round.score - round.par}`}
                                </Text>
                            </View>
                        </View>
                    ))}
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
    handicapCircle: {
        width: 140,
        height: 140,
        justifyContent: 'center',
        alignItems: 'center',
    },
    handicapContent: {
        position: 'absolute',
        alignItems: 'center',
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
