import xml.etree.ElementTree as ET
import json
import os

def build_universal_database(folder_path="orc", output_filename="master_catalog.json"):
    master_catalog = {
        "Materials": {}, 
        "Components": {} 
    }

    files = [f for f in os.listdir(folder_path) if f.lower().endswith('.orc')]
    
    for filename in files:
        file_path = os.path.join(folder_path, filename)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except: continue

        # 1. Parse Materials
        for mats in root.findall('.//Materials'):
            for mat in mats.findall('Material'):
                name = mat.findtext('name', 'Unknown')
                density = mat.findtext('density', '0')
                master_catalog["Materials"][name] = {"density": density}

        # 2. Parse Components 

        for comps in root.findall('.//Components'):
            for child in comps:
                comp_type = child.tag
                name = child.findtext('name') or child.findtext('Description') or "Unknown"
                
                details = {sub.tag: sub.text for sub in child}
                
                if comp_type not in master_catalog["Components"]:
                    master_catalog["Components"][comp_type] = {}
                    
                master_catalog["Components"][comp_type][name] = details

    with open(output_filename, "w") as f:
        json.dump(master_catalog, f, indent=4)

    print(f"Compilation Complete! Saved to {output_filename}")
    for k, v in master_catalog["Components"].items():
        print(f"{k}: {len(v)} found")

if __name__ == "__main__":
    build_universal_database()