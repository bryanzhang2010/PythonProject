import json
import math
import os

class Rocket:
    def __init__(self, designation, materials_db_path="./Main/materials.json", motors_db_path="./Main/motors.json"):
        """
        Master assembly class for the launch vehicle. Compiles structural parts, 
        aerodynamics, and links the parsed motor thrust configurations.
        """
        self.designation = designation.upper().strip()
        self.components = {}  # Holds nose_cone, body_tube, etc.
        self.fin_set = None    # Active FinSet configuration instance
        
        # 1. Load materials and motor profiles from your database pipelines
        self.materials_db = self._load_json(materials_db_path)
        with open(motors_db_path, 'r', encoding='utf-8') as f:
            self.motor_database = json.load(f)
            
        # 2. Connect the engine specs
        self.motor_profile = self.motor_database.get(self.designation)
        if not self.motor_profile:
            print(f"[-] Warning: Propulsion engine '{self.designation}' not found in library.")
            self.propellant_mass_kg = 0.0
            self.motor_total_mass_kg = 0.0
            self.motor_dry_mass_kg = 0.0
            self.burn_time_s = 0.0
            self.thrust_curve = []
        else:
            self.propellant_mass_kg = self.motor_profile.get("propellant_mass_g", 0.0) / 1000.0
            self.motor_total_mass_kg = self.motor_profile.get("total_mass_g", 0.0) / 1000.0
            self.motor_dry_mass_kg = self.motor_total_mass_kg - self.propellant_mass_kg
            self.burn_time_s = self.motor_profile.get("burn_time_s", 1.0)
            self.thrust_curve = self.motor_profile.get("thrust_curve", [])

    def _load_json(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def attach_structure_from_catalog(self, catalog_path="./Main/master_catalog.json"):
        """
        Automatically parses your master catalog file, builds NoseCone/BodyTube 
        objects, and hooks them to the structural dictionary.
        """
        catalog = self._load_json(catalog_path)
        for part_id, properties in catalog.items():
            part_id_lower = part_id.lower()
            
            if "nose" in part_id_lower or properties.get("type") == "nosecone":
                self.components[part_id] = NoseCone.from_catalog(part_id, properties, self.materials_db)
            elif all(k in properties for k in ['outer_diameter', 'inner_diameter', 'length']):
                self.components[part_id] = BodyTube.from_catalog(part_id, properties, self.materials_db)

    def set_fins(self, fin_instance):
        """Attaches an explicit FinSet geometry instance (Trapezoidal, Elliptical, or Freeform)"""
        if isinstance(fin_instance, FinSet):
            self.fin_set = fin_instance
        else:
            raise TypeError("Provided object must extend the base FinSet abstract class.")

    def get_dry_airframe_mass_kg(self):
        """Sums the weight of all structural components currently attached (excluding motor)."""
        total_mass_g = sum(part.getMass() for part in self.components.values())
        return total_mass_g / 1000.0

    def get_total_mass_at_time(self, current_time):
        """
        Computes dynamic vehicle mass matrix (Airframe + Empty Casing + Propellant Delta) 
        for integration loops.
        """
        airframe_kg = self.get_dry_airframe_mass_kg()
        
        if current_time <= 0:
            return airframe_kg + self.motor_total_mass_kg
        if current_time >= self.burn_time_s:
            return airframe_kg + self.motor_dry_mass_kg
            
        # Linear approximation of propellant consumption profile
        burned_ratio = current_time / self.burn_time_s
        remaining_propellant = self.propellant_mass_kg * (1.0 - burned_ratio)
        return airframe_kg + self.motor_dry_mass_kg + remaining_propellant

    def get_thrust_at_time(self, current_time):
        """Linearly interpolates raw coordinate intervals to get real-time thrust forces (Newtons)."""
        if not self.thrust_curve or current_time <= 0:
            return 0.0
        if current_time >= self.thrust_curve[-1][0]:
            return 0.0

        for i in range(len(self.thrust_curve) - 1):
            t0, f0 = self.thrust_curve[i]
            t1, f1 = self.thrust_curve[i+1]
            
            if t0 <= current_time <= t1:
                fraction = (current_time - t0) / (t1 - t0)
                return round(f0 + fraction * (f1 - f0), 3)
        return 0.0

    def get_aerodynamics(self):
        """Gathers stability calculations across the composite structure."""
        if self.fin_set:
            return self.fin_set.calculate_aerodynamics()
        return {"C_N_alpha": 0.0, "X_cp_mm": 0.0}


# Operational execution block for self-contained testing
if __name__ == "__main__":
    print("=== Testing Full Component Hierarchy ===")
    
    # 1. Initialize rocket with your parsed data layout profiles
    my_rocket = Rocket(designation="C3.4T")
    
    # 2. Attach airframe elements from your inventory files
    my_rocket.attach_structure_from_catalog()
    
    # 3. Create a Trapezoidal fin planform configuration and attach it
    # parameters: count, body_diameter, root_chord, tip_chord, semi_span, sweep_length
    fins = TrapezoidalFinSet(count=4, body_diameter=0.038, root_chord=0.080, tip_chord=0.040, semi_span=0.050, sweep_length=0.025)
    my_rocket.set_fins(fins)
    
    # 4. Print telemetry checks out to the terminal console screen
    print(f"[+] Total Attached Structural Parts: {len(my_rocket.components)}")
    print(f"[+] Computed Dry Structure Mass   : {my_rocket.get_dry_airframe_mass_kg() * 1000.0:.2f}g")
    print(f"[+] Liftoff Mass (Loaded)        : {my_rocket.get_total_mass_at_time(0.0) * 1000.0:.2f}g")
    
    # 5. Output aerodynamic parameters from our Barrowman models
    aero = my_rocket.get_aerodynamics()
    print(f"[+] Fin Aero Lift Coefficient    : {aero.get('C_N_alpha')}")
    print(f"[+] Fin Center of Pressure (CP)  : {aero.get('X_cp_mm')} mm from root leading edge")