"""
3D Golf Ball Trajectory Physics Simulator

Implements a 3-Degree-of-Freedom (3DOF) point mass model with:
- Gravity
- Quadratic drag (air resistance)
- Magnus force (lift from spin)
- Wind effects

Uses Runge-Kutta 4th order (RK4) numerical integration for accuracy.
"""

import numpy as np
import math


class TrajectorySimulator:
    def __init__(self):
        """Initialize physics constants."""
        # Golf ball properties
        self.ball_mass = 0.0459  # kg (regulation weight)
        self.ball_diameter = 0.0427  # meters (regulation size)
        self.ball_radius = self.ball_diameter / 2
        self.ball_area = math.pi * self.ball_radius ** 2
        
        # Air properties (sea level, 70°F)
        self.air_density = 1.225  # kg/m³
        
        # Aerodynamic coefficients (empirical)
        self.drag_coefficient = 0.25  # Typical for golf ball
        self.lift_coefficient_per_spin = 0.00001  # Simplified Magnus effect
        
        # Physics constants
        self.gravity = 9.81  # m/s²
        
    def set_conditions(self, altitude_meters=0, temperature_f=70, humidity=50):
        """
        Adjust air density for environmental conditions.
        
        Args:
            altitude_meters: Elevation above sea level
            temperature_f: Temperature in Fahrenheit
            humidity: Relative humidity percentage
        """
        # Simplified altitude correction (loses ~4% density per 1000ft)
        altitude_ft = altitude_meters * 3.28084
        density_ratio = 1 - (altitude_ft / 1000) * 0.04
        
        # Temperature correction (simplified)
        temp_c = (temperature_f - 32) * 5/9
        temp_ratio = (273 + 15) / (273 + temp_c)  # Relative to 15°C
        
        self.air_density = 1.225 * density_ratio * temp_ratio
    
    def _forces(self, state, wind_vector):
        """
        Calculate forces acting on the ball.
        
        Args:
            state: [x, y, z, vx, vy, vz, spin_rate, spin_axis]
            wind_vector: (wind_x, wind_y) in m/s
            
        Returns:
            [ax, ay, az] acceleration vector
        """
        x, y, z, vx, vy, vz, spin_rate, spin_axis = state
        
        # Relative velocity (ball velocity - wind)
        vx_rel = vx - wind_vector[0]
        vy_rel = vy - wind_vector[1]
        vz_rel = vz  # Wind doesn't affect vertical
        
        v_rel = math.sqrt(vx_rel**2 + vy_rel**2 + vz_rel**2)
        
        if v_rel < 0.1:  # Ball has stopped
            return [0, 0, -self.gravity]
        
        # Drag force (opposes motion)
        drag_magnitude = 0.5 * self.air_density * v_rel**2 * self.drag_coefficient * self.ball_area
        drag_x = -(drag_magnitude / self.ball_mass) * (vx_rel / v_rel)
        drag_y = -(drag_magnitude / self.ball_mass) * (vy_rel / v_rel)
        drag_z = -(drag_magnitude / self.ball_mass) * (vz_rel / v_rel)
        
        # Magnus force (perpendicular to velocity and spin axis)
        # Simplified: lift is proportional to spin rate
        spin_rpm = spin_rate
        lift_coefficient = self.lift_coefficient_per_spin * spin_rpm
        
        # Spin axis creates lift perpendicular to velocity
        # Positive spin_axis = ball curves right
        # Negative spin_axis = ball curves left
        spin_rad = math.radians(spin_axis)
        
        # Magnus force components
        magnus_magnitude = 0.5 * self.air_density * v_rel**2 * lift_coefficient * self.ball_area / self.ball_mass
        
        # Backspin creates upward lift
        lift_z = magnus_magnitude * math.cos(spin_rad)
        
        # Side spin creates lateral force
        lift_x = magnus_magnitude * math.sin(spin_rad)
        lift_y = 0  # Simplified (assumes spin axis in x-z plane)
        
        # Total acceleration
        ax = drag_x + lift_x
        ay = drag_y + lift_y
        az = drag_z + lift_z - self.gravity
        
        return [ax, ay, az]
    
    def _rk4_step(self, state, dt, wind_vector):
        """
        Single Runge-Kutta 4th order integration step.
        
        Args:
            state: Current state vector
            dt: Time step
            wind_vector: Wind velocity
            
        Returns:
            New state after dt
        """
        def derivative(s):
            x, y, z, vx, vy, vz, spin, axis = s
            ax, ay, az = self._forces(s, wind_vector)
            # Spin decay (simplified - loses ~2% per second)
            spin_decay = -0.02 * spin
            return [vx, vy, vz, ax, ay, az, spin_decay, 0]
        
        k1 = derivative(state)
        k2 = derivative([state[i] + dt/2 * k1[i] for i in range(len(state))])
        k3 = derivative([state[i] + dt/2 * k2[i] for i in range(len(state))])
        k4 = derivative([state[i] + dt * k3[i] for i in range(len(state))])
        
        new_state = [
            state[i] + dt/6 * (k1[i] + 2*k2[i] + 2*k3[i] + k4[i])
            for i in range(len(state))
        ]
        
        return new_state
    
    def simulate_flight(self, launch_speed_mph, launch_angle_deg, 
                       backspin_rpm, side_spin_axis_deg,
                       wind_speed_mph=0, wind_direction_deg=0,
                       temperature_f=70, altitude_m=0):
        """
        Simulate complete ball flight trajectory.
        
        Args:
            launch_speed_mph: Initial ball speed in mph
            launch_angle_deg: Launch angle (vertical) in degrees
            backspin_rpm: Backspin rate in RPM
            side_spin_axis_deg: Side spin axis tilt (+ = right, - = left)
            wind_speed_mph: Wind speed in mph
            wind_direction_deg: Wind direction (0 = headwind, 90 = right, 180 = tailwind)
            temperature_f: Temperature in Fahrenheit
            altitude_m: Altitude in meters
            
        Returns:
            dict with trajectory data
        """
        # Set environmental conditions
        self.set_conditions(altitude_m, temperature_f)
        
        # Convert units
        v0 = launch_speed_mph * 0.44704  # mph to m/s
        angle_rad = math.radians(launch_angle_deg)
        wind_speed_ms = wind_speed_mph * 0.44704
        
        # Initial velocity components
        vx0 = v0 * math.cos(angle_rad)  # Forward
        vy0 = 0  # No initial lateral velocity
        vz0 = v0 * math.sin(angle_rad)  # Upward
        
        # Wind vector (convert direction to components)
        wind_rad = math.radians(wind_direction_deg)
        wind_x = -wind_speed_ms * math.cos(wind_rad)  # Headwind is negative
        wind_y = wind_speed_ms * math.sin(wind_rad)
        wind_vector = (wind_x, wind_y)
        
        # Initial state: [x, y, z, vx, vy, vz, spin_rate, spin_axis]
        state = [0, 0, 0, vx0, vy0, vz0, backspin_rpm, side_spin_axis_deg]
        
        # Simulation parameters
        dt = 0.01  # 10ms time steps
        max_time = 15.0  # Maximum 15 seconds
        
        # Storage
        trajectory_points = []
        time = 0
        apex_height = 0
        
        # Simulate until ball hits ground
        while state[2] >= 0 and time < max_time:
            # Record point
            trajectory_points.append([state[0], state[1], state[2]])
            
            # Track apex
            if state[2] > apex_height:
                apex_height = state[2]
            
            # Integration step
            state = self._rk4_step(state, dt, wind_vector)
            time += dt
        
        # Calculate final metrics
        carry_distance = math.sqrt(state[0]**2 + state[1]**2)  # Total distance
        lateral_displacement = state[1]  # How far left/right
        flight_time = time
        
        # Convert back to yards for golf
        carry_yards = carry_distance * 1.09361
        apex_yards = apex_height * 1.09361
        curve_yards = lateral_displacement * 1.09361
        
        return {
            "points": trajectory_points,  # List of [x, y, z] in meters
            "apex_height_yards": apex_yards,
            "carry_distance_yards": carry_yards,
            "curve_yards": curve_yards,
            "flight_time_seconds": flight_time,
            "final_spin_rpm": state[6],  # Spin at landing
            "num_points": len(trajectory_points)
        }
    
    def simulate_archetype(self, archetype_data, launch_speed_mph, 
                          wind_speed_mph=0, wind_direction_deg=0):
        """
        Simulate using a shot archetype definition.
        
        Args:
            archetype_data: Dict from shot_archetypes.py
            launch_speed_mph: Detected ball speed
            wind_speed_mph: Wind speed
            wind_direction_deg: Wind direction
            
        Returns:
            Trajectory dict
        """
        return self.simulate_flight(
            launch_speed_mph=launch_speed_mph,
            launch_angle_deg=archetype_data["launch_angle"],
            backspin_rpm=archetype_data["backspin_rpm"],
            side_spin_axis_deg=archetype_data["side_spin_axis"],
            wind_speed_mph=wind_speed_mph,
            wind_direction_deg=wind_direction_deg
        )


