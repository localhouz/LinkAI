"""
Flask API Server for LinksAI
Provides REST API endpoints for video analysis and ball tracking
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import tempfile
import os
import time
from hybrid_detector import HybridBallDetector
from kalman_tracker import KalmanTracker
from trajectory_predictor import TrajectoryPredictor
from config import N_FRAMES_TO_ANALYZE, FRAME_SKIP, FPS
from osm_fetcher import OSMGolfFetcher

app = Flask(__name__)

# Initialize golf course fetcher
golf_fetcher = OSMGolfFetcher()
CORS(app)  # Enable CORS for mobile app requests

# Initialize detector with hybrid pipeline (YOLO + Hough + Kalman)
# Will automatically fall back to Hough-only if YOLO model not found
yolo_model_path = 'models/yolov8n.onnx' if os.path.exists('models/yolov8n.onnx') else None
detector = HybridBallDetector(yolo_model_path=yolo_model_path, confidence_threshold=0.3)

tracker = KalmanTracker(
    process_noise=1.5,      # Moderate process noise (ball physics)
    measurement_noise=5.0,  # Measurement noise
    dt=0.15                 # Approximate time between frames (~6-7 FPS)
)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'LinksAI API is running'
    })




import base64

@app.route('/api/detect_frame', methods=['POST'])
def detect_frame():
    try:
        if 'image' not in request.files:
            return jsonify({'detected': False, 'error': 'No image'}), 400

        image_file = request.files['image']
        
        # Read directly from memory to avoid disk I/O lag
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'detected': False, 'error': 'Bad image'}), 400

        # Detect ball
        center, radius = detector.detect_ball(frame)
        
        # Update Kalman filter
        # Pass (x, y, radius) tuple or None
        measurement = (center[0], center[1], radius) if center else None
        state = tracker.update(measurement)
        
        # Draw debug info on frame
        if state:
            x, y = int(state["x"]), int(state["y"])
            r = int(state.get("r", 10))
            cv2.circle(frame, (x, y), r, (0, 255, 0), 2)
            cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)
            
            # Draw velocity vector if significant
            vx, vy = state.get("vx", 0), state.get("vy", 0)
            speed = (vx**2 + vy**2)**0.5
            if speed > 5:  # Only draw if moving
                end_x = int(x + vx * 0.1)  # Scale velocity for visualization
                end_y = int(y + vy *0.1)
                cv2.arrowedLine(frame, (x, y), (end_x, end_y), (255, 0, 255), 2)
        
        # Convert frame to base64 for display on phone
        _, buffer = cv2.imencode('.jpg', frame)
        debug_image = base64.b64encode(buffer).decode('utf-8')

        height, width = frame.shape[:2]
        
        if state:
            return jsonify({
                'detected': True,
                'x': float(state["x"]),
                'y': float(state["y"]),
                'radius': float(state.get("r", 10)),
                'vx': float(state.get("vx", 0)),
                'vy': float(state.get("vy", 0)),
                'predicted': state.get('predicted', False),
                'frame_width': width,
                'frame_height': height,
                'debug_image': debug_image
            }), 200
        else:
            return jsonify({
                'detected': False,
                'x': 0,
                'y': 0,
                'radius': 0,
                'vx': 0,
                'vy': 0,
                'frame_width': width,
                'frame_height': height,
                'debug_image': debug_image
            }), 200

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'detected': False, 'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """
    Analyzes uploaded video for golf ball tracking

    Expected: multipart/form-data with 'video' file
    Returns: JSON with trajectory analysis results
    """
    try:
        # Check if video file is in request
        if 'video' not in request.files:
            return jsonify({
                'error': 'No video file provided'
            }), 400

        video_file = request.files['video']

        # Save video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            video_path = tmp_file.name
            video_file.save(video_path)

        # Process video
        result = process_video(video_path)

        # Clean up temporary file
        os.unlink(video_path)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'error': f'Processing failed: {str(e)}'
        }), 500


def process_video(video_path):
    """
    Process video file and extract ball trajectory

    Args:
        video_path: Path to video file

    Returns:
        dict: Analysis results or error message
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {'error': 'Could not open video file'}

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    predictor = TrajectoryPredictor(fps)

    # Storage for detected positions
    positions = []
    frame_count = 0

    # Phase 1: Detect and track ball
    while cap.isOpened() and len(positions) < N_FRAMES_TO_ANALYZE:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Skip frames if configured
        if frame_count % FRAME_SKIP != 0:
            continue

        # Detect ball in current frame
        center, radius = detector.detect_ball(frame)

        if center:
            timestamp = frame_count / fps
            positions.append((center[0], center[1], timestamp))

    cap.release()

    # Check if we have enough data
    if len(positions) < 2:
        return {
            'error': 'Not enough ball positions detected',
            'frames_analyzed': len(positions),
            'suggestion': 'Make sure the ball is clearly visible and well-lit'
        }

    # Phase 2: Analyze trajectory
    try:
        (vx, vy), angle_deg, speed = predictor.estimate_initial_velocity(positions)
        ball_range = predictor.predict_range(speed, angle_deg)

        x0, y0, _ = positions[0]
        landing_zone = predictor.get_landing_zone(x0, y0, vx, vy)

        return {
            'success': True,
            'frames_analyzed': len(positions),
            'initial_velocity': {
                'vx': float(vx),
                'vy': float(vy),
                'speed': float(speed)
            },
            'launch_angle': float(angle_deg),
            'speed': float(speed),
            'predicted_range_pixels': float(ball_range),
            'landing_zone': {
                'center': [float(landing_zone['center'][0]), float(landing_zone['center'][1])],
                'distance_pixels': float(landing_zone['distance_pixels']),
                'distance_meters': float(landing_zone['distance_meters']),
                'radius': float(landing_zone['radius'])
            },
            'distance_meters': float(landing_zone['distance_meters']),
            'positions': [
                {'x': float(p[0]), 'y': float(p[1]), 't': float(p[2])}
                for p in positions
            ]
        }
    except Exception as e:
        return {
            'error': f'Trajectory analysis failed: {str(e)}',
            'frames_analyzed': len(positions)
        }


