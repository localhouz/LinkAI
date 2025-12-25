import React, { useState, useEffect } from 'react';
import {
    StyleSheet, Text, View, TouchableOpacity, ScrollView,
    TextInput, Modal, Alert, ActivityIndicator
} from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { getClubs, addClub, updateClub, deleteClub } from './services/storage';

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

const CLUB_TYPES = [
    { key: 'wood', label: 'Wood', icon: 'golf' },
    { key: 'hybrid', label: 'Hybrid', icon: 'golf' },
    { key: 'iron', label: 'Iron', icon: 'golf' },
    { key: 'wedge', label: 'Wedge', icon: 'golf' },
    { key: 'putter', label: 'Putter', icon: 'golf-tee' },
];

export default function ClubBagScreen({ onBack }) {
    const [clubs, setClubs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [modalVisible, setModalVisible] = useState(false);
    const [editingClub, setEditingClub] = useState(null);

    // Form state
    const [clubName, setClubName] = useState('');
    const [clubType, setClubType] = useState('iron');
    const [clubDistance, setClubDistance] = useState('');

    useEffect(() => {
        loadClubs();
    }, []);

    const loadClubs = async () => {
        setLoading(true);
        const loadedClubs = await getClubs();
        setClubs(loadedClubs);
        setLoading(false);
    };

    const handleAddClub = () => {
        setEditingClub(null);
        setClubName('');
        setClubType('iron');
        setClubDistance('');
        setModalVisible(true);
    };

    const handleEditClub = (club) => {
        setEditingClub(club);
        setClubName(club.name);
        setClubType(club.type);
        setClubDistance(club.typicalDistance.toString());
        setModalVisible(true);
    };

    const handleDeleteClub = (club) => {
        Alert.alert(
            'Delete Club',
            `Are you sure you want to remove ${club.name} from your bag?`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        await deleteClub(club.id);
                        triggerHaptic('success');
                        loadClubs();
                    }
                },
            ]
        );
    };

    const handleSaveClub = async () => {
        if (!clubName.trim()) {
            Alert.alert('Error', 'Please enter a club name');
            return;
        }

        const distance = parseInt(clubDistance) || 0;

        if (editingClub) {
            await updateClub(editingClub.id, {
                name: clubName.trim(),
                type: clubType,
                typicalDistance: distance,
            });
        } else {
            await addClub({
                name: clubName.trim(),
                type: clubType,
                typicalDistance: distance,
            });
        }

        triggerHaptic('success');
        setModalVisible(false);
        loadClubs();
    };

    const getAverageDistance = (club) => {
        if (club.calculatedDistance) {
            return club.calculatedDistance;
        }
        return club.typicalDistance;
    };

    const getShotCount = (club) => {
        return club.shots ? club.shots.length : 0;
    };

    const groupedClubs = () => {
        const groups = {
            wood: [],
            hybrid: [],
            iron: [],
            wedge: [],
            putter: [],
        };
        clubs.forEach(club => {
            if (groups[club.type]) {
                groups[club.type].push(club);
            }
        });
        return groups;
    };

    const renderClubCard = (club) => (
        <TouchableOpacity
            key={club.id}
            style={styles.clubCard}
            onPress={() => handleEditClub(club)}
            onLongPress={() => handleDeleteClub(club)}
        >
            <View style={styles.clubIconContainer}>
                <MaterialCommunityIcons
                    name={club.type === 'putter' ? 'golf-tee' : 'golf'}
                    size={24}
                    color="#3FB950"
                />
            </View>
            <View style={styles.clubInfo}>
                <Text style={styles.clubName}>{club.name}</Text>
                <Text style={styles.clubStats}>
                    {getShotCount(club) > 0
                        ? `${getShotCount(club)} shots tracked`
                        : 'No shots tracked yet'
                    }
                </Text>
            </View>
            <View style={styles.clubDistance}>
                <Text style={styles.distanceValue}>{getAverageDistance(club)}</Text>
                <Text style={styles.distanceUnit}>yds</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#8B949E" />
        </TouchableOpacity>
    );

    const renderSection = (title, clubList) => {
        if (clubList.length === 0) return null;
        return (
            <View style={styles.section} key={title}>
                <Text style={styles.sectionTitle}>{title}</Text>
                {clubList.map(renderClubCard)}
            </View>
        );
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#3FB950" />
            </View>
        );
    }

    const grouped = groupedClubs();

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>My Clubs</Text>
                <TouchableOpacity onPress={handleAddClub} style={styles.addButton}>
                    <Ionicons name="add" size={28} color="#3FB950" />
                </TouchableOpacity>
            </View>

            {/* Info Banner */}
            <View style={styles.infoBanner}>
                <MaterialCommunityIcons name="information-outline" size={20} color="#58A6FF" />
                <Text style={styles.infoText}>
                    Tap to edit • Long press to delete • Distances auto-calibrate from tracked shots
                </Text>
            </View>

            {/* Club List */}
            <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
                {renderSection('Woods', grouped.wood)}
                {renderSection('Hybrids', grouped.hybrid)}
                {renderSection('Irons', grouped.iron)}
                {renderSection('Wedges', grouped.wedge)}
                {renderSection('Putter', grouped.putter)}

                <View style={{ height: 100 }} />
            </ScrollView>

            {/* Add/Edit Modal */}
            <Modal
                visible={modalVisible}
                animationType="slide"
                transparent={true}
                onRequestClose={() => setModalVisible(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>
                                {editingClub ? 'Edit Club' : 'Add Club'}
                            </Text>
                            <TouchableOpacity onPress={() => setModalVisible(false)}>
                                <Ionicons name="close" size={24} color="#8B949E" />
                            </TouchableOpacity>
                        </View>

                        {/* Club Name */}
                        <Text style={styles.inputLabel}>Club Name</Text>
                        <TextInput
                            style={styles.input}
                            value={clubName}
                            onChangeText={setClubName}
                            placeholder="e.g. 7 Iron"
                            placeholderTextColor="#8B949E"
                        />

                        {/* Club Type */}
                        <Text style={styles.inputLabel}>Club Type</Text>
                        <View style={styles.typeSelector}>
                            {CLUB_TYPES.map(type => (
                                <TouchableOpacity
                                    key={type.key}
                                    style={[
                                        styles.typeButton,
                                        clubType === type.key && styles.typeButtonActive
                                    ]}
                                    onPress={() => setClubType(type.key)}
                                >
                                    <Text style={[
                                        styles.typeButtonText,
                                        clubType === type.key && styles.typeButtonTextActive
                                    ]}>
                                        {type.label}
                                    </Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        {/* Typical Distance */}
                        <Text style={styles.inputLabel}>Typical Distance (yards)</Text>
                        <TextInput
                            style={styles.input}
                            value={clubDistance}
                            onChangeText={setClubDistance}
                            placeholder="150"
                            placeholderTextColor="#8B949E"
                            keyboardType="numeric"
                        />

                        {/* Save Button */}
                        <TouchableOpacity
                            style={styles.saveButton}
                            onPress={handleSaveClub}
                        >
                            <Text style={styles.saveButtonText}>
                                {editingClub ? 'Save Changes' : 'Add to Bag'}
                            </Text>
                        </TouchableOpacity>
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
    loadingContainer: {
        flex: 1,
        backgroundColor: '#0D1117',
        justifyContent: 'center',
        alignItems: 'center',
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
    headerTitle: {
        fontSize: 20,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    addButton: {
        padding: 8,
    },
    infoBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(88, 166, 255, 0.1)',
        paddingVertical: 12,
        paddingHorizontal: 16,
        marginHorizontal: 16,
        marginTop: 16,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: 'rgba(88, 166, 255, 0.3)',
    },
    infoText: {
        flex: 1,
        marginLeft: 10,
        fontSize: 12,
        color: '#58A6FF',
        lineHeight: 18,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: 16,
    },
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: '#8B949E',
        marginBottom: 12,
        letterSpacing: 1,
        textTransform: 'uppercase',
    },
    clubCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#161B22',
        borderRadius: 12,
        padding: 16,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#21262D',
    },
    clubIconContainer: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 14,
    },
    clubInfo: {
        flex: 1,
    },
    clubName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#F0F6FC',
        marginBottom: 4,
    },
    clubStats: {
        fontSize: 13,
        color: '#8B949E',
    },
    clubDistance: {
        alignItems: 'flex-end',
        marginRight: 10,
    },
    distanceValue: {
        fontSize: 20,
        fontWeight: '700',
        color: '#3FB950',
    },
    distanceUnit: {
        fontSize: 11,
        color: '#8B949E',
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
        padding: 24,
        paddingBottom: 40,
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 24,
    },
    modalTitle: {
        fontSize: 22,
        fontWeight: '700',
        color: '#F0F6FC',
    },
    inputLabel: {
        fontSize: 14,
        fontWeight: '600',
        color: '#8B949E',
        marginBottom: 8,
        marginTop: 16,
    },
    input: {
        backgroundColor: '#0D1117',
        borderRadius: 10,
        padding: 16,
        fontSize: 16,
        color: '#F0F6FC',
        borderWidth: 1,
        borderColor: '#21262D',
    },
    typeSelector: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    typeButton: {
        paddingVertical: 8,
        paddingHorizontal: 16,
        borderRadius: 20,
        backgroundColor: '#0D1117',
        borderWidth: 1,
        borderColor: '#21262D',
    },
    typeButtonActive: {
        backgroundColor: 'rgba(63, 185, 80, 0.15)',
        borderColor: '#3FB950',
    },
    typeButtonText: {
        fontSize: 14,
        color: '#8B949E',
    },
    typeButtonTextActive: {
        color: '#3FB950',
        fontWeight: '600',
    },
    saveButton: {
        backgroundColor: '#238636',
        borderRadius: 10,
        paddingVertical: 16,
        alignItems: 'center',
        marginTop: 32,
    },
    saveButtonText: {
        fontSize: 16,
        fontWeight: '700',
        color: '#FFFFFF',
    },
});
