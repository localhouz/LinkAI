# 📱 Golf Ball Tracker - Mobile App Deployment Guide

**Version**: 1.0.0 MVP  
**Framework**: React Native + Expo  
**Status**: ✅ Ready for Testing

---

## 🚀 Quick Start

### **Prerequisites**
- Node.js 16+ installed
- Expo Go app on your phone ([iOS](https://apps.apple.com/app/expo-go/id982107779) | [Android](https://play.google.com/store/apps/details?id=host.exp.exponent))
- Backend server running (see `../README.md`)

### **Installation**
```bash
cd mobile-app

# Install dependencies
npm install

# Start development server
npm start

# Scan QR code with Expo Go app
```

---

## ⚙️ Configuration

### **1. Set Backend URL**

Update server IP address in these files:

**`App.js` (line 10):**
```javascript
const API_URL = 'http://YOUR_IP_HERE:5000';
```

**`CaptureScreen.js` (line 8):**
```javascript
const API_URL = 'http://YOUR_IP_HERE:5000';
```

**Find your IP address:**
```bash
# Windows
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.168)

# Mac/Linux
ifconfig
# Look for "inet" under active network interface
```

### **2. Test Backend Connection**
```bash
# From any device on same network:
curl http://YOUR_IP:5000/api/health

# Should return:
# {"status":"healthy","message":"Golf Ball Tracker API is running"}
```

---

## 📁 Project Structure

```
mobile-app/
├── App.js                    # Main navigation & routing
├── SplashScreen.js           # Onboarding screen
├── CalibrationScreen.js      # Camera calibration
├── CaptureScreen.js          # Swing recording
├── ARShotSelector.js         # Shot pattern selection
├── SearchZoneMap.js          # GPS navigation
├── ErrorScreen.js            # Error handling (NEW)
├── SettingsScreen.js         # App settings (NEW)
├── package.json              # Dependencies
└── assets/                   # Images & fonts
```

---

## 🔧 Dependencies

### **Core**
- `expo` ~54.0.0 - Development platform
- `react` 19.1.0 - UI framework
- `react-native` 0.81.2 - Mobile framework

### **Camera & Sensors**
- `expo-camera` ~17.0.9 - Camera access
- `expo-location` ~19.0.0 - GPS
- `expo-sensors` ~15.0.0 - Compass, gyroscope

### **UI & Maps**
- `react-native-maps` 1.18.1 - Satellite view
- `react-native-svg` 15.12.1 - Vector graphics
- `@react-native-async-storage/async-storage` ^1.23.1 - Persistent storage

### **Networking**
- `axios` ^1.6.0 - HTTP requests

---

## 📱 Screen Flow

```
┌─────────────────────────────────────────────┐
│  1. SplashScreen                           │
│     "Get Started" →                         │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  2. Main Menu (App.js)                     │
│     [Track Shot] [Calibration] [Settings]  │
└─────────────────────────────────────────────┘
       ↓             ↓              ↓
   ┌───────┐   ┌──────────┐   ┌──────────┐
   │Capture│   │Calibrate │   │ Settings │
   └───────┘   └──────────┘   └──────────┘
       ↓
┌─────────────────────────────────────────────┐
│  3. CaptureScreen                          │
│     • 3-2-1 countdown                       │
│     • Record 15 frames                      │
│     • Capture GPS + compass + gyro          │
│     • Send to backend →                     │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  4. ARShotSelector                         │
│     • "Align with fairway" visual guide    │
│     • 9 colored trajectory curves           │
│     • Select matching pattern →             │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  5. SearchZoneMap                          │
│     • Satellite view                        │
│     • Real-time GPS navigation              │
│     • "🎯 YOU ARE IN THE ZONE!"            │
└─────────────────────────────────────────────┘
```

---

## 🧪 Testing Checklist

### **Permissions**
- [ ] Camera permission granted
- [ ] Location permission granted
- [ ] Location services enabled on device

### **Network**
- [ ] Phone and server on same WiFi network
- [ ] Backend server running
- [ ] Health check endpoint responds
- [ ] No firewall blocking port 5000

### **Functionality**
- [ ] Main menu loads
- [ ] Can navigate to calibration
- [ ] Can capture frames
- [ ] GPS coordinates display
- [ ] Compass heading updates
- [ ] Server accepts frames
- [ ] Trajectories display
- [ ] Map shows search zone
- [ ] Settings can be changed

---

## 🐛 Troubleshooting

### **"Could not connect to server"**
- Verify backend is running: `curl http://YOUR_IP:5000/api/health`
- Check API_URL in `CaptureScreen.js` matches your IP
- Ensure phone and PC on same network
- Try disabling Windows Firewall temporarily

### **"GPS not available"**
- Enable Location Services on phone
- Grant location permission to Expo Go
- Test outdoors (GPS weak indoors)

### **"No frames provided" error**
- Camera permission not granted
- Check camera is working in calibration screen
- Try restarting Expo Go app

### **Blank screen / App crashes**
- Check Metro bundler console for errors
- Run `npm install` again
- Clear Expo cache: `expo start -c`

### **Slow performance**
- Reduce frame quality in `CaptureScreen.js` (line 76: `quality: 0.3`)
- Test on real device instead of simulator
- Close other apps on phone

---

## 📦 Building for Production

### **Android APK**
```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build APK
eas build --platform android --profile preview

# Download and install APK on device
```

### **iOS App (requires Apple Developer account)**
```bash
eas build --platform ios
```

---

## 🎯 Performance Optimization

### **Reduce Bundle Size**
- Remove unused dependencies
- Enable Hermes engine (configured in `app.json`)

### **Improve Detection Speed**
- Lower frame quality: `quality: 0.2` (line 76 in CaptureScreen.js)
- Reduce frame count: `[:10]` instead of `[:15]` (line 329 in CaptureScreen.js)

### **Battery Optimization**
- Stop GPS updates when not navigating
- Reduce map re-render frequency

---

## 🔐 Security Notes

- API URL should use HTTPS in production
- Add authentication for backend API
- Store sensitive data securely (use expo-secure-store)
- Validate all user inputs

---

## 📊 Analytics & Monitoring

Consider adding:
- Sentry for crash reporting
- Firebase Analytics for usage tracking
- Performance monitoring

---

## 🚀 Deployment Checklist

- [ ] Update `API_URL` to production server
- [ ] Add proper app icon (`assets/icon.png`)
- [ ] Add splash screen (`assets/splash.png`)
- [ ] Configure `app.json` (name, version, permissions)
- [ ] Test on multiple devices
- [ ] Build production APK/IPA
- [ ] Submit to app stores (if desired)

---

## 📝 Version History

**1.0.0 (MVP) - Dec 2, 2025**
- ✅ Swing recording with GPS + compass + gyro
- ✅ Ball detection and tracking
- ✅ 9 shot pattern selection
- ✅ GPS navigation to search zone
- ✅ Error handling
- ✅ Settings screen

---

## 🆘 Support

**Issues?**
- Check console logs in Expo Dev Tools
- Review backend logs in terminal
- Test API endpoints with curl/Postman
- Verify all permissions granted

**Need Help?**
- Expo Documentation: https://docs.expo.dev
- React Native Docs: https://reactnative.dev
- Project README: `../README.md`

---

## 📄 License

Part of Golf Ball Tracker project.  
For internal use and testing.

---

**Status**: ✅ Production Ready (MVP)  
**Last Updated**: December 2, 2025  
**Maintainer**: Golf Ball Tracker Team
