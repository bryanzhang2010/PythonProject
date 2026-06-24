import os
import json
import math
from parts import FinSet, NoseCone, BodyTube  # <-- No "Main." prefix

class Rocket:
    def __init__(self, designation, materials_db_path="./Main/materials.json", motors_db_path="./Main/motors.json"):
        """
        Master assembly class for the launch vehicle. Compiles structural parts, 
        aerodynamics, and links the parsed motor thrust configurations.
        """
        # Force string type casting to guarantee .upper() and .strip() never fail
        self.designation = str(designation).upper().strip()
        self.components = {}  # Holds structural part instances (NoseCone, BodyTube)
        self.fin_set = None    # Active FinSet configuration instance
        
        # Load local JSON materials asset database
        self.materials_db = self._load_json(materials_db_path)
        
        # Safely extract the motor database log
        if not os.path.exists(motors_db_path):
            print(f"[-] Warning: Motor database file not found at {motors_db_path}")
            self.motor_database = {}
        else:
            with open(motors_db_path, 'r', encoding='utf-8') as f:
                self.motor_database = json.load(f)
            
        # Connect the motor specification dictionary profile safely
        self.motor_profile = self.motor_database.get(self.designation)
        
        if not self.motor_profile or not isinstance(self.motor_profile, dict):
            print(f"[-] Warning: Propulsion engine '{self.designation}' profile not found or invalid.")
            self.propellant_mass_kg = 0.0
            self.motor_total_mass_kg = 0.0
            self.motor_dry_mass_kg = 0.0
            self.burn_time_s = 1.0
            self.thrust_curve = []
        else:
            # Safely cast metrics to floats to guarantee physics math processing runs smoothly
            self.propellant_mass_kg = float(self.motor_profile.get("propellant_mass_g", 0.0)) / 1000.0
            self.motor_total_mass_kg = float(self.motor_profile.get("total_mass_g", 0.0)) / 1000.0
            self.motor_dry_mass_kg = self.motor_total_mass_kg - self.propellant_mass_kg
            self.burn_time_s = float(self.motor_profile.get("burn_time_s", 1.0))
            self.thrust_curve = self.motor_profile.get("thrust_curve", [])

    def _load_json(self, path):
        """Internal helper to safely read files without crashing if they don't exist yet."""
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def attach_structure_from_catalog(self, catalog_path="./Main/master_catalog.json"):
        """
        Parses master catalog items safely, converting keys to strings,
        validating parameters, and ensuring no corrupt objects break assembly.
        """
        catalog = self._load_json(catalog_path)
        if not catalog:
            print(f"[-] Warning: Structural catalog data is empty or missing at {catalog_path}")
            return

        for part_id, properties in catalog.items():
            if not properties or not isinstance(properties, dict):
                continue
                
            part_id_lower = str(part_id).lower()
            part_type = str(properties.get("type", "")).lower().strip()
            
            try:
                # 1. Look for Nose Cone indicators
                if "nose" in part_id_lower or part_type == "nosecone":
                    cone_instance = NoseCone.from_catalog(part_id, properties, self.materials_db)
                    if cone_instance is not None:
                        self.components[part_id] = cone_instance
                
                # 2. Look for Body Tube indicators (handles case-insensitive configurations)
                elif "tube" in part_id_lower or any(k in properties for k in ['outer_diameter', 'inner_diameter', 'length', 'Length', 'OutsideDiameter']):
                    tube_instance = BodyTube.from_catalog(part_id, properties, self.materials_db)
                    if tube_instance is not None:
                        self.components[part_id] = tube_instance
                        
            except Exception as e:
                print(f"[-] Skipping corrupted component entry [{part_id}]: {e}")
                continue

    def set_fins(self, fin_instance):
        """Attaches an explicit FinSet geometry instance (Trapezoidal, Elliptical, or Freeform)"""
        if isinstance(fin_instance, FinSet):
            self.fin_set = fin_instance
        else:
            raise TypeError("Provided object must extend the base FinSet abstract class.")

    def get_dry_airframe_mass_kg(self):
        """Sums the weight of all structural components currently attached (excluding motor)."""
        total_mass_g = 0.0
        
        for part in self.components.values():
            # Safely verify structural attributes or execution methods before computing weight sum
            if hasattr(part, 'getMass'):
                total_mass_g += float(part.getMass())
            elif hasattr(part, 'mass'):
                total_mass_g += float(part.mass)
                
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

    def get_aerodynamics(self) -> dict:
        """
        Gathers stability calculations across the composite structure.
        Explicit type hint forcing guarantees VS Code intercepts dictionary properties.
        """
        if self.fin_set:
            return self.fin_set.calculate_aerodynamics()
        return {"C_N_alpha": 0.0, "X_cp_mm": 0.0}