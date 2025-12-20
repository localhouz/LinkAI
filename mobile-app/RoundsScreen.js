import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView } from 'react-native';
import Svg, { Circle, Path, Rect, Line, G, Polygon } from 'react-native-svg';

export default function RoundsScreen({ onBack, onStartRound }) {
    const [activeTab, setActiveTab] = useState('recent');

    // Demo rounds data
    const recentRounds = [
        {
            id: 1,
            date: 'Dec 5, 2024',
            course: 'Sample Golf Course',
            score: 82,
            par: 72,
            holes: 18,
            putts: 31,
            fairways: '9/14',
            gir: '8/18',
        },
        {
            id: 2,
            date: 'Dec 1, 2024',
            course: 'Local Country Club',
            score: 85,
            par: 71,
            holes: 18,
            putts: 34,
            fairways: '7/14',
            gir: '6/18',
        },
        {
            id: 3,
            date: 'Nov 28, 2024',
            course: 'Mountain View Golf',
            score: 79,
            par: 72,
            holes: 18,
            putts: 29,
            fairways: '11/14',
            gir: '10/18',
        },
        {
            id: 4,
            date: 'Nov 24, 2024',
            course: 'Sample Golf Course',
            score: 88,
            par: 72,
            holes: 18,
            putts: 36,
            fairways: '6/14',
            gir: '5/18',
        },
    ];

    const getScoreDiff = (score, par) => {
        const diff = score - par;
        if (diff === 0) return { text: 'E', color: '#4CAF50' };
        if (diff > 0) return { text: `+${diff}`, color: '#f44336' };
        return { text: `${diff}`, color: '#2196F3' };
    };

    // Flag icon for course
    const FlagIcon = () => (
        <Svg width={24} height={24} viewBox="0 0 100 100">
            <Rect x="48" y="20" width="4" height="65" fill="#4CAF50" />
            <Polygon points="52,20 80,32 52,44" fill="#f44336" />
            <Circle cx="50" cy="88" r="8" fill="#4CAF50" opacity="0.5" />
        </Svg>
    );

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
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
                    <Text style={styles.quickStatValue}>{recentRounds.length}</Text>
                    <Text style={styles.quickStatLabel}>Total Rounds</Text>
                </View>
                <View style={styles.quickStatItem}>
                    <Text style={styles.quickStatValue}>82.3</Text>
                    <Text style={styles.quickStatLabel}>Avg Score</Text>
                </View>
                <View style={styles.quickStatItem}>
                    <Text style={styles.quickStatValue}>79</Text>
                    <Text style={styles.quickStatLabel}>Best Round</Text>
                </View>
            </View>

            {/* Rounds List */}
            <ScrollView style={styles.roundsList}>
                {recentRounds.map(round => {
                    const scoreDiff = getScoreDiff(round.score, round.par);
                    return (
                        <TouchableOpacity key={round.id} style={styles.roundCard}>
                            <View style={styles.roundHeader}>
                                <View style={styles.roundCourseInfo}>
                                    <FlagIcon />
                                    <View style={styles.roundCourseText}>
                                        <Text style={styles.roundCourseName}>{round.course}</Text>
                                        <Text style={styles.roundDate}>{round.date}</Text>
                                    </View>
                                </View>
                                <View style={styles.roundScoreBox}>
                                    <Text style={styles.roundScore}>{round.score}</Text>
                                    <Text style={[styles.roundScoreDiff, { color: scoreDiff.color }]}>
                                        {scoreDiff.text}
                                    </Text>
                                </View>
                            </View>

                            <View style={styles.roundStats}>
                                <View style={styles.roundStatItem}>
                                    <Text style={styles.roundStatValue}>{round.putts}</Text>
                                    <Text style={styles.roundStatLabel}>Putts</Text>
                                </View>
                                <View style={styles.roundStatDivider} />
                                <View style={styles.roundStatItem}>
                                    <Text style={styles.roundStatValue}>{round.fairways}</Text>
                                    <Text style={styles.roundStatLabel}>FW Hit</Text>
                                </View>
                                <View style={styles.roundStatDivider} />
                                <View style={styles.roundStatItem}>
                                    <Text style={styles.roundStatValue}>{round.gir}</Text>
                                    <Text style={styles.roundStatLabel}>GIR</Text>
                                </View>
                                <View style={styles.roundStatDivider} />
                                <View style={styles.roundStatItem}>
                                    <Text style={styles.roundStatValue}>{round.holes}</Text>
                                    <Text style={styles.roundStatLabel}>Holes</Text>
                                </View>
                            </View>
                        </TouchableOpacity>
                    );
                })}

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
