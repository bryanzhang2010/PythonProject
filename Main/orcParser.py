import xml.etree.ElementTree as ET
import json
import os

def build_universal_database(folder_path, output_filename="master_catalog.json"):
    print(f"--- Starting Parser ---")
    print(f"Looking for .orc files in: {os.path.abspath(folder_path)}")
    
    master_catalog = {
        "Materials": {}, 
        "Components": {} 
    }

    # List of all OpenRocket component tags we want to capture
    component_types = [
        'BodyTube', 'NoseCone', 'Transition', 'TubeCoupler', 
        'CenteringRing', 'EngineBlock', 'BulkHead', 'Parachute', 
        'LaunchLug', 'TrapezoidalFinSet', 'FreeformFinSet', 'EllipticalFinSet'
    ]

    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' was not found.")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.orc')]
    print(f"Found {len(files)} files to process.")

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        print(f"Processing: {filename}...")
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as e:
            print(f"  Could not parse {filename}: {e}")
            continue

        # 1. Parse Materials
        for mats in root.findall('.//Materials'):
            for mat in mats.findall('Material'):
                name = mat.findtext('name', 'Unknown')
                density = mat.findtext('density', '0')
                master_catalog["Materials"][name] = {"density": density}

        # 2. Parse Components (Global Search)
        # This iterates through our list and finds the tags ANYWHERE in the XML
        for tag in component_types:
            for item in root.findall(f'.//{tag}'):
                name = item.findtext('name') or item.findtext('Description') or "Unknown"
                
                # Get all children elements as a dictionary
                details = {sub.tag: sub.text for sub in item if sub.tag != 'name'}
                
                if tag not in master_catalog["Components"]:
                    master_catalog["Components"][tag] = {}
                    
                master_catalog["Components"][tag][name] = details

    # Save to file
    with open(output_filename, "w") as f:
        json.dump(master_catalog, f, indent=4)

    print(f"\nCompilation Complete!")
    print(f"Saved to: {os.path.abspath(output_filename)}")
    
    # Print summary
    for k, v in master_catalog["Components"].items():
        print(f" - {k}: {len(v)} found")

if __name__ == "__main__":
    # Get the directory where THIS script (orcParser.py) is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Join that directory with 'orc' to get the absolute path
    orc_directory = os.path.join(script_dir, 'orc')
    
    # Run the function
    build_universal_database(orc_directory)