import AsyncStorage from '@react-native-async-storage/async-storage';

// Storage keys
const KEYS = {
    CLUBS: '@linksai_clubs',
    ROUNDS: '@linksai_rounds',
    SETTINGS: '@linksai_settings',
    PRACTICE_SESSIONS: '@linksai_practice',
};

// Default club set
const DEFAULT_CLUBS = [
    { id: '1', name: 'Driver', type: 'wood', typicalDistance: 250, shots: [] },
    { id: '2', name: '3 Wood', type: 'wood', typicalDistance: 220, shots: [] },
    { id: '3', name: '5 Wood', type: 'wood', typicalDistance: 200, shots: [] },
    { id: '4', name: '4 Hybrid', type: 'hybrid', typicalDistance: 190, shots: [] },
    { id: '5', name: '5 Iron', type: 'iron', typicalDistance: 175, shots: [] },
    { id: '6', name: '6 Iron', type: 'iron', typicalDistance: 165, shots: [] },
    { id: '7', name: '7 Iron', type: 'iron', typicalDistance: 155, shots: [] },
    { id: '8', name: '8 Iron', type: 'iron', typicalDistance: 145, shots: [] },
    { id: '9', name: '9 Iron', type: 'iron', typicalDistance: 135, shots: [] },
    { id: '10', name: 'PW', type: 'wedge', typicalDistance: 120, shots: [] },
    { id: '11', name: 'GW', type: 'wedge', typicalDistance: 105, shots: [] },
    { id: '12', name: 'SW', type: 'wedge', typicalDistance: 90, shots: [] },
    { id: '13', name: 'LW', type: 'wedge', typicalDistance: 70, shots: [] },
    { id: '14', name: 'Putter', type: 'putter', typicalDistance: 0, shots: [] },
];

// ===================
// CLUBS
// ===================

export const getClubs = async () => {
    try {
        const data = await AsyncStorage.getItem(KEYS.CLUBS);
        if (data) {
            return JSON.parse(data);
        }
        // First time - initialize with defaults
        await saveClubs(DEFAULT_CLUBS);
        return DEFAULT_CLUBS;
    } catch (error) {
        console.error('Error getting clubs:', error);
        return DEFAULT_CLUBS;
    }
};

export const saveClubs = async (clubs) => {
    try {
        await AsyncStorage.setItem(KEYS.CLUBS, JSON.stringify(clubs));
        return true;
    } catch (error) {
        console.error('Error saving clubs:', error);
        return false;
    }
};

export const addClub = async (club) => {
    const clubs = await getClubs();
    const newClub = {
        ...club,
        id: Date.now().toString(),
        shots: [],
    };
    clubs.push(newClub);
    await saveClubs(clubs);
    return newClub;
};

export const updateClub = async (clubId, updates) => {
    const clubs = await getClubs();
    const index = clubs.findIndex(c => c.id === clubId);
    if (index >= 0) {
        clubs[index] = { ...clubs[index], ...updates };
        await saveClubs(clubs);
        return clubs[index];
    }
    return null;
};

export const deleteClub = async (clubId) => {
    const clubs = await getClubs();
    const filtered = clubs.filter(c => c.id !== clubId);
    await saveClubs(filtered);
    return true;
};

export const recordShotForClub = async (clubId, distance) => {
    const clubs = await getClubs();
    const index = clubs.findIndex(c => c.id === clubId);
    if (index >= 0) {
        clubs[index].shots.push({
            distance,
            timestamp: Date.now(),
        });
        // Keep only last 50 shots for each club
        if (clubs[index].shots.length > 50) {
            clubs[index].shots = clubs[index].shots.slice(-50);
        }
        // Recalculate average
        const avgDistance = Math.round(
            clubs[index].shots.reduce((sum, s) => sum + s.distance, 0) / clubs[index].shots.length
        );
        clubs[index].calculatedDistance = avgDistance;
        await saveClubs(clubs);
        return clubs[index];
    }
    return null;
};

export const getClubRecommendation = async (targetDistance) => {
    const clubs = await getClubs();
    // Find closest club to target distance
    let closest = null;
    let minDiff = Infinity;

    for (const club of clubs) {
        if (club.type === 'putter') continue;
        const distance = club.calculatedDistance || club.typicalDistance;
        const diff = Math.abs(distance - targetDistance);
        if (diff < minDiff) {
            minDiff = diff;
            closest = club;
        }
    }
    return closest;
};

// ===================
// ROUNDS
// ===================

export const getRounds = async () => {
    try {
        const data = await AsyncStorage.getItem(KEYS.ROUNDS);
        return data ? JSON.parse(data) : [];
    } catch (error) {
        console.error('Error getting rounds:', error);
        return [];
    }
};

export const saveRound = async (round) => {
    try {
        const rounds = await getRounds();
        const newRound = {
            ...round,
            id: Date.now().toString(),
            timestamp: Date.now(),
        };
        rounds.unshift(newRound); // Add to beginning
        // Keep last 100 rounds
        if (rounds.length > 100) {
            rounds.pop();
        }
        await AsyncStorage.setItem(KEYS.ROUNDS, JSON.stringify(rounds));
        return newRound;
    } catch (error) {
        console.error('Error saving round:', error);
        return null;
    }
};

export const getRoundById = async (roundId) => {
    const rounds = await getRounds();
    return rounds.find(r => r.id === roundId);
};

export const deleteRound = async (roundId) => {
    const rounds = await getRounds();
    const filtered = rounds.filter(r => r.id !== roundId);
    await AsyncStorage.setItem(KEYS.ROUNDS, JSON.stringify(filtered));
    return true;
};

// ===================
// PRACTICE SESSIONS
// ===================

export const getPracticeSessions = async () => {
    try {
        const data = await AsyncStorage.getItem(KEYS.PRACTICE_SESSIONS);
        return data ? JSON.parse(data) : [];
    } catch (error) {
        console.error('Error getting practice sessions:', error);
        return [];
    }
};

export const savePracticeSession = async (session) => {
    try {
        const sessions = await getPracticeSessions();
        const newSession = {
            ...session,
            id: Date.now().toString(),
            timestamp: Date.now(),
        };
        sessions.unshift(newSession);
        // Keep last 50 sessions
        if (sessions.length > 50) {
            sessions.pop();
        }
        await AsyncStorage.setItem(KEYS.PRACTICE_SESSIONS, JSON.stringify(sessions));
        return newSession;
    } catch (error) {
        console.error('Error saving practice session:', error);
        return null;
    }
};

// ===================
// SETTINGS
// ===================

export const getSettings = async () => {
    try {
        const data = await AsyncStorage.getItem(KEYS.SETTINGS);
        return data ? JSON.parse(data) : {
            units: 'yards', // 'yards' | 'meters'
            hapticFeedback: true,
            soundEffects: true,
            notifications: true,
            autoRecordShots: true,
        };
    } catch (error) {
        console.error('Error getting settings:', error);
        return { units: 'yards', hapticFeedback: true, soundEffects: true };
    }
};

export const saveSettings = async (settings) => {
    try {
        await AsyncStorage.setItem(KEYS.SETTINGS, JSON.stringify(settings));
        return true;
    } catch (error) {
        console.error('Error saving settings:', error);
        return false;
    }
};

// ===================
// STATS AGGREGATION
// ===================

export const getStats = async () => {
    const rounds = await getRounds();

    if (rounds.length === 0) {
        return {
            roundsPlayed: 0,
            averageScore: null,
            bestScore: null,
            worstScore: null,
            handicap: null,
            fairwaysHit: null,
            greensInReg: null,
            avgPutts: null,
        };
    }

    const scores = rounds.map(r => r.totalScore).filter(Boolean);
    const avgScore = scores.length > 0
        ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
        : null;

    // Simple handicap estimate (score - 72) * 0.96 for recent rounds
    const recentScores = scores.slice(0, 10);
    const handicap = recentScores.length >= 3
        ? Math.round((recentScores.reduce((a, b) => a + b, 0) / recentScores.length - 72) * 0.96 * 10) / 10
        : null;

    // Aggregate fairways, GIR, putts
    let totalFairways = 0, totalFairwayHoles = 0;
    let totalGIR = 0, totalGIRHoles = 0;
    let totalPutts = 0, totalPuttHoles = 0;

    for (const round of rounds) {
        if (round.holes) {
            for (const hole of round.holes) {
                if (hole.fairwayHit !== undefined) {
                    totalFairways += hole.fairwayHit ? 1 : 0;
                    totalFairwayHoles++;
                }
                if (hole.greenInReg !== undefined) {
                    totalGIR += hole.greenInReg ? 1 : 0;
                    totalGIRHoles++;
                }
                if (hole.putts !== undefined) {
                    totalPutts += hole.putts;
                    totalPuttHoles++;
                }
            }
        }
    }

    return {
        roundsPlayed: rounds.length,
        averageScore: avgScore,
        bestScore: scores.length > 0 ? Math.min(...scores) : null,
        worstScore: scores.length > 0 ? Math.max(...scores) : null,
        handicap: handicap,
        fairwaysHit: totalFairwayHoles > 0
            ? Math.round((totalFairways / totalFairwayHoles) * 100)
            : null,
        greensInReg: totalGIRHoles > 0
            ? Math.round((totalGIR / totalGIRHoles) * 100)
            : null,
        avgPutts: totalPuttHoles > 0
            ? Math.round((totalPutts / totalPuttHoles) * 10) / 10
            : null,
    };
};

export default {
    getClubs,
    saveClubs,
    addClub,
    updateClub,
    deleteClub,
    recordShotForClub,
    getClubRecommendation,
    getRounds,
    saveRound,
    getRoundById,
    deleteRound,
    getPracticeSessions,
    savePracticeSession,
    getSettings,
    saveSettings,
    getStats,
};
