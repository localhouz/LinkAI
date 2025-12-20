import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, TextInput, Alert } from 'react-native';
import Svg, { Circle, Path, Rect, Line, G } from 'react-native-svg';

export default function ScorecardScreen({ onBack, courseName: propCourseName }) {
    const [currentHole, setCurrentHole] = useState(1);
    const [scores, setScores] = useState({});
    const courseName = propCourseName || 'Sample Golf Course';

    // Demo course data
    const courseData = [
        { hole: 1, par: 4, yards: 385, handicap: 7 },
        { hole: 2, par: 3, yards: 165, handicap: 15 },
        { hole: 3, par: 5, yards: 520, handicap: 3 },
        { hole: 4, par: 4, yards: 410, handicap: 1 },
        { hole: 5, par: 4, yards: 375, handicap: 11 },
        { hole: 6, par: 3, yards: 195, handicap: 17 },
        { hole: 7, par: 5, yards: 545, handicap: 5 },
        { hole: 8, par: 4, yards: 340, handicap: 13 },
        { hole: 9, par: 4, yards: 420, handicap: 9 },
        { hole: 10, par: 4, yards: 390, handicap: 8 },
        { hole: 11, par: 5, yards: 510, handicap: 4 },
        { hole: 12, par: 3, yards: 175, handicap: 16 },
        { hole: 13, par: 4, yards: 400, handicap: 2 },
        { hole: 14, par: 4, yards: 365, handicap: 12 },
        { hole: 15, par: 5, yards: 535, handicap: 6 },
        { hole: 16, par: 3, yards: 185, handicap: 18 },
        { hole: 17, par: 4, yards: 430, handicap: 10 },
        { hole: 18, par: 4, yards: 395, handicap: 14 },
    ];

    const currentHoleData = courseData[currentHole - 1];

    const updateScore = (delta) => {
        const current = scores[currentHole] || currentHoleData.par;
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

    const getTotalScore = () => {
        let total = 0;
        Object.entries(scores).forEach(([hole, score]) => {
            total += score;
        });
        return total;
    };

    const getTotalPar = () => {
        let par = 0;
        Object.keys(scores).forEach(hole => {
            par += courseData[parseInt(hole) - 1].par;
        });
        return par;
    };

    const getScoreVsPar = () => {
        const total = getTotalScore();
        const par = getTotalPar();
        const diff = total - par;
        if (diff === 0) return 'E';
        return diff > 0 ? `+${diff}` : `${diff}`;
    };

    const currentScore = scores[currentHole] || currentHoleData.par;
    const scoreInfo = getScoreLabel(currentScore, currentHoleData.par);

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <View style={styles.headerCenter}>
                    <Text style={styles.headerTitle}>Scorecard</Text>
                    <Text style={styles.courseName}>{courseName}</Text>
                </View>
                <View style={styles.placeholder} />
            </View>

            {/* Current Hole Display */}
            <View style={styles.currentHoleSection}>
                <View style={styles.holeNavigation}>
                    <TouchableOpacity
                        style={styles.holeNavButton}
                        onPress={() => setCurrentHole(Math.max(1, currentHole - 1))}
                    >
                        <Text style={styles.holeNavText}>◀</Text>
                    </TouchableOpacity>

                    <View style={styles.holeInfo}>
                        <Text style={styles.holeNumber}>HOLE {currentHole}</Text>
                        <View style={styles.holeDetails}>
                            <View style={styles.holeDetail}>
                                <Text style={styles.detailValue}>{currentHoleData.par}</Text>
                                <Text style={styles.detailLabel}>PAR</Text>
                            </View>
                            <View style={styles.holeDetail}>
                                <Text style={styles.detailValue}>{currentHoleData.yards}</Text>
                                <Text style={styles.detailLabel}>YARDS</Text>
                            </View>
                            <View style={styles.holeDetail}>
                                <Text style={styles.detailValue}>{currentHoleData.handicap}</Text>
                                <Text style={styles.detailLabel}>HCP</Text>
                            </View>
                        </View>
                    </View>

                    <TouchableOpacity
                        style={styles.holeNavButton}
                        onPress={() => setCurrentHole(Math.min(18, currentHole + 1))}
                    >
                        <Text style={styles.holeNavText}>▶</Text>
                    </TouchableOpacity>
                </View>

                {/* Score Entry */}
                <View style={styles.scoreEntry}>
                    <TouchableOpacity
                        style={styles.scoreButton}
                        onPress={() => updateScore(-1)}
                    >
                        <Text style={styles.scoreButtonText}>−</Text>
                    </TouchableOpacity>

                    <View style={styles.scoreDisplay}>
                        <Text style={styles.scoreValue}>{currentScore}</Text>
                        <Text style={[styles.scoreLabel, { color: scoreInfo.color }]}>
                            {scoreInfo.label}
                        </Text>
                    </View>

                    <TouchableOpacity
                        style={styles.scoreButton}
                        onPress={() => updateScore(1)}
                    >
                        <Text style={styles.scoreButtonText}>+</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Total Score */}
            <View style={styles.totalSection}>
                <View style={styles.totalItem}>
                    <Text style={styles.totalLabel}>THRU</Text>
                    <Text style={styles.totalValue}>{Object.keys(scores).length}</Text>
                </View>
                <View style={styles.totalDivider} />
                <View style={styles.totalItem}>
                    <Text style={styles.totalLabel}>TOTAL</Text>
                    <Text style={styles.totalValue}>{getTotalScore() || '—'}</Text>
                </View>
                <View style={styles.totalDivider} />
                <View style={styles.totalItem}>
                    <Text style={styles.totalLabel}>VS PAR</Text>
                    <Text style={[styles.totalValue, styles.vsPar]}>
                        {Object.keys(scores).length > 0 ? getScoreVsPar() : '—'}
                    </Text>
                </View>
            </View>

            {/* Scorecard Grid */}
            <ScrollView style={styles.scoreGrid}>
                {/* Front Nine */}
                <View style={styles.nineSection}>
                    <Text style={styles.nineTitle}>FRONT NINE</Text>
                    <View style={styles.holesRow}>
                        {courseData.slice(0, 9).map(hole => (
                            <TouchableOpacity
                                key={hole.hole}
                                style={[
                                    styles.holeCell,
                                    currentHole === hole.hole && styles.holeCellActive
                                ]}
                                onPress={() => setCurrentHole(hole.hole)}
                            >
                                <Text style={styles.holeCellNumber}>{hole.hole}</Text>
                                <Text style={styles.holeCellPar}>P{hole.par}</Text>
                                <View style={[
                                    styles.holeCellScore,
                                    scores[hole.hole] && {
                                        backgroundColor: getScoreLabel(scores[hole.hole], hole.par).color
                                    }
                                ]}>
                                    <Text style={styles.holeCellScoreText}>
                                        {scores[hole.hole] || '—'}
                                    </Text>
                                </View>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                {/* Back Nine */}
                <View style={styles.nineSection}>
                    <Text style={styles.nineTitle}>BACK NINE</Text>
                    <View style={styles.holesRow}>
                        {courseData.slice(9, 18).map(hole => (
                            <TouchableOpacity
                                key={hole.hole}
                                style={[
                                    styles.holeCell,
                                    currentHole === hole.hole && styles.holeCellActive
                                ]}
                                onPress={() => setCurrentHole(hole.hole)}
                            >
                                <Text style={styles.holeCellNumber}>{hole.hole}</Text>
                                <Text style={styles.holeCellPar}>P{hole.par}</Text>
                                <View style={[
                                    styles.holeCellScore,
                                    scores[hole.hole] && {
                                        backgroundColor: getScoreLabel(scores[hole.hole], hole.par).color
                                    }
                                ]}>
                                    <Text style={styles.holeCellScoreText}>
                                        {scores[hole.hole] || '—'}
                                    </Text>
                                </View>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>
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
    headerCenter: {
        alignItems: 'center',
    },
    headerTitle: {
        color: '#FFFFFF',
        fontSize: 20,
        fontWeight: 'bold',
    },
    courseName: {
        color: '#888888',
        fontSize: 12,
        marginTop: 2,
    },
    placeholder: {
        width: 60,
    },
    currentHoleSection: {
        padding: 20,
        backgroundColor: 'rgba(46, 125, 50, 0.2)',
        marginHorizontal: 20,
        borderRadius: 20,
        marginBottom: 20,
    },
    holeNavigation: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    holeNavButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    holeNavText: {
        color: '#FFFFFF',
        fontSize: 18,
    },
    holeInfo: {
        alignItems: 'center',
    },
    holeNumber: {
        color: '#4CAF50',
        fontSize: 14,
        fontWeight: 'bold',
        letterSpacing: 2,
    },
    holeDetails: {
        flexDirection: 'row',
        marginTop: 8,
        gap: 24,
    },
    holeDetail: {
        alignItems: 'center',
    },
    detailValue: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
    detailLabel: {
        color: '#888888',
        fontSize: 10,
        marginTop: 2,
    },
    scoreEntry: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: 20,
        gap: 24,
    },
    scoreButton: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: '#2E7D32',
        justifyContent: 'center',
        alignItems: 'center',
    },
    scoreButtonText: {
        color: '#FFFFFF',
        fontSize: 32,
        fontWeight: '300',
    },
    scoreDisplay: {
        alignItems: 'center',
        width: 100,
    },
    scoreValue: {
        color: '#FFFFFF',
        fontSize: 64,
        fontWeight: 'bold',
    },
    scoreLabel: {
        fontSize: 14,
        fontWeight: 'bold',
    },
    totalSection: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 16,
        marginHorizontal: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 12,
        marginBottom: 20,
    },
    totalItem: {
        alignItems: 'center',
        paddingHorizontal: 24,
    },
    totalLabel: {
        color: '#888888',
        fontSize: 10,
        letterSpacing: 1,
    },
    totalValue: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
        marginTop: 4,
    },
    vsPar: {
        color: '#4CAF50',
    },
    totalDivider: {
        width: 1,
        height: 40,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    scoreGrid: {
        flex: 1,
        paddingHorizontal: 20,
    },
    nineSection: {
        marginBottom: 20,
    },
    nineTitle: {
        color: '#4CAF50',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 1,
        marginBottom: 10,
    },
    holesRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    holeCell: {
        width: '10%',
        aspectRatio: 0.8,
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 8,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 4,
    },
    holeCellActive: {
        backgroundColor: 'rgba(46, 125, 50, 0.4)',
        borderWidth: 1,
        borderColor: '#4CAF50',
    },
    holeCellNumber: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
    },
    holeCellPar: {
        color: '#888888',
        fontSize: 9,
    },
    holeCellScore: {
        marginTop: 4,
        width: 24,
        height: 24,
        borderRadius: 12,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    holeCellScoreText: {
        color: '#FFFFFF',
        fontSize: 12,
        fontWeight: 'bold',
    },
});
