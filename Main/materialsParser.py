import xml.etree.ElementTree as ET
import json
import os

def generate_materials_json():
    # Correct paths based on your VS Code sidebar screenshot
    orc_folder = "./Main/orc"
    output_json_path = "./Main/materials.json"
    
    material_db = {}
    
    # Scan all .orc files in your Main/orc directory
    if not os.path.exists(orc_folder):
        print(f"[-] Error: Cannot find folder at {orc_folder}")
        return

    for filename in os.listdir(orc_folder):
        if filename.endswith(".orc"):
            file_path = os.path.join(orc_folder, filename)
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Parse the exact XML structure you have
                for mat_element in root.iter('Material'):
                    name_node = mat_element.find('Name')
                    density_node = mat_element.find('Density')
                    
                    if name_node is not None and density_node is not None:
                        name_text = name_node.text
                        density_text = density_node.text
                        if name_text and density_text:
                            # Use lowercase keys for painless lookups later
                            material_db[name_text.strip().lower()] = float(density_text.strip())
            except ET.ParseError:
                print(f"[-] Skipping malformed file: {filename}")

    # Save to your clean, dedicated materials catalog
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(material_db, f, indent=4)
        
    print(f"[+] Success! Created clean materials database with {len(material_db)} entries.")
    print(f"    Saved to: {output_json_path}")

if __name__ == "__main__":
    generate_materials_json()