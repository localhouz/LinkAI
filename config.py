# Configuration for Golf Ball Finder

# Video settings
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30

# Ball detection settings (HSV color range for white ball)
# Ball detection settings (HSV color range for white ball)
# Widened range to handle different lighting and off-white balls
LOWER_WHITE = [0, 0, 120]  # Lower value to accept darker/shadowed white
UPPER_WHITE = [180, 100, 255] # Higher saturation to accept slightly yellow/warm white
MIN_BALL_RADIUS = 2  # Minimum radius in pixels to consider as ball

# Tracking settings
N_FRAMES_TO_ANALYZE = 10  # Number of frames to use for velocity estimation
FRAME_SKIP = 1  # Process every Nth frame (1 = process all frames)

# Physics constants
GRAVITY = 9.81  # m/s^2

# Camera calibration (placeholder - needs real calibration)
PIXELS_PER_METER = 500  # Approximate conversion factor
# TODO: Implement proper camera calibration using known reference objects

# Debug settings
DEBUG_MODE = True
SHOW_VISUALIZATION = True
