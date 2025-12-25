import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function ShotSelector({ analysisData, onSelectShot, onCancel }) {
    const [selectedKey, setSelectedKey] = useState(null);

    if (!analysisData || !analysisData.trajectories) {
        return (
            <View style={styles.container}>
                <Text style={styles.errorText}>No trajectory data available</Text>
                <TouchableOpacity style={styles.cancelButton} onPress={onCancel}>
                    <Text style={styles.cancelButtonText}>Go Back</Text>
                </TouchableOpacity>
            </View>
        );
    }

    const handleSelectShot = (key) => {
        setSelectedKey(key);
        const trajectory = analysisData.trajectories[key];

        Alert.alert(
            'Navigate to Ball?',
            `${trajectory.name}\nEstimated distance: ${trajectory.carry_distance_yards.toFixed(1)} yards`,
            [
                { text: 'Cancel', style: 'cancel', onPress: () => setSelectedKey(null) },
                {
                    text: 'Yes, Find Ball',
                    onPress: () => onSelectShot(key, trajectory)
                }
            ]
        );
    };

    const trajectories = analysisData.trajectories;
    const launchData = analysisData;

    // Organized by ball flight pattern
    const shotGroups = [
        {
            title: 'Ball Curved Right',
            shots: [
                { key: 'high_slice', label: 'High Slice', icon: 'arrow-top-right' },
                { key: 'medium_slice', label: 'Medium Slice', icon: 'arrow-right-bold' },
                { key: 'low_fade', label: 'Low Fade', icon: 'tray-arrow-up' },
            ]
        },
        {
            title: 'Ball Went Straight',
            shots: [
                { key: 'straight', label: 'Straight', icon: 'arrow-up-bold' },
                { key: 'high_balloon', label: 'High & Short (Ballooned)', icon: 'arrow-up-circle' },
            ]
        },
        {
            title: 'Ball Curved Left',
            shots: [
                { key: 'low_draw', label: 'Low Draw', icon: 'tray-arrow-up' },
                { key: 'medium_hook', label: 'Medium Hook', icon: 'arrow-left-bold' },
                { key: 'high_hook', label: 'High Hook', icon: 'arrow-top-left' },
                { key: 'low_snap_hook', label: 'Low Snap Hook', icon: 'arrow-bottom-left' },
            ]
        },
    ];

    return (
        <View style={styles.container}>
            {/* Header with Instructions */}
            <View style={styles.header}>
                <Text style={styles.title}>Which Way Did Your Ball Go?</Text>
                <Text style={styles.instructions}>
                    Select the pattern that matches what you saw
                </Text>
            </View>

            {/* Launch Data Summary */}
            <View style={styles.launchBox}>
                <View style={styles.launchItem}>
                    <Text style={styles.launchLabel}>Speed</Text>
                    <Text style={styles.launchValue}>
                        {launchData.launch_speed_mph?.toFixed(1) || '0'} mph
                    </Text>
                    <Text style={styles.launchHint}>Estimated</Text>
                </View>
                <View style={styles.launchItem}>
                    <Text style={styles.launchLabel}>Launch Angle</Text>
                    <Text style={styles.launchValue}>
                        {launchData.launch_angle?.toFixed(0) || '0'}°
                    </Text>
                </View>
                <View style={styles.launchItem}>
                    <Text style={styles.launchLabel}>Direction</Text>
                    <Text style={styles.launchValue}>
                        {launchData.launch_direction?.toFixed(0) || '0'}°
                    </Text>
                </View>
            </View>

            {/* Shot Selection by Group */}
            <ScrollView style={styles.scrollView} contentContainerStyle={styles.shotList}>
                {shotGroups.map((group, groupIndex) => (
                    <View key={groupIndex} style={styles.shotGroup}>
                        <Text style={styles.groupTitle}>{group.title}</Text>

                        {group.shots.map(({ key, label, icon }) => {
                            const traj = trajectories[key];
                            if (!traj) return null;

                            const isSelected = selectedKey === key;
                            const distance = traj.carry_distance_yards;

                            return (
                                <TouchableOpacity
                                    key={key}
                                    style={[
                                        styles.shotCard,
                                        isSelected && styles.shotCardSelected,
                                    ]}
                                    onPress={() => handleSelectShot(key)}
                                    activeOpacity={0.7}
                                >
                                    <View style={styles.shotIconContainer}>
                                        <MaterialCommunityIcons
                                            name={icon}
                                            size={32}
                                            color={isSelected ? '#3FB950' : '#8B949E'}
                                            style={[
                                                group.title.includes('Left') && icon === 'tray-arrow-up' && { transform: [{ scaleX: -1 }] }
                                            ]}
                                        />
                                    </View>

                                    <View style={styles.shotInfo}>
                                        <Text style={styles.shotName}>{label}</Text>
                                        <Text style={styles.shotDistance}>
                                            ~{distance < 1
                                                ? `${(distance * 3 * 12).toFixed(0)} inches`
                                                : `${distance.toFixed(0)} yards`
                                            }
                                        </Text>
                                    </View>

                                    {isSelected && (
                                        <View style={styles.selectedBadge}>
                                            <MaterialCommunityIcons name="check" size={18} color="#FFFFFF" />
                                        </View>
                                    )}
                                </TouchableOpacity>
                            );
                        })}
                    </View>
                ))}

                {/* Help Text */}
                <View style={styles.helpBox}>
                    <Text style={styles.helpTitle}>Not Sure?</Text>
                    <Text style={styles.helpText}>
                        Think about which way the ball curved in the air:{'\n'}
                        • Right = Slice/Fade{'\n'}
                        • Straight = Straight{'\n'}
                        • Left = Draw/Hook{'\n'}
                        {'\n'}
                        Choose "Straight" if you're not sure.
                    </Text>
                </View>
            </ScrollView>

            {/* Footer */}
            <View style={styles.footer}>
                <TouchableOpacity style={styles.cancelButton} onPress={onCancel}>
                    <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
    header: {
        paddingTop: 60,
        paddingBottom: 20,
        paddingHorizontal: 20,
        backgroundColor: '#151515',
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A2A',
    },
    title: {
        color: '#FFFFFF',
        fontSize: 22,
        fontWeight: 'bold',
        marginBottom: 8,
        textAlign: 'center',
    },
    instructions: {
        color: '#00B4D8',
        fontSize: 14,
        textAlign: 'center',
    },
    launchBox: {
        flexDirection: 'row',
        backgroundColor: '#151515',
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A2A',
    },
    launchItem: {
        flex: 1,
        alignItems: 'center',
    },
    launchLabel: {
        color: '#808080',
        fontSize: 10,
        marginBottom: 4,
        textTransform: 'uppercase',
    },
    launchValue: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    launchHint: {
        color: '#666',
        fontSize: 9,
        marginTop: 2,
    },
    scrollView: {
        flex: 1,
    },
    shotList: {
        padding: 20,
    },
    shotGroup: {
        marginBottom: 28,
    },
    groupTitle: {
        color: '#00B4D8',
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 12,
        paddingBottom: 8,
        borderBottomWidth: 1,
        borderBottomColor: '#2A2A2A',
    },
    shotCard: {
        flexDirection: 'row',
        backgroundColor: '#1A1A1A',
        borderRadius: 10,
        padding: 16,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#2A2A2A',
        alignItems: 'center',
    },
    shotCardSelected: {
        backgroundColor: '#1F2A2A',
        borderColor: '#00B4D8',
        borderWidth: 2,
    },
    shotIconContainer: {
        width: 40,
        marginRight: 16,
        alignItems: 'center',
        justifyContent: 'center',
    },
    shotInfo: {
        flex: 1,
    },
    shotName: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    shotDistance: {
        color: '#808080',
        fontSize: 13,
    },
    selectedBadge: {
        width: 28,
        height: 28,
        borderRadius: 14,
        backgroundColor: '#00B4D8',
        justifyContent: 'center',
        alignItems: 'center',
    },
    selectedText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    helpBox: {
        backgroundColor: '#1A1A2E',
        padding: 16,
        borderRadius: 10,
        marginTop: 20,
        borderLeftWidth: 3,
        borderLeftColor: '#00B4D8',
    },
    helpTitle: {
        color: '#00B4D8',
        fontSize: 14,
        fontWeight: 'bold',
        marginBottom: 8,
    },
    helpText: {
        color: '#B0B0B0',
        fontSize: 12,
        lineHeight: 20,
    },
    footer: {
        padding: 20,
        backgroundColor: '#151515',
        borderTopWidth: 1,
        borderTopColor: '#2A2A2A',
    },
    cancelButton: {
        backgroundColor: '#2A2A2A',
        paddingVertical: 16,
        borderRadius: 10,
        alignItems: 'center',
    },
    cancelButtonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '600',
    },
    errorText: {
        color: '#FFFFFF',
        fontSize: 16,
        textAlign: 'center',
        marginTop: 100,
    },
});
