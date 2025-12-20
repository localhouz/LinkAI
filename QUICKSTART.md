# LinksAI - Quick Start Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js 18 or 20** installed (NOT v25)
3. **Expo Go** app on your phone (iOS/Android)
4. Phone and computer on **same WiFi network**

---

## Backend Setup (Flask Server)

### 1. Install Python Dependencies
```bash
cd C:\Users\steve\Documents\LinksAI
pip install -r requirements.txt
```

### 2. Find Your Computer's IP Address
```powershell
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
# Example: 192.168.1.168
```

### 3. Update Mobile App with Your IP
Edit `mobile-app/App.js` and `mobile-app/CalibrationScreen.js`:
```javascript
const API_URL = 'http://YOUR_IP_HERE:5000';
// Example: const API_URL = 'http://192.168.1.168:5000';
```

### 4. Start the Server
```bash
python api_server.py
```

You should see:
```
============================================================
LinksAI API Server
============================================================
Server starting...
Make sure to update API_URL in the mobile app with this server's IP address
Example: http://192.168.1.100:5000
============================================================
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.168:5000
```

---

## Mobile App Setup (React Native/Expo)

### 1. Install Dependencies
```bash
cd C:\Users\steve\Documents\LinksAI\mobile-app
npm install
```

### 2. Start Expo
```bash
npx expo start
```

Or if you want tunnel mode (works across different networks):
```bash
npx expo start --tunnel
```

### 3. Open on Phone
1. Open **Expo Go** app
2. Scan the QR code shown in terminal
3. App will load on your phone

---

## First-Time Calibration

When you first open the app, you'll see the **Calibration Screen**:

1. Place a golf ball at the **green crosshair** in the center of the screen
2. Tap **"Calibrate"** button
3. Wait 2-3 seconds while app tests orientation transforms
4. Calibration result will be saved automatically
5. Main tracking screen will appear

If the ball marker doesn't align with the actual ball later:
- Tap the **"⚙️ Re-calibrate"** button (top right)
- Repeat calibration process

---

## Using the Tracker

### Starting Detection
1. Point camera at a golf ball (any color)
2. Tap the green **"Start"** button
3. Wait for **"BALL FOUND! Tracking..."** status

### What You'll See
- **Green trajectory line** showing ball's path
- **Circle marker** on current ball position
- **Status text** at top:
  - "Searching..." - Looking for ball
  - "BALL FOUND! Tracking..." - Locked onto ball
  - "Holding lock..." - Ball temporarily hidden but still tracking

### Stopping
- Tap the red **"Stop"** button

---

## Troubleshooting

### "Network request failed" or "timeout"

**Cause:** Phone can't reach the Flask server

**Fix:**
1. Check both devices are on same WiFi
2. Verify IP address in `App.js` matches your computer's IP
3. Check Windows Firewall isn't blocking port 5000:
   ```powershell
   netsh advfirewall firewall add rule name="Flask Server" dir=in action=allow protocol=TCP localport=5000
   ```

---

### Ball marker doesn't align with real ball

**Fix:**
1. Tap **"⚙️ Re-calibrate"** button
2. Place ball at crosshair
3. Re-run calibration

Or manually cycle through transforms:
- Tap **"View: Default"** button (top right)
- Cycles through: Default → Flip X → Flip Y → Rotate 90

---

### Ball not detected

**Possible causes:**
1. **Ball too far away** - Move closer (optimal: 1-5 meters)
2. **Poor lighting** - Add more light or move to brighter area
3. **Ball too small in frame** - Move closer
4. **Ball not circular** - Only works with spherical balls

**Debug:**
- Check server terminal for "Circle found at..." messages
- If you see messages, problem is coordinate mapping (re-calibrate)
- If no messages, ball isn't being detected (try better lighting)

---

### App is slow/laggy

**Causes:**
- WiFi network is slow
- Server processing is slow
- Phone is low-powered

**Fixes:**
1. **Reduce image quality** (already at 0.08, lowest practical)
2. **Disable preprocessing** in `ball_detector.py`:
   ```python
   detector = BallDetector(use_preprocessing=False)
   ```
3. **Increase intervals** in `App.js`:
   ```javascript
   const DETECT_INTERVAL_MS = 600;  // Slower search
   const TRACK_INTERVAL_MS = 250;   // Slower tracking
   ```

---

## Checking If It's Working

### Test 1: Health Check
Open in phone's web browser: `http://YOUR_IP:5000/api/health`

Should see:
```json
{
  "status": "healthy",
  "message": "LinksAI API is running"
}
```

### Test 2: Ping Server
From computer terminal:
```powershell
curl http://localhost:5000/api/health
```

Should see same JSON response.

### Test 3: Check Detection
1. Start the app
2. Point at ball
3. Tap "Start"
4. Watch server terminal for:
   ```
   Circle found at (640, 360) radius 25
   ```

---

## Advanced: Tuning Detection

### If detecting too many false circles:
In `ball_detector.py`, increase `param2`:
```python
param2=25,  # Was 18, higher = stricter
```

### If missing the ball:
Lower `param2`:
```python
param2=15,  # Lower = more sensitive
```

### For faster/slower balls:
In `mobile-app/App.js`, adjust `MAX_STEP_PX`:
```javascript
const MAX_STEP_PX = 200;  // Faster balls (was 165)
const MAX_STEP_PX = 100;  // Slower balls
```

---

## File Structure

```
LinksAI/
├── api_server.py              # Flask backend
├── ball_detector.py           # Detection logic (Hough circles + preprocessing)
├── kalman_tracker.py          # Kalman filter for smoothing
├── tracking_thresholds.py     # Physics-based threshold calculator
├── trajectory_predictor.py    # (Original, not currently used)
├── config.py                  # Configuration constants
├── requirements.txt           # Python dependencies
├── TODO.md                    # Task tracking
├── IMPLEMENTATION_SUMMARY.md  # Technical documentation
│
└── mobile-app/
    ├── App.js                 # Main tracking screen
    ├── CalibrationScreen.js   # Auto-calibration wizard
    ├── package.json           # Node dependencies
    └── ...
```

---

## What's Implemented

✅ **Ball detection** - Any color, Hough circles  
✅ **Kalman filtering** - Smooth tracking, velocity estimation  
✅ **Auto-calibration** - One-time setup per device  
✅ **Physics-based thresholds** - Scientific gating values  
✅ **Advanced preprocessing** - CLAHE + bilateral filter  
✅ **Persistent calibration** - Saved to AsyncStorage  

---

## What's Next (TODO)

See `TODO.md` for full list. Top priorities:
- Hough parameter tuning UI
- Dynamic FPS adjustment
- Confidence scoring
- ML-based detection (optional)

---

## Getting Help

1. Check server terminal for error messages
2. Check phone logs in Expo terminal
3. Review `IMPLEMENTATION_SUMMARY.md` for technical details
4. Test with "Test Connection" feature (if implemented)

---

**Quick command reference:**
```bash
# Backend
pip install -r requirements.txt
python api_server.py

# Frontend
npm install
npx expo start

# Test server
curl http://localhost:5000/api/health

# Find IP
ipconfig
```

Good luck! 🏌️‍♂️⛳
