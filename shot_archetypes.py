"""
Golf Shot Archetype Definitions

Defines standard shot shapes with realistic physics parameters based on 
typical launch monitor data (TrackMan, FlightScope, etc.)

Each archetype includes:
- Launch angle (degrees)
- Backspin rate (rpm)
- Side spin axis tilt (degrees, + = right, - = left)
- Visual identifiers (color, label)
"""

# Shot type definitions
SHOT_TYPES = {
    "high_slice": {
        "name": "High Slice",
        "launch_angle": 16,
        "backspin_rpm": 3500,
        "side_spin_axis": 20,  # degrees right
        "color": "#FF5252",  # Red
        "description": "High launch, strong right curve",
        "typical_distance_loss": 30,  # yards vs straight
        "curve_severity": "severe"
    },
    
    "medium_slice": {
        "name": "Medium Slice",
        "launch_angle": 13,
        "backspin_rpm": 3000,
        "side_spin_axis": 15,
        "color": "#FF9800",  # Orange
        "description": "Medium launch, moderate right curve",
        "typical_distance_loss": 20,
        "curve_severity": "moderate"
    },
    
    "low_fade": {
        "name": "Low Fade",
        "launch_angle": 9,
        "backspin_rpm": 2200,
        "side_spin_axis": 8,
        "color": "#FFC107",  # Amber
        "description": "Low launch, gentle right curve (controlled)",
        "typical_distance_loss": 5,
        "curve_severity": "mild"
    },
    
    "straight": {
        "name": "Straight",
        "launch_angle": 12,
        "backspin_rpm": 2500,
        "side_spin_axis": 0,
        "color": "#4CAF50",  # Green
        "description": "Neutral flight, minimal curve",
        "typical_distance_loss": 0,
        "curve_severity": "none"
    },
    
    "low_draw": {
        "name": "Low Draw",
        "launch_angle": 9,
        "backspin_rpm": 2200,
        "side_spin_axis": -8,
        "color": "#2196F3",  # Blue
        "description": "Low launch, gentle left curve (controlled)",
        "typical_distance_loss": 5,
        "curve_severity": "mild"
    },
    
    "medium_hook": {
        "name": "Medium Hook",
        "launch_angle": 12,
        "backspin_rpm": 2300,
        "side_spin_axis": -15,
        "color": "#3F51B5",  # Indigo
        "description": "Medium launch, moderate left curve",
        "typical_distance_loss": 20,
        "curve_severity": "moderate"
    },
    
    "high_hook": {
        "name": "High Hook",
        "launch_angle": 15,
        "backspin_rpm": 2800,
        "side_spin_axis": -25,
        "color": "#9C27B0",  # Purple
        "description": "High launch, strong left curve",
        "typical_distance_loss": 30,
        "curve_severity": "severe"
    },
    
    "low_snap_hook": {
        "name": "Low Snap Hook",
        "launch_angle": 7,
        "backspin_rpm": 1800,  # Less backspin
        "side_spin_axis": -30,
        "color": "#673AB7",  # Deep Purple
        "description": "Low launch with severe left curve (often dives)",
        "typical_distance_loss": 50,
        "curve_severity": "extreme"
    },
    
    "high_balloon": {
        "name": "High Balloon",
        "launch_angle": 18,
        "backspin_rpm": 4500,  # Excessive backspin
        "side_spin_axis": 5,
        "color": "#00BCD4",  # Cyan
        "description": "Very high launch, stalls in air, limited distance",
        "typical_distance_loss": 40,
        "curve_severity": "mild"
    }
}


def get_archetype(shot_type):
    """
    Get shot archetype by key.
    
    Args:
        shot_type: Key from SHOT_TYPES dict
        
    Returns:
        dict with shot parameters or None
    """
    return SHOT_TYPES.get(shot_type)


def get_all_archetypes():
    """
    Get list of all shot archetypes.
    
    Returns:
        list of dicts
    """
    return [
        {"key": key, **values} 
        for key, values in SHOT_TYPES.items()
    ]


def get_archetypes_for_display():
    """
    Get simplified list for mobile app display.
    
    Returns:
        list of dicts with minimal info for UI
    """
    return [
        {
            "key": key,
            "name": data["name"],
            "color": data["color"],
            "description": data["description"]
        }
        for key, data in SHOT_TYPES.items()
    ]


def estimate_archetype_from_curve(observed_curve_yards, direction="right"):
    """
    Estimate which archetype matches an observed ball flight.
    
    Args:
        observed_curve_yards: How far left/right the ball curved
        direction: "right" or "left"
        
    Returns:
        Best matching archetype key
    """
    curve = abs(observed_curve_yards)
    
    if direction == "right":
        if curve > 40:
            return "high_slice"
        elif curve > 25:
            return "medium_slice"
        elif curve > 10:
            return "low_fade"
        else:
            return "straight"
    else:  # left
        if curve > 50:
            return "low_snap_hook"
        elif curve > 35:
            return "high_hook"
        elif curve > 20:
            return "medium_hook"
        elif curve > 10:
            return "low_draw"
        else:
            return "straight"


# Archetype metadata
ARCHETYPE_METADATA = {
    "source": "Based on PGA Tour and amateur launch monitor data",
    "reference_club": "Driver",
    "reference_speed": "145 mph ball speed",
    "notes": [
        "Actual spin rates vary by club, speed, and conditions",
        "These are typical values for driver shots",
        "Irons have higher backspin (4000-8000 rpm)",
        "Wedges can exceed 10,000 rpm backspin"
    ]
}


if __name__ == "__main__":
    """Quick test of archetypes"""
    print("Golf Shot Archetypes")
    print("=" * 60)
    
    for key, data in SHOT_TYPES.items():
        print(f"\n{data['name']} ({key})")
        print(f"  Launch: {data['launch_angle']}°")
        print(f"  Backspin: {data['backspin_rpm']} rpm")
        print(f"  Side spin: {data['side_spin_axis']}°")
        print(f"  Color: {data['color']}")
        print(f"  Distance loss: ~{data['typical_distance_loss']} yards")
    
    print("\n" + "=" * 60)
    print(f"\nTotal archetypes: {len(SHOT_TYPES)}")