@app.route('/api/config', methods=['GET'])
def get_config():
    """Returns current configuration settings"""
    from config import (
        LOWER_WHITE, UPPER_WHITE, MIN_BALL_RADIUS,
        N_FRAMES_TO_ANALYZE, FRAME_SKIP, PIXELS_PER_METER
    )

    return jsonify({
        'lower_white': LOWER_WHITE,
        'upper_white': UPPER_WHITE,
        'min_ball_radius': MIN_BALL_RADIUS,
        'n_frames_to_analyze': N_FRAMES_TO_ANALYZE,
        'frame_skip': FRAME_SKIP,
        'pixels_per_meter': PIXELS_PER_METER
    })


@app.route('/api/analyze_shot', methods=['POST'])
def analyze_shot():
    """
    Analyze golf shot and return trajectory predictions for all shot archetypes.
    
    Expected input (JSON):
    {
        "frames": [base64_encoded_images],  // First 10-15 frames after impact
        "gps": {"lat": float, "lon": float},
        "compass_heading": float,  // degrees from North
        "gyro_tilt": float  // Phone tilt in degrees
    }
    
    Returns:
    {
        "launch_speed_mph": float,
        "launch_direction": float,
        "launch_angle": float,
        "trajectories": {
            "high_slice": {
                "points": [[lat,lon,z], ...],
                "landing_gps": {"lat": ..., "lon": ...},
                "carry_distance_yards": float,
                "curve_yards": float,
                "search_zone": {...}
            },
            ...
        },
        "weather": {...}
    }
    """
    from shot_archetypes import SHOT_TYPES, get_all_archetypes
    from trajectory_physics import TrajectorySimulator
    from gps_converter import trajectory_to_gps, create_search_zone
    from weather_service import get_weather_service
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract input data
        frames_b64 = data.get('frames', [])
        gps_data = data.get('gps', {})
        compass_heading = data.get('compass_heading', 0)
        gyro_tilt = data.get('gyro_tilt', 0)
        
        start_lat = gps_data.get('lat')
        start_lon = gps_data.get('lon')
        
        if not start_lat or not start_lon:
            return jsonify({'error': 'GPS coordinates required'}), 400
        
        if not frames_b64:
            return jsonify({'error': 'No frames provided'}), 400
        
        # Decode frames
        frames = []
        for frame_b64 in frames_b64[:15]:  # Limit to first 15 frames
            try:
                img_data = base64.b64decode(frame_b64)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is not None:
                    frames.append(frame)
            except Exception as e:
                print(f"Error decoding frame: {e}")
                continue
        
        if len(frames) < 5:
            return jsonify({'error': 'Not enough valid frames (need at least 5)'}), 400
        
        # Track ball through frames
        trajectory_points = []
        for i, frame in enumerate(frames):
            center, radius = detector.detect_ball(frame)
            if center:
                measurement = (center[0], center[1], radius)
                state = tracker.update(measurement)
                trajectory_points.append({
                    'x': state['x'],
                    'y': state['y'],
                    'frame': i,
                    'timestamp': i * 0.033  # Assume 30fps
                })
        
        if len(trajectory_points) < 3:
            return jsonify({'error': 'Could not track ball in frames'}), 400
        
        # Calculate launch vector using proper modules ✅
        from launch_vector import LaunchVectorCalculator
        from homography_calibration import quick_calibrate_from_ball
        
        # Quick calibration using detected ball size
        avg_radius = 10  # Default
        radius_samples = []
        for i, frame in enumerate(frames[:5]):
            center, radius = detector.detect_ball(frame)
            if radius > 0:
                radius_samples.append(radius)
        if radius_samples:
            avg_radius = sum(radius_samples) / len(radius_samples)
        
        calibrator = quick_calibrate_from_ball(avg_radius)
        
        # Initialize launch vector calculator
        launch_calc = LaunchVectorCalculator(calibrator=calibrator)
        
        # Calculate launch vector from trajectory
        launch_vector = launch_calc.calculate_launch_vector(
            trajectory_points=trajectory_points,
            gyro_data=gyro_tilt,
            compass_heading=compass_heading,
            fps=30
        )
        
        estimated_speed_mph = launch_vector['speed_mph']
        launch_direction = launch_vector['direction']
        launch_angle = launch_vector['launch_angle']
        
        # Get weather data
        weather_service = get_weather_service()
        weather_data = weather_service.get_wind_relative_to_shot(
            start_lat, start_lon, launch_direction
        )
        
        wind_speed = weather_data.get('wind_speed_mph', 0) if weather_data else 0
        wind_direction = weather_data.get('wind_direction_deg', 0) if weather_data else 0
        
        # Initialize physics simulator
        simulator = TrajectorySimulator()
        
        # Generate trajectories for all archetypes
        trajectories = {}
        
        for archetype_key, archetype_data in SHOT_TYPES.items():
            # Simulate trajectory
            result = simulator.simulate_archetype(
                archetype_data,
                launch_speed_mph=estimated_speed_mph,
                wind_speed_mph=wind_speed,
                wind_direction_deg=wind_direction - launch_direction  # Relative to shot
            )
            
            # Convert to GPS coordinates
            gps_points = trajectory_to_gps(
                result['points'],
                start_lat,
                start_lon,
                launch_direction
            )
            
            # Get landing point (last point above ground)
            landing_point = gps_points[-1] if gps_points else [start_lat, start_lon, 0]
            
            # Create search zone
            search_zone = create_search_zone(landing_point[:2], radius_meters=15)
            
            trajectories[archetype_key] = {
                'name': archetype_data['name'],
                'color': archetype_data['color'],
                'points': gps_points,
                'landing_gps': {'lat': landing_point[0], 'lon': landing_point[1]},
                'carry_distance_yards': result['carry_distance_yards'],
                'apex_height_yards': result['apex_height_yards'],
                'curve_yards': result['curve_yards'],
                'flight_time_seconds': result['flight_time_seconds'],
                'search_zone': search_zone
            }
        
        # Return complete analysis
        return jsonify({
            'success': True,
            'launch_speed_mph': round(estimated_speed_mph, 1),
            'launch_direction': round(launch_direction, 1),
            'launch_angle': round(launch_angle, 1),
            'frames_analyzed': len(frames),
            'trajectory_points_detected': len(trajectory_points),
            'trajectories': trajectories,
            'weather': weather_data,
            'note': 'Speed calculation is estimated - needs calibration for accuracy'
        })
        
    except Exception as e:
        print(f"Error in analyze_shot: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/search', methods=['GET'])
def search_courses():
    """
    Search for golf courses by name.
    
    Query params:
        name: Course name to search for (required)
        country: Country code (default: US)
    
    Returns:
        List of matching courses with name, id, lat, lon
    """
    try:
        course_name = request.args.get('name', '')
        country = request.args.get('country', 'US')
        
        if not course_name:
            return jsonify({'error': 'Course name is required'}), 400
        
        courses = golf_fetcher.search_courses_by_name(course_name, country)
        
        return jsonify({
            'success': True,
            'count': len(courses),
            'courses': courses
        })
        
    except Exception as e:
        print(f"Error searching courses: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/nearby', methods=['GET'])
def get_nearby_courses():
    """
    Search for golf courses near a GPS location.
    
    Query params:
        lat: Latitude (required)
        lon: Longitude (required)
        radius: Search radius in meters (default: 5000)
    
    Returns:
        List of nearby courses
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 5000, type=int)
        
        if lat is None or lon is None:
            return jsonify({'error': 'lat and lon are required'}), 400
        
        # Use Overpass query to find golf courses near location
        query = f"""
        [out:json];
        (
          way["leisure"="golf_course"](around:{radius},{lat},{lon});
          relation["leisure"="golf_course"](around:{radius},{lat},{lon});
        );
        out center;
        """
        
        import requests as req
        response = req.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        courses = []
        for element in data.get('elements', []):
            course = {
                'id': element.get('id'),
                'name': element.get('tags', {}).get('name', 'Unknown Course'),
                'type': element.get('type'),
            }
            
            if 'center' in element:
                course['lat'] = element['center']['lat']
                course['lon'] = element['center']['lon']
            elif 'lat' in element and 'lon' in element:
                course['lat'] = element['lat']
                course['lon'] = element['lon']
            
            courses.append(course)
        
        return jsonify({
            'success': True,
            'count': len(courses),
            'courses': courses
        })
        
    except Exception as e:
        print(f"Error finding nearby courses: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/details', methods=['GET'])
def get_course_details():
    """
    Get detailed golf course features (greens, tees, fairways, hazards).
    
    Query params:
        lat: Latitude of course center (required)
        lon: Longitude of course center (required)
        radius: Search radius in meters (default: 1000)
    
    Returns:
        Course features including greens, tees, fairways, bunkers, water hazards
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 1000, type=int)
        
        if lat is None or lon is None:
            return jsonify({'error': 'lat and lon are required'}), 400
        
        features = golf_fetcher.get_course_details(lat, lon, radius)
        
        return jsonify({
            'success': True,
            'lat': lat,
            'lon': lon,
            'radius': radius,
            'features': features,
            'summary': {
                'holes': len(features.get('holes', [])),
                'greens': len(features['greens']),
                'tees': len(features['tees']),
                'fairways': len(features['fairways']),
                'bunkers': len(features['bunkers']),
                'water': len(features['water']),
                'pins': len(features['pins'])
            }
        })
        
    except Exception as e:
        print(f"Error getting course details: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("LinksAI API Server")
    print("=" * 60)
    print("Server starting...")
    print("Make sure to update API_URL in the mobile app with this server's IP address")
    print("Example: http://192.168.1.100:5000")
    print("=" * 60)

    # Run on all interfaces so mobile devices can connect
    app.run(host='0.0.0.0', port=5000, debug=True)
