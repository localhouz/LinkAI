"""
Shot Archetype Physics Lookup Tables Generator
Pre-calculates trajectory curves for all shot types
Exports to JSON for instant AR overlay rendering
"""

import json
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple
from pathlib import Path


@dataclass
class TrajectoryPoint:
    """Single point in a trajectory."""
    x: float  # meters (forward)
    y: float  # meters (height)
    z: float  # meters (lateral curve)
    t: float  # seconds


@dataclass
class ShotArchetype:
    """Defines a shot type with physics parameters."""
    name: str
    spin_rate: float      # RPM
    spin_axis: float      # degrees from vertical (+ = slice, - = hook)
    launch_angle: float   # typical launch angle (degrees)
    ball_speed: float     # typical ball speed (mph)
    curve_factor: float   # lateral curve multiplier


# All 9 shot archetypes
ARCHETYPES = [
    # High shots (high launch, high spin)
    ShotArchetype("high_slice", 3500, 30, 18, 150, 3.0),
    ShotArchetype("high_straight", 3000, 0, 16, 155, 0.0),
    ShotArchetype("high_hook", 3500, -30, 18, 150, -3.0),
    
    # Medium shots (medium launch, medium spin)
    ShotArchetype("medium_fade", 2500, 15, 12, 160, 1.5),
    ShotArchetype("straight", 2000, 0, 11, 165, 0.0),
    ShotArchetype("medium_draw", 2500, -15, 12, 160, -1.5),
    
    # Low shots (low launch, low spin)
    ShotArchetype("low_fade", 1800, 10, 8, 170, 1.0),
    ShotArchetype("low_straight", 1500, 0, 7, 175, 0.0),
    ShotArchetype("low_draw", 1800, -10, 8, 170, -1.0),
]


def mph_to_ms(mph: float) -> float:
    """Convert miles per hour to meters per second."""
    return mph * 0.44704


def calculate_trajectory(
    archetype: ShotArchetype,
    speed_multiplier: float = 1.0,
    dt: float = 0.02
) -> List[TrajectoryPoint]:
    """
    Calculate full trajectory for a shot archetype.
    
    Uses simplified physics model accounting for:
    - Gravity
    - Air resistance (drag)
    - Magnus effect (spin-induced curve)
    """
    
    # Initial conditions
    v0 = mph_to_ms(archetype.ball_speed * speed_multiplier)
    angle_rad = math.radians(archetype.launch_angle)
    
    vx = v0 * math.cos(angle_rad)  # forward velocity
    vy = v0 * math.sin(angle_rad)  # vertical velocity
    vz = 0.0  # lateral velocity (starts at 0)
    
    x, y, z = 0.0, 0.0, 0.0
    t = 0.0
    
    # Physics constants
    g = 9.81  # gravity (m/s²)
    rho = 1.225  # air density (kg/m³)
    
    # Golf ball properties
    mass = 0.0459  # kg
    radius = 0.02135  # meters
    area = math.pi * radius ** 2
    cd = 0.25  # drag coefficient
    cl = 0.15  # lift coefficient (Magnus)
    
    # Spin effects
    spin_rad_s = archetype.spin_rate * 2 * math.pi / 60  # convert RPM to rad/s
    spin_axis_rad = math.radians(archetype.spin_axis)
    
    trajectory = []
    
    while y >= 0 or t < 0.1:  # Continue until ball lands
        # Record point
        trajectory.append(TrajectoryPoint(x=x, y=y, z=z, t=t))
        
        # Calculate velocity magnitude
        v = math.sqrt(vx**2 + vy**2 + vz**2)
        if v < 0.01:
            break
            
        # Drag force (opposite to velocity)
        Fd = 0.5 * rho * cd * area * v**2
        ax_drag = -Fd * (vx / v) / mass
        ay_drag = -Fd * (vy / v) / mass
        az_drag = -Fd * (vz / v) / mass
        
        # Magnus force (perpendicular to velocity, based on spin)
        # Simplified: lateral acceleration proportional to spin and speed
        Fm = 0.5 * rho * cl * area * v * (spin_rad_s * radius)
        az_magnus = Fm * math.sin(spin_axis_rad) / mass * archetype.curve_factor * 0.1
        
        # Lift component (helps ball stay airborne longer with backspin)
        ay_lift = Fm * math.cos(spin_axis_rad) / mass * 0.3
        
        # Total accelerations
        ax = ax_drag
        ay = -g + ay_drag + ay_lift
        az = az_drag + az_magnus
        
        # Update velocities
        vx += ax * dt
        vy += ay * dt
        vz += az * dt
        
        # Update positions
        x += vx * dt
        y += vy * dt
        z += vz * dt
        t += dt
        
        # Safety limit
        if t > 15:
            break
    
    return trajectory


def meters_to_yards(m: float) -> float:
    """Convert meters to yards."""
    return m * 1.09361


