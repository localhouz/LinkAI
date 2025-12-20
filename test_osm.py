from osm_fetcher import OSMGolfFetcher

f = OSMGolfFetcher()

# Test Battle Creek Golf Club (from the GolfLogix screenshot)
# Let's try a few courses to see which have good data

courses_to_test = [
    ("Battle Creek G.C. (approx)", 36.19, -95.88),  # Tulsa area
    ("Pebble Beach", 36.5681, -121.9511),
    ("Augusta National (approx)", 33.503, -82.022),
]

for name, lat, lon in courses_to_test:
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"Location: {lat}, {lon}")
    print('='*50)
    
    d = f.get_course_details(lat, lon, 2000)
    
    print(f"Holes: {len(d.get('holes', []))}")
    print(f"Fairways: {len(d.get('fairways', []))}")  # <-- Key metric!
    print(f"Greens: {len(d.get('greens', []))}")
    print(f"Tees: {len(d.get('tees', []))}")
    print(f"Bunkers: {len(d.get('bunkers', []))}")
    print(f"Water: {len(d.get('water', []))}")
    
    if d.get('fairways'):
        print(f"\nFirst fairway has {len(d['fairways'][0].get('coords', []))} coordinates")
