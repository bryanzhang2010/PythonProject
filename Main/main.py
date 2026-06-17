import json
import os
from rocket import calculate_tube_mass, load_json_file

def fuzzy_find_part(data, keywords):
    """
    Recursively scans the catalog keys. If a key contains ALL specified 
    keywords (case-insensitive), it returns that component's data.
    e.g., keywords=["nose cone", "pnc-20"]
    """
    if isinstance(data, dict):
        for key, value in data.items():
            # Check if every single keyword is hidden somewhere inside the dictionary key string
            if all(kw.lower() in key.lower() for kw in keywords):
                return key, value # Return the full official key name and the data
            
            # Continue drilling down recursively
            result = fuzzy_find_part(value, keywords)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = fuzzy_find_part(item, keywords)
            if result is not None:
                return result
    return None

def run_rocket_test():
    catalog_path = "./Main/master_catalog.json"
    materials_path = "./Main/materials.json"
    
    if not os.path.exists(catalog_path) or not os.path.exists(materials_path):
        print("[-] Error: Missing database files in ./Main/")
        return

    catalog = load_json_file(catalog_path)
    materials = load_json_file(materials_path)
    
    print("==================================================")
    print("           ROCKET COMPONENT INTEGRATION TEST       ")
    print("==================================================")

    # --- NEW FUZZY SEARCH CONFIG ---
    # Instead of full strings, just provide lists of identifying keywords!
    test_build_queries = [
        ["bth-20", "heavy wall"],
        ["nose cone", "pnc-20"],
        ["engine hook", "eh-2"]
    ]
    
    total_mass = 0.0
    
    for keywords in test_build_queries:
        match = fuzzy_find_part(catalog, keywords)
        
        if match:
            full_key_name, part_data = match
            part_mass = 0.0
            
            # --- TUBE CALCULATIONS (Matching your JSON's Capitalization) ---
            if "OutsideDiameter" in part_data and "InsideDiameter" in part_data and "Length" in part_data:
                mat_name = part_data.get('Material', 'cardboard').lower().strip()
                density = materials.get(mat_name, 680.0) # Default to cardboard density
                
                part_mass = calculate_tube_mass(
                    float(part_data['OutsideDiameter']),
                    float(part_data['InsideDiameter']),
                    float(part_data['Length']),
                    density
                )
            
            # --- STATIC OBJECT CALCULATIONS (Nose Cones / Hooks) ---
            elif "Mass" in part_data:
                part_mass = float(part_data["Mass"])
                
            total_mass += part_mass
            
            # Shorten the long display name for a clean terminal output
            display_name = full_key_name[:50] + "..." if len(full_key_name) > 50 else full_key_name
            print(f"[FOUND] {display_name:<53} | Mass: {part_mass:.2f}g")
        else:
            print(f"[MISSING] Could not find part matching keywords: {keywords}")

    print("----------------------------------------------------------------------")
    print(f"Calculated Empty Airframe Mass: {total_mass:.2f}g")
    print("======================================================================")

if __name__ == "__main__":
    run_rocket_test()