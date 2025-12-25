import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';

export default function ErrorScreen({ error, onRetry, onCancel }) {
    const getErrorMessage = (error) => {
        if (error.includes('GPS')) {
            return {
                title: 'GPS Error',
                message: 'Unable to get your location. Please enable GPS and try again.',
                icon: 'location-outline',
                iconType: 'ionicons'
            };
        } else if (error.includes('frames') || error.includes('track')) {
            return {
                title: 'Detection Error',
                message: 'Could not detect the ball in the video. Make sure the ball is visible and try again.',
                icon: 'videocam-off-outline',
                iconType: 'ionicons'
            };
        } else if (error.includes('network') || error.includes('timeout')) {
            return {
                title: 'Network Error',
                message: 'Could not connect to server. Check your internet connection and try again.',
                icon: 'wifi-off',
                iconType: 'material'
            };
        } else {
            return {
                title: 'Unexpected Error',
                message: error || 'Something went wrong. Please try again.',
                icon: 'close-circle-outline',
                iconType: 'ionicons'
            };
        }
    };

    const errorInfo = getErrorMessage(error);

    return (
        <View style={styles.container}>
            <View style={styles.errorBox}>
                <View style={styles.iconContainer}>
                    {errorInfo.iconType === 'material' ? (
                        <MaterialCommunityIcons name={errorInfo.icon} size={60} color="#ff5252" />
                    ) : (
                        <Ionicons name={errorInfo.icon} size={60} color="#ff5252" />
                    )}
                </View>
                <Text style={styles.title}>{errorInfo.title}</Text>
                <Text style={styles.message}>{errorInfo.message}</Text>

                <View style={styles.buttonContainer}>
                    <TouchableOpacity
                        style={[styles.button, styles.retryButton]}
                        onPress={onRetry}
                    >
                        <Ionicons name="refresh" size={20} color="#000" style={{ marginRight: 8 }} />
                        <Text style={styles.buttonText}>Try Again</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={[styles.button, styles.cancelButton]}
                        onPress={onCancel}
                    >
                        <Text style={styles.cancelButtonText}>Cancel</Text>
                    </TouchableOpacity>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    errorBox: {
        backgroundColor: '#1a1a1a',
        borderRadius: 20,
        padding: 30,
        alignItems: 'center',
        width: '100%',
        maxWidth: 400,
        borderWidth: 2,
        borderColor: '#ff5252',
    },
    iconContainer: {
        marginBottom: 20,
    },
    title: {
        color: '#ff5252',
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 15,
        textAlign: 'center',
    },
    message: {
        color: '#aaa',
        fontSize: 16,
        textAlign: 'center',
        lineHeight: 24,
        marginBottom: 30,
    },
    buttonContainer: {
        width: '100%',
        gap: 10,
    },
    button: {
        flexDirection: 'row',
        paddingVertical: 15,
        borderRadius: 10,
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 10,
    },
    retryButton: {
        backgroundColor: '#00e676',
    },
    cancelButton: {
        backgroundColor: 'transparent',
        borderWidth: 1,
        borderColor: '#666',
    },
    buttonText: {
        color: '#000',
        fontSize: 18,
        fontWeight: 'bold',
    },
    cancelButtonText: {
        color: '#fff',
        fontSize: 16,
    },
});