def generate_speed_variants(archetype: ShotArchetype) -> Dict:
    """
    Generate trajectory tables for different club speeds.
    Covers range from 60% to 120% of typical speed.
    """
    
    variants = {}
    
    for speed_pct in [60, 70, 80, 90, 100, 110, 120]:
        multiplier = speed_pct / 100.0
        trajectory = calculate_trajectory(archetype, multiplier)
        
        # Convert to serializable format
        points = [
            {
                "x": round(p.x, 3),
                "y": round(p.y, 3),
                "z": round(p.z, 3),
                "t": round(p.t, 3)
            }
            for p in trajectory
        ]
        
        # Calculate summary stats
        max_height = max(p.y for p in trajectory)
        total_distance = trajectory[-1].x if trajectory else 0
        total_curve = trajectory[-1].z if trajectory else 0
        flight_time = trajectory[-1].t if trajectory else 0
        
        variants[f"{speed_pct}pct"] = {
            "speed_mph": round(archetype.ball_speed * multiplier, 1),
            "carry_yards": round(meters_to_yards(total_distance), 1),
            "max_height_yards": round(meters_to_yards(max_height), 1),
            "curve_yards": round(meters_to_yards(abs(total_curve)), 1),
            "curve_direction": "right" if total_curve > 0 else "left" if total_curve < 0 else "straight",
            "flight_time_seconds": round(flight_time, 2),
            "points": points
        }
    
    return variants


def generate_all_lookup_tables() -> Dict:
    """Generate complete lookup tables for all archetypes."""
    
    tables = {
        "version": "1.0",
        "generated_by": "generate_archetype_tables.py",
        "description": "Pre-calculated golf shot trajectories for AR overlay",
        "units": {
            "position": "meters",
            "distance_display": "yards",
            "time": "seconds",
            "speed": "mph"
        },
        "archetypes": {}
    }
    
    for archetype in ARCHETYPES:
        print(f"Generating: {archetype.name}...")
        
        variants = generate_speed_variants(archetype)
        
        tables["archetypes"][archetype.name] = {
            "display_name": archetype.name.replace("_", " ").title(),
            "typical_spin_rpm": archetype.spin_rate,
            "spin_axis_degrees": archetype.spin_axis,
            "typical_launch_angle": archetype.launch_angle,
            "typical_ball_speed_mph": archetype.ball_speed,
            "curve_type": "slice" if archetype.curve_factor > 0 else "hook" if archetype.curve_factor < 0 else "straight",
            "variants": variants
        }
    
    return tables


def generate_ar_color_scheme() -> Dict:
    """Generate color scheme for AR trajectory visualization."""
    
    return {
        "slice_shots": {
            "primary": "#FF4444",
            "secondary": "#FF8888",
            "transparent": "rgba(255, 68, 68, 0.3)"
        },
        "straight_shots": {
            "primary": "#44FF44",
            "secondary": "#88FF88",
            "transparent": "rgba(68, 255, 68, 0.3)"
        },
        "hook_shots": {
            "primary": "#4444FF",
            "secondary": "#8888FF",
            "transparent": "rgba(68, 68, 255, 0.3)"
        },
        "ghost_line": {
            "primary": "#FFFFFF",
            "secondary": "#CCCCCC",
            "transparent": "rgba(255, 255, 255, 0.5)"
        }
    }


def main():
    """Generate and save all lookup tables."""
    
    output_dir = Path("models")
    output_dir.mkdir(exist_ok=True)
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║           SHOT ARCHETYPE LOOKUP TABLE GENERATOR                 ║
╠════════════════════════════════════════════════════════════════╣
║  Generating physics-based trajectory curves for all 9 shot      ║
║  archetypes at 7 speed levels (60% to 120% of typical speed).   ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Generate main lookup tables
    tables = generate_all_lookup_tables()
    
    # Add color scheme
    tables["colors"] = generate_ar_color_scheme()
    
    # Save to JSON
    output_path = output_dir / "archetype_lookup_tables.json"
    with open(output_path, 'w') as f:
        json.dump(tables, f, indent=2)
    
    print(f"\n✅ Lookup tables saved to: {output_path}")
    
    # Generate summary
    print("\n📊 ARCHETYPE SUMMARY (at 100% speed):")
    print("━" * 60)
    
    for name, data in tables["archetypes"].items():
        variant = data["variants"]["100pct"]
        print(f"""
{data['display_name']}:
  Carry: {variant['carry_yards']:.0f} yards
  Max Height: {variant['max_height_yards']:.0f} yards
  Curve: {variant['curve_yards']:.0f} yards {variant['curve_direction']}
  Flight Time: {variant['flight_time_seconds']:.1f}s
""")
    
    # Also save a minimal version for mobile
    minimal_tables = {
        "version": tables["version"],
        "colors": tables["colors"],
        "archetypes": {}
    }
    
    for name, data in tables["archetypes"].items():
        # Only include 100% speed variant and reduce point density
        points = data["variants"]["100pct"]["points"]
        # Sample every 5th point for smaller file
        sampled_points = points[::5]
        
        minimal_tables["archetypes"][name] = {
            "display_name": data["display_name"],
            "curve_type": data["curve_type"],
            "carry_yards": data["variants"]["100pct"]["carry_yards"],
            "curve_yards": data["variants"]["100pct"]["curve_yards"],
            "points": sampled_points
        }
    
    minimal_path = output_dir / "archetype_tables_mobile.json"
    with open(minimal_path, 'w') as f:
        json.dump(minimal_tables, f)
    
    print(f"✅ Mobile-optimized tables saved to: {minimal_path}")
    print(f"   Full: {output_path.stat().st_size / 1024:.1f} KB")
    print(f"   Mobile: {minimal_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
