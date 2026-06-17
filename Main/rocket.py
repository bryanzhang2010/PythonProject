import json
import math
import os

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_tube_mass(od_in, id_in, length_in, density_kg_m3):
    """Calculates tube mass in grams from inches and kg/m3."""
    # Convert inches to meters
    od_m = od_in * 0.0254
    id_m = id_in * 0.0254
    length_m = length_in * 0.0254
    
    # Cylinder wall volume: V = pi * (R_out^2 - R_in^2) * L
    volume_m3 = math.pi * ((od_m / 2)**2 - ((id_m / 2)**2)) * length_m
    
    # Mass in grams = volume * density * 1000
    return volume_m3 * density_kg_m3 * 1000.0

def compute_rocket_mass():
    # Load your two clean JSON sources
    materials = load_json_file("./Main/materials.json")
    catalog = load_json_file("./Main/master_catalog.json")
    
    total_mass = 0.0
    
    print("\n=== Simulating Rocket Component Masses ===")
    
    # Loop through the components in your master catalog
    # (Adjust this loop based on your specific master_catalog.json structure)
    for part_id, properties in catalog.items():
        # Check if the component is a tube type
        if all(k in properties for k in ['outer_diameter', 'inner_diameter', 'length']):
            material_name = properties.get('material', 'cardboard').lower().strip()
            
            # Match material name against our clean database
            density = materials.get(material_name)
            
            # Fuzzy match backup if the exact string isn't found
            if density is None:
                for mat_key, mat_density in materials.items():
                    if material_name in mat_key:
                        density = mat_density
                        break
                        
            if density is not None:
                mass = calculate_tube_mass(
                    float(properties['outer_diameter']),
                    float(properties['inner_diameter']),
                    float(properties['length']),
                    density
                )
                print(f"[TUBE] {part_id:<40} -> Computed Mass: {mass:.2f}g")
                total_mass += mass
            else:
                print(f"[?] Unknown material '{material_name}' for component {part_id}")
                
    print("---------------------------------------------------------")
    print(f"Total Dry Airframe Mass: {total_mass:.2f}g\n")
    return total_mass

if __name__ == "__main__":
    compute_rocket_mass()