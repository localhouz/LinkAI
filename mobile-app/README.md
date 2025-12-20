# LinksAI Mobile App

A React Native mobile app built with Expo for tracking golf ball trajectories in real-time using computer vision.

## Features

- 📹 Record golf shots directly from your phone camera
- 🎯 Real-time ball tracking and trajectory analysis
- 📊 View launch angle, speed, and predicted distance
- 📱 Cross-platform (iOS & Android)

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Expo Go app installed on your mobile device
- Python 3.8+ (for backend server)

## Setup Instructions

### 1. Install Mobile App Dependencies

```bash
cd mobile-app
npm install
```

### 2. Start Backend Server

First, make sure you have the Python dependencies installed:

```bash
cd ..
pip install -r requirements.txt
```

Then start the Flask API server:

```bash
python api_server.py
```

The server will start on `http://0.0.0.0:5000`

### 3. Configure API URL

1. Find your computer's local IP address:
   - **Windows**: Open Command Prompt and run `ipconfig`, look for "IPv4 Address"
   - **Mac/Linux**: Open Terminal and run `ifconfig`, look for "inet" under your network interface

2. Update the API_URL in [App.js](App.js) line 16:
   ```javascript
   const API_URL = 'http://YOUR_IP_ADDRESS:5000';
   ```
   Example: `const API_URL = 'http://192.168.1.100:5000';`

### 4. Start the Mobile App

```bash
npm start
```

This will open Expo DevTools in your browser.

### 5. Run on Your Device

1. Install **Expo Go** from the App Store (iOS) or Google Play Store (Android)
2. Scan the QR code shown in the terminal or Expo DevTools with:
   - **iOS**: Camera app
   - **Android**: Expo Go app
3. The app will load on your device

## Usage

1. Grant camera permissions when prompted
2. Point your camera at a golf ball
3. Tap the red record button to start recording a shot
4. Tap again to stop recording (or it will auto-stop after 10 seconds)
5. Wait for the analysis to complete
6. View the results including launch angle, speed, and predicted distance

## Troubleshooting

### "Failed to process video" error
- Make sure the backend server is running
- Verify the API_URL matches your computer's IP address
- Ensure your phone and computer are on the same WiFi network
- Check that port 5000 is not blocked by your firewall

### No ball detected
- Ensure good lighting conditions
- Make sure the ball is white or light-colored
- Keep the ball in frame during the entire shot
- You can adjust detection parameters in `../config.py`:
  - `LOWER_WHITE` and `UPPER_WHITE` for color threshold
  - `MIN_BALL_RADIUS` for minimum ball size

### Camera not working
- Make sure you granted camera permissions
- Try restarting the Expo Go app
- Check that no other apps are using the camera

## Development

To run on an iOS Simulator:
```bash
npm run ios
```

To run on an Android Emulator:
```bash
npm run android
```

## Project Structure

```
mobile-app/
├── App.js              # Main application component
├── app.json            # Expo configuration
├── package.json        # Dependencies and scripts
└── README.md          # This file
```

## Backend API Endpoints

- `GET /api/health` - Health check
- `POST /api/analyze` - Upload and analyze video
- `GET /api/config` - Get current detection configuration

## License

This project is part of the LinksAI system.