if __name__ == "__main__":
    """Test the physics simulator"""
    print("Golf Ball Physics Simulator Test")
    print("=" * 60)
    
    sim = TrajectorySimulator()
    
    # Test case: Typical driver shot
    print("\nTest: 145mph driver, 12° launch, 2500rpm backspin, no side spin")
    result = sim.simulate_flight(
        launch_speed_mph=145,
        launch_angle_deg=12,
        backspin_rpm=2500,
        side_spin_axis_deg=0
    )
    
    print(f"  Carry distance: {result['carry_distance_yards']:.1f} yards")
    print(f"  Apex height: {result['apex_height_yards']:.1f} yards")
    print(f"  Flight time: {result['flight_time_seconds']:.2f} seconds")
    print(f"  Curve: {result['curve_yards']:.1f} yards")
    print(f"  Trajectory points: {result['num_points']}")
    
    # Test case: Slice
    print("\nTest: 140mph, 14° launch, 3200rpm, 20° side spin (slice)")
    result = sim.simulate_flight(
        launch_speed_mph=140,
        launch_angle_deg=14,
        backspin_rpm=3200,
        side_spin_axis_deg=20  # Right curve
    )
    
    print(f"  Carry distance: {result['carry_distance_yards']:.1f} yards")
    print(f"  Curve (right): {result['curve_yards']:.1f} yards")
    
    # Test case: With wind
    print("\nTest: Same shot with 10mph headwind")
    result = sim.simulate_flight(
        launch_speed_mph=140,
        launch_angle_deg=14,
        backspin_rpm=3200,
        side_spin_axis_deg=20,
        wind_speed_mph=10,
        wind_direction_deg=0  # Headwind
    )
    
    print(f"  Carry distance: {result['carry_distance_yards']:.1f} yards")
    print(f"  Distance loss from wind: ~{220 - result['carry_distance_yards']:.1f} yards")
    
    print("\n" + "=" * 60)
