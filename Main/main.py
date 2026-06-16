import json
import os
from parts import BodyTube, NoseCone 

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    catalog_path = os.path.join(script_dir, 'master_catalog.json')

    with open(catalog_path, 'r') as f:
        catalog = json.load(f)

    # ADD THIS: Simple verification to see if it loaded
    components = catalog.get("Components", {})
    print(f"Successfully loaded {len(components)} component categories.")

    print("Available categories in master_catalog:")
    for category in catalog['Components'].keys():
        print(f"- {category}")
    
    # Example check: How many BodyTubes are there?
    if "BodyTube" in components:
        print(f"Found {len(components['BodyTube'])} body tubes in catalog.")

# THIS IS CRITICAL: This line tells Python to actually run the main() function
if __name__ == "__main__":
    main()

