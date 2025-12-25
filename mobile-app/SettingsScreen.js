import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, Switch, TextInput, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

const SETTINGS_KEY = '@golf_tracker_settings';

export default function SettingsScreen({ onClose, currentApiUrl, onApiUrlChange }) {
    const [apiUrl, setApiUrl] = useState(currentApiUrl || 'http://192.168.1.168:5000');
    const [enableDebugMode, setEnableDebugMode] = useState(false);
    const [autoSaveShots, setAutoSaveShots] = useState(true);
    const [searchRadius, setSearchRadius] = useState('15');
    const [calibrationData, setCalibrationData] = useState(null);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const settingsJson = await AsyncStorage.getItem(SETTINGS_KEY);
            if (settingsJson) {
                const settings = JSON.parse(settingsJson);
                setApiUrl(settings.apiUrl || apiUrl);
                setEnableDebugMode(settings.debugMode || false);
                setAutoSaveShots(settings.autoSave !== false);
                setSearchRadius(settings.searchRadius?.toString() || '15');
            }

            // Check for calibration data
            const calibJson = await AsyncStorage.getItem('@golf_tracker_calibration');
            if (calibJson) {
                setCalibrationData(JSON.parse(calibJson));
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    };

    const saveSettings = async () => {
        try {
            const settings = {
                apiUrl,
                debugMode: enableDebugMode,
                autoSave: autoSaveShots,
                searchRadius: parseInt(searchRadius) || 15,
            };

            await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));

            if (onApiUrlChange && apiUrl !== currentApiUrl) {
                onApiUrlChange(apiUrl);
            }

            Alert.alert('Success', 'Settings saved successfully');
        } catch (error) {
            Alert.alert('Error', 'Failed to save settings');
        }
    };

    const clearCalibration = async () => {
        Alert.alert(
            'Clear Calibration',
            'Are you sure you want to clear camera calibration?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Clear',
                    style: 'destructive',
                    onPress: async () => {
                        await AsyncStorage.removeItem('@golf_tracker_calibration');
                        setCalibrationData(null);
                        Alert.alert('Success', 'Calibration cleared');
                    },
                },
            ]
        );
    };

    const resetToDefaults = () => {
        Alert.alert(
            'Reset Settings',
            'Reset all settings to defaults?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Reset',
                    style: 'destructive',
                    onPress: () => {
                        setApiUrl('http://192.168.1.168:5000');
                        setEnableDebugMode(false);
                        setAutoSaveShots(true);
                        setSearchRadius('15');
                    },
                },
            ]
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <View style={styles.headerRow}>
                    <Ionicons name="settings" size={24} color="#FFFFFF" style={{ marginRight: 10 }} />
                    <Text style={styles.title}>Settings</Text>
                </View>
                <TouchableOpacity onPress={onClose}>
                    <Ionicons name="close" size={28} color="#FFFFFF" />
                </TouchableOpacity>
            </View>

            <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
                {/* Server Settings */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <MaterialCommunityIcons name="web" size={20} color="#00e676" />
                        <Text style={styles.sectionTitle}>Server</Text>
                    </View>

                    <View style={styles.settingRow}>
                        <Text style={styles.label}>API URL</Text>
                        <TextInput
                            style={styles.input}
                            value={apiUrl}
                            onChangeText={setApiUrl}
                            placeholder="http://192.168.1.168:5000"
                            placeholderTextColor="#666"
                            autoCapitalize="none"
                            autoCorrect={false}
                        />
                    </View>

                    <Text style={styles.hint}>
                        Change this to your server's IP address. Find it with `ipconfig` (Windows) or `ifconfig` (Mac/Linux).
                    </Text>
                </View>

                {/* Shot Analysis */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <MaterialCommunityIcons name="target" size={20} color="#00e676" />
                        <Text style={styles.sectionTitle}>Shot Analysis</Text>
                    </View>

                    <View style={styles.settingRow}>
                        <Text style={styles.label}>Search Radius (yards)</Text>
                        <TextInput
                            style={[styles.input, styles.smallInput]}
                            value={searchRadius}
                            onChangeText={setSearchRadius}
                            keyboardType="numeric"
                            placeholderTextColor="#666"
                        />
                    </View>

                    <View style={styles.settingRow}>
                        <Text style={styles.label}>Auto-Save Shots</Text>
                        <Switch
                            value={autoSaveShots}
                            onValueChange={setAutoSaveShots}
                            trackColor={{ false: '#333', true: '#00e676' }}
                            thumbColor={autoSaveShots ? '#fff' : '#666'}
                        />
                    </View>
                </View>

                {/* Calibration */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Ionicons name="camera" size={20} color="#00e676" />
                        <Text style={styles.sectionTitle}>Calibration</Text>
                    </View>

                    {calibrationData ? (
                        <>
                            <View style={styles.calibrationRow}>
                                <Ionicons name="checkmark-circle" size={18} color="#00e676" />
                                <Text style={styles.calibrationInfo}>
                                    Camera calibrated
                                </Text>
                            </View>
                            <Text style={styles.calibrationDetails}>
                                Transform: {calibrationData.transform || 'Default'}
                            </Text>
                            <TouchableOpacity
                                style={styles.dangerButton}
                                onPress={clearCalibration}
                            >
                                <Text style={styles.dangerButtonText}>Clear Calibration</Text>
                            </TouchableOpacity>
                        </>
                    ) : (
                        <View style={styles.calibrationRow}>
                            <Ionicons name="warning" size={18} color="#FF9800" />
                            <Text style={styles.calibrationInfo}>
                                Not calibrated. Run calibration from main menu.
                            </Text>
                        </View>
                    )}
                </View>

                {/* Debug */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <MaterialCommunityIcons name="bug" size={20} color="#00e676" />
                        <Text style={styles.sectionTitle}>Debug</Text>
                    </View>

                    <View style={styles.settingRow}>
                        <Text style={styles.label}>Debug Mode</Text>
                        <Switch
                            value={enableDebugMode}
                            onValueChange={setEnableDebugMode}
                            trackColor={{ false: '#333', true: '#00e676' }}
                            thumbColor={enableDebugMode ? '#fff' : '#666'}
                        />
                    </View>

                    <Text style={styles.hint}>
                        Shows detailed logs and detection overlays
                    </Text>
                </View>

                {/* Actions */}
                <View style={styles.section}>
                    <TouchableOpacity
                        style={styles.saveButton}
                        onPress={saveSettings}
                    >
                        <Ionicons name="save" size={20} color="#000" style={{ marginRight: 8 }} />
                        <Text style={styles.saveButtonText}>Save Settings</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.resetButton}
                        onPress={resetToDefaults}
                    >
                        <Text style={styles.resetButtonText}>Reset to Defaults</Text>
                    </TouchableOpacity>
                </View>

                {/* App Info */}
                <View style={styles.infoSection}>
                    <Text style={styles.infoText}>Golf Ball Tracker</Text>
                    <Text style={styles.infoSubtext}>Version 1.0.0 (MVP)</Text>
                    <Text style={styles.infoSubtext}>96% Complete</Text>
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        paddingTop: 50,
        backgroundColor: '#1a1a1a',
        borderBottomWidth: 1,
        borderBottomColor: '#333',
    },
    title: {
        color: '#fff',
        fontSize: 24,
        fontWeight: 'bold',
    },
    closeButton: {
        color: '#fff',
        fontSize: 28,
        padding: 5,
    },
    scrollView: {
        flex: 1,
    },
    content: {
        padding: 20,
    },
    section: {
        marginBottom: 30,
    },
    sectionHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 15,
    },
    sectionTitle: {
        color: '#00e676',
        fontSize: 18,
        fontWeight: 'bold',
        marginLeft: 10,
    },
    headerRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    calibrationRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
    },
    settingRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 15,
    },
    label: {
        color: '#fff',
        fontSize: 16,
        flex: 1,
    },
    input: {
        backgroundColor: '#1a1a1a',
        color: '#fff',
        padding: 12,
        borderRadius: 8,
        flex: 2,
        borderWidth: 1,
        borderColor: '#333',
    },
    smallInput: {
        flex: 0,
        width: 80,
    },
    hint: {
        color: '#666',
        fontSize: 12,
        marginTop: 5,
        fontStyle: 'italic',
    },
    calibrationInfo: {
        color: '#aaa',
        fontSize: 14,
        marginLeft: 8,
    },
    calibrationDetails: {
        color: '#666',
        fontSize: 12,
        marginBottom: 15,
    },
    saveButton: {
        flexDirection: 'row',
        backgroundColor: '#00e676',
        padding: 15,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 10,
    },
    saveButtonText: {
        color: '#000',
        fontSize: 18,
        fontWeight: 'bold',
    },
    resetButton: {
        backgroundColor: 'transparent',
        padding: 15,
        borderRadius: 10,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#666',
    },
    resetButtonText: {
        color: '#fff',
        fontSize: 16,
    },
    dangerButton: {
        backgroundColor: '#ff5252',
        padding: 12,
        borderRadius: 8,
        alignItems: 'center',
    },
    dangerButtonText: {
        color: '#fff',
        fontSize: 14,
        fontWeight: 'bold',
    },
    infoSection: {
        alignItems: 'center',
        paddingVertical: 30,
        borderTopWidth: 1,
        borderTopColor: '#333',
        marginTop: 20,
    },
    infoText: {
        color: '#fff',
        fontSize: 16,
        marginBottom: 5,
    },
    infoSubtext: {
        color: '#666',
        fontSize: 12,
    },
});
