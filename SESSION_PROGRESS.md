# LinksAI - Session Progress Report

**Date:** 2025-11-29  
**Status:** In Progress - Setting up ML Detection

---

## ✅ Completed Today

### 1. **Kalman Filter Implementation** 
- Replaced simple exponential smoothing with proper 2D Kalman filter
- State vector: `[x, y, vx, vy]` (position + velocity)
- Handles up to 6 consecutive misses before dropping track
- File: `kalman_tracker.py`

### 2. **Physics-Based Tracking Thresholds**
- Calculated scientifically-grounded thresholds based on:
  - Ball speed: 2.5 m/s (putt), 10 m/s (chip), 70 m/s (drive)
  - Frame rate: 6.7 FPS
  - Camera FOV: 60° horizontal
  - Distance: 3m default
- File: `tracking_thresholds.py`
- **Putt mode values:**
  - Max displacement: 165px (vs arbitrary 120px)
  - Stability: 3px (vs arbitrary 12px)

### 3. **Automatic Calibration Screen**
- Auto-calibrates camera-to-screen coordinate mapping
- Tests all 8 transforms (flip X/Y, rotate combinations)
- Saves to AsyncStorage for persistence
- File: `mobile-app/CalibrationScreen.js`
- **Process:**
  1. User places ball at crosshair
  2. App captures 3 frames
  3. Tests 8 transforms
  4. Selects best match
  5. Saves calibration

### 4. **Advanced Preprocessing Pipeline**
- **CLAHE** (Contrast Limited Adaptive Histogram Equalization)
- **Bilateral Filter** (edge-preserving smoothing)
- **Gaussian Blur** (noise reduction)
- File: Updated `ball_detector.py`
- Works in varying lighting conditions

### 5. **ML-Based Detection**
- Downloaded MobileNet-SSD v2 (COCO dataset)
- Created `ml_ball_detector.py` using OpenCV DNN
- Integrated with `api_server.py`
- Detects "sports ball" class (ID 37)
- **Note:** Initially used OpenCV DNN due to Python 3.14 compatibility issues

### 6. **Dynamic FPS/Quality Adjustment**
- Monitors round-trip latency per frame
- Auto-reduces quality if latency > 200ms
- Auto-increases quality if latency < 100ms
- Dynamic throttling: adds delay if network is slow
- File: Updated `mobile-app/App.js`

### 7. **Debug Overlay**
- Real-time display of:
  - FPS (frames per second)
  - Latency (ms)
  - Quality (0.03-0.20)
  - Confidence (0-100%)
  - Mode (PUTT/CHIP/DRIVE)
- Toggle with 🐞 button (bottom left)
- File: Updated `mobile-app/App.js`

### 8. **Python 3.11 Virtual Environment**
- Installed Python 3.11.9 (for TensorFlow compatibility)
- Created `venv311` virtual environment
- Currently installing TensorFlow 2.20.0 (331.8 MB)
- Created `run_server_venv.bat` convenience script

---

## 📊 Progress Summary

**Priority 1 (Core):** ✅ 3/3 Complete (100%)
- ✅ Kalman Filter
- ✅ Physics Thresholds  
- ✅ Calibration Screen

**Priority 2 (Robustness):** ✅ 1/3 Complete (33%)
- ✅ Preprocessing Pipeline
- 🚫 Hough Parameter Tuning (SKIPPED - replaced by ML)
- 🚫 Multi-Stage Detection (SKIPPED - replaced by ML)

**Priority 3 (Performance/UX):** ✅ 2/3 Complete (67%)
- ✅ Dynamic FPS/Quality
- ❌ Better Coordinate Mapping (homography)
- ⏳ UI/UX Improvements (debug overlay done, other items pending)

**Priority 4 (Future):** ⏳ 1/3 In Progress (33%)
- ⏳ ML Detection (OpenCV DNN done, TensorFlow in progress)
- ❌ VisionCamera Migration
- ❌ Advanced Features

---

## 🔧 Current Setup

### Backend (Python)
**Environment:** Python 3.11 venv (`venv311`)  
**Dependencies:**
- TensorFlow 2.20.0 (installing...)
- OpenCV
- NumPy
- Flask
- Flask-CORS

**Files:**
- `api_server.py` - Main Flask server
- `ml_ball_detector.py` - ML detection (currently OpenCV DNN, will switch to TF)
- `ball_detector.py` - Legacy Hough circles (backup)
- `kalman_tracker.py` - State estimator
- `tracking_thresholds.py` - Physics calculations

### Frontend (Mobile App)
**Environment:** React Native / Expo  
**Dependencies:**
- expo
- react-native
- axios
- react-native-svg
- expo-camera
- @react-native-async-storage/async-storage

**Files:**
- `App.js` - Main tracking screen
- `CalibrationScreen.js` - Auto-calibration wizard

---

## 🎯 Next Steps

1. **Complete TensorFlow Installation** ⏳
   - Currently downloading (97.3/331.8 MB)
   - ETA: ~10 minutes

2. **Switch to TensorFlow Lite**
   - Update `ml_ball_detector.py` to use TFLite interpreter
   - Use `models/detect.tflite` instead of frozen graph
   - Test accuracy vs OpenCV DNN

3. **Test End-to-End**
   - Run server: `run_server_venv.bat`
   - Run app: `npx expo start`
   - Calibrate camera
   - Point at golf ball
   - Verify debug overlay shows metrics
   - Check ML confidence scores

4. **Fine-Tune ML Detection**
   - Adjust confidence threshold (currently 0.3)
   - Test with different colored balls
   - Optimize for speed vs accuracy

5. **Add Fallback Logic**
   - If ML fails, fall back to Hough circles
   - Hybrid approach for robustness

---

## 📝 Key Decisions Made

1. **ML over Hough:** Prioritized ML detection for better accuracy, skipped Hough tuning.
2. **OpenCV DNN → TensorFlow:** Started with OpenCV DNN due to Python 3.14, now switching to TensorFlow in Python 3.11 venv for better performance.
3. **Color-Agnostic:** Detect any circular object (or "sports ball" class) rather than specific colors.
4. **Physics-Based:** Use real-world physics for thresholds instead of arbitrary values.
5. **Auto-Calibration:** Eliminate manual trial-and-error for coordinate mapping.

---

## 🐛 Known Issues

1. **TensorFlow Installation:** Long download time (331.8 MB)
2. **Coordinate Mapping:** Basic transform-based, could be improved with homography matrix
3. **Speed Limit:** Not suitable for full drives (70 m/s) at current 6.7 FPS
4. **Single Ball:** Only tracks one ball at a time

---

## 📚 Documentation Created

- `QUICKSTART.md` - Setup and troubleshooting guide
- `IMPLEMENTATION_SUMMARY.md` - Technical documentation
- `TODO.md` - Task tracking (148 lines)
- `run_server_venv.bat` - Convenience script

---

## 🎉 Highlights

- **Foundational work complete:** Kalman filter, physics thresholds, calibration
- **ML detection integrated:** MobileNet-SSD via OpenCV DNN
- **Performance optimized:** Dynamic FPS/quality adjustment
- **Debug tools added:** Real-time overlay with metrics
- **Ready for testing:** Once TensorFlow installation completes

---

**Next session:** Test ML detection accuracy, fine-tune parameters, and potentially add trajectory prediction/visualization features.
