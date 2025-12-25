import React, { useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Image, Switch } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

export default function ProfileScreen({ onBack }) {
    const [notifications, setNotifications] = useState(true);
    const [autoRecord, setAutoRecord] = useState(true);
    const [metricUnits, setMetricUnits] = useState(false);

    // Demo user data
    const user = {
        name: 'John Golfer',
        email: 'john@example.com',
        memberSince: 'January 2024',
        handicap: 12.4,
        totalRounds: 47,
        shotsTracked: 2840,
    };

    // Profile avatar placeholder
    const Avatar = () => (
        <View style={styles.avatar}>
            <Ionicons name="person" size={40} color="#4CAF50" />
        </View>
    );

    const MenuItem = ({ icon, label, value, onPress, isSwitch, switchValue, onSwitchChange }) => (
        <TouchableOpacity
            style={styles.menuItem}
            onPress={onPress}
            disabled={isSwitch}
        >
            <View style={styles.menuIconContainer}>
                <MaterialCommunityIcons name={icon} size={22} color="#4CAF50" />
            </View>
            <Text style={styles.menuLabel}>{label}</Text>
            {isSwitch ? (
                <Switch
                    value={switchValue}
                    onValueChange={onSwitchChange}
                    trackColor={{ false: '#333', true: '#2E7D32' }}
                    thumbColor={switchValue ? '#4CAF50' : '#666'}
                />
            ) : (
                <View style={styles.menuRight}>
                    {value && <Text style={styles.menuValue}>{value}</Text>}
                    <Ionicons name="chevron-forward" size={18} color="#4CAF50" />
                </View>
            )}
        </TouchableOpacity>
    );

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Profile</Text>
                <View style={styles.placeholder} />
            </View>

            <ScrollView style={styles.scrollView}>
                {/* Profile Card */}
                <View style={styles.profileCard}>
                    <Avatar />
                    <View style={styles.profileInfo}>
                        <Text style={styles.userName}>{user.name}</Text>
                        <Text style={styles.userEmail}>{user.email}</Text>
                        <Text style={styles.memberSince}>Member since {user.memberSince}</Text>
                    </View>
                    <TouchableOpacity style={styles.editButton}>
                        <Text style={styles.editButtonText}>Edit</Text>
                    </TouchableOpacity>
                </View>

                {/* Stats Summary */}
                <View style={styles.statsCard}>
                    <View style={styles.statItem}>
                        <Text style={styles.statValue}>{user.handicap}</Text>
                        <Text style={styles.statLabel}>Handicap</Text>
                    </View>
                    <View style={styles.statDivider} />
                    <View style={styles.statItem}>
                        <Text style={styles.statValue}>{user.totalRounds}</Text>
                        <Text style={styles.statLabel}>Rounds</Text>
                    </View>
                    <View style={styles.statDivider} />
                    <View style={styles.statItem}>
                        <Text style={styles.statValue}>{user.shotsTracked}</Text>
                        <Text style={styles.statLabel}>Shots Tracked</Text>
                    </View>
                </View>

                {/* Settings Section */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>PREFERENCES</Text>

                    <MenuItem
                        icon="bell-outline"
                        label="Notifications"
                        isSwitch
                        switchValue={notifications}
                        onSwitchChange={setNotifications}
                    />
                    <MenuItem
                        icon="video-outline"
                        label="Auto-Record Shots"
                        isSwitch
                        switchValue={autoRecord}
                        onSwitchChange={setAutoRecord}
                    />
                    <MenuItem
                        icon="ruler"
                        label="Use Metric Units"
                        isSwitch
                        switchValue={metricUnits}
                        onSwitchChange={setMetricUnits}
                    />
                </View>

                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>ACCOUNT</Text>

                    <MenuItem
                        icon="golf"
                        label="My Clubs"
                        value="14 clubs"
                    />
                    <MenuItem
                        icon="home-outline"
                        label="Home Course"
                        value="Sample GC"
                    />
                    <MenuItem
                        icon="file-export-outline"
                        label="Export Data"
                    />
                    <MenuItem
                        icon="lock-outline"
                        label="Privacy Settings"
                    />
                </View>

                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>SUPPORT</Text>

                    <MenuItem
                        icon="help-circle-outline"
                        label="Help & FAQ"
                    />
                    <MenuItem
                        icon="email-outline"
                        label="Contact Support"
                    />
                    <MenuItem
                        icon="star-outline"
                        label="Rate the App"
                    />
                    <MenuItem
                        icon="file-document-outline"
                        label="Terms & Privacy"
                    />
                </View>

                {/* Sign Out */}
                <TouchableOpacity style={styles.signOutButton}>
                    <Text style={styles.signOutText}>Sign Out</Text>
                </TouchableOpacity>

                {/* Version */}
                <Text style={styles.versionText}>LinksAI v1.0.0</Text>

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
    profileCard: {
        flexDirection: 'row',
        alignItems: 'center',
        margin: 20,
        padding: 20,
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 16,
    },
    avatar: {
        width: 70,
        height: 70,
        borderRadius: 35,
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 16,
    },
    profileInfo: {
        flex: 1,
    },
    userName: {
        color: '#FFFFFF',
        fontSize: 20,
        fontWeight: 'bold',
    },
    userEmail: {
        color: '#888888',
        fontSize: 14,
        marginTop: 2,
    },
    memberSince: {
        color: '#4CAF50',
        fontSize: 12,
        marginTop: 4,
    },
    editButton: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        backgroundColor: 'rgba(76, 175, 80, 0.2)',
        borderRadius: 16,
    },
    editButtonText: {
        color: '#4CAF50',
        fontSize: 14,
        fontWeight: '600',
    },
    statsCard: {
        flexDirection: 'row',
        marginHorizontal: 20,
        padding: 20,
        backgroundColor: 'rgba(46, 125, 50, 0.15)',
        borderRadius: 16,
        marginBottom: 20,
    },
    statItem: {
        flex: 1,
        alignItems: 'center',
    },
    statValue: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
    },
    statLabel: {
        color: '#888888',
        fontSize: 11,
        marginTop: 4,
    },
    statDivider: {
        width: 1,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    section: {
        paddingHorizontal: 20,
        marginBottom: 20,
    },
    sectionTitle: {
        color: '#4CAF50',
        fontSize: 12,
        fontWeight: 'bold',
        letterSpacing: 1,
        marginBottom: 12,
    },
    menuItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        padding: 16,
        borderRadius: 12,
        marginBottom: 8,
    },
    menuIconContainer: {
        width: 32,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 10,
    },
    menuLabel: {
        flex: 1,
        color: '#FFFFFF',
        fontSize: 16,
    },
    menuRight: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    menuValue: {
        color: '#888888',
        fontSize: 14,
        marginRight: 8,
    },
    menuArrow: {
        color: '#4CAF50',
        fontSize: 22,
    },
    signOutButton: {
        marginHorizontal: 20,
        padding: 16,
        backgroundColor: 'rgba(244, 67, 54, 0.15)',
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 10,
    },
    signOutText: {
        color: '#f44336',
        fontSize: 16,
        fontWeight: '600',
    },
    versionText: {
        color: '#666666',
        fontSize: 12,
        textAlign: 'center',
        marginTop: 20,
    },
});
