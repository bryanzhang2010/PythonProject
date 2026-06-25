import os
import json
import math

class Rocket:
    def __init__(self, designation="", materials_db_path="./Main/materials.json", 
                 motors_db_path="./Main/motors.json", catalog_path="./Main/master_catalog.json"):
        """
        Master assembly class for the launch vehicle. Centralizes catalog lookups,
        component weight matrices, and kinematic flight solvers.
        """
        self.components = {}  # Holds attached structural instances
        self.fin_set = None    # Active FinSet geometry configuration
        
        # Core Databases
        self.materials_db = self._load_json(materials_db_path)
        self.motor_database = self._load_json(motors_db_path)
        self.catalog_db = self._load_json(catalog_path)
        
        # Set the active motor
        self.set_motor(designation)

    def _load_json(self, path):
        if not os.path.exists(path):
            print(f"[-] Warning: Asset file missing at {path}")
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"[-] Error: Failed to parse JSON at {path}")
                return {}

    def set_motor(self, designation):
        """Dynamically configures or swaps the rocket engine profile via its string ID."""
        self.designation = str(designation).upper().strip()
        self.motor_profile = self.motor_database.get(self.designation)
        
        if not self.motor_profile or not isinstance(self.motor_profile, dict):
            self.propellant_mass_kg = 0.0
            self.motor_total_mass_kg = 0.0
            self.motor_dry_mass_kg = 0.0
            self.burn_time_s = 1.0
            self.thrust_curve = []
        else:
            self.propellant_mass_kg = float(self.motor_profile.get("propellant_mass_g", 0.0)) / 1000.0
            self.motor_total_mass_kg = float(self.motor_profile.get("total_mass_g", 0.0)) / 1000.0
            self.motor_dry_mass_kg = self.motor_total_mass_kg - self.propellant_mass_kg
            self.burn_time_s = float(self.motor_profile.get("burn_time_s", 1.0))
            self.thrust_curve = self.motor_profile.get("thrust_curve", [])

    def _find_part_properties(self, part_id):
        """Helper to search for a part ID across all nested catalog categories."""
        target_catalog = self.catalog_db.get("Components", self.catalog_db)
        
        # Search inside nested dictionaries (e.g., Components -> BodyTube -> part_id)
        for category_items in target_catalog.values():
            if isinstance(category_items, dict) and part_id in category_items:
                return category_items[part_id]
                
        # Fallback if the JSON isn't nested for this specific item
        return target_catalog.get(part_id)

    def add_nose_cone(self, part_id):
        """Looks up a nose cone by its catalog string ID and adds it to the rocket structure."""
        properties = self._find_part_properties(part_id)
        if properties and isinstance(properties, dict):
            from parts import NoseCone
            self.components[part_id] = NoseCone.from_catalog(part_id, properties, self.materials_db)
            print(f"[+] Added Nose Cone: {part_id}")
        else:
            print(f"[-] Error: Nose Cone '{part_id}' not found in catalog database.")

    def add_body_tube(self, part_id):
        """Looks up a body tube by its catalog string ID and adds it to the rocket structure."""
        properties = self._find_part_properties(part_id)
        if properties and isinstance(properties, dict):
            from parts import BodyTube
            self.components[part_id] = BodyTube.from_catalog(part_id, properties, self.materials_db)
            print(f"[+] Added Body Tube: {part_id}")
        else:
            print(f"[-] Error: Body Tube '{part_id}' not found in catalog database.")

    def set_fins(self, fin_instance):
        """Binds a configured geometric fin assembly layout."""
        from parts import FinSet
        if isinstance(fin_instance, FinSet):
            self.fin_set = fin_instance
        else:
            raise TypeError("Provided object must extend the base FinSet class.")

    def get_dry_airframe_mass_kg(self):
        """Sums weights across all attached structural items dynamically."""
        total_mass_g = 0.0
        for part in self.components.values():
            if hasattr(part, 'getMass'):
                total_mass_g += float(part.getMass())
        return total_mass_g / 1000.0

    def get_total_mass_at_time(self, current_time):
        airframe_kg = self.get_dry_airframe_mass_kg()
        if current_time <= 0:
            return airframe_kg + self.motor_total_mass_kg
        if current_time >= self.burn_time_s:
            return airframe_kg + self.motor_dry_mass_kg
            
        burned_ratio = current_time / self.burn_time_s
        remaining_propellant = self.propellant_mass_kg * (1.0 - burned_ratio)
        return airframe_kg + self.motor_dry_mass_kg + remaining_propellant

    def get_thrust_at_time(self, current_time):
        if not self.thrust_curve or current_time <= 0 or current_time >= self.thrust_curve[-1][0]:
            return 0.0
        for i in range(len(self.thrust_curve) - 1):
            t0, f0 = self.thrust_curve[i]
            t1, f1 = self.thrust_curve[i+1]
            if t0 <= current_time <= t1:
                fraction = (current_time - t0) / (t1 - t0)
                return round(f0 + fraction * (f1 - f0), 3)
        return 0.0

    def simulate_trajectory(self, time_step=0.01, max_duration=6.0) -> dict:
        """
        Executes a 1D numerical flight profile. Clamps the vehicle
        to the pad if thrust < weight, preventing negative altitudes.
        """
        current_time = 0.0
        altitude = 0.0
        velocity = 0.0
        g = 9.80665
        
        time_series = []
        altitude_series = []
        velocity_series = []
        
        has_lifted_off = False
        
        while current_time <= max_duration:
            thrust = self.get_thrust_at_time(current_time)
            mass_kg = self.get_total_mass_at_time(current_time)
            
            weight = mass_kg * g
            net_force = thrust - weight
            
            if not has_lifted_off:
                if net_force > 0.0:
                    has_lifted_off = True
                    acceleration = net_force / mass_kg
                else:
                    acceleration = 0.0
                    velocity = 0.0
                    altitude = 0.0
            else:
                acceleration = net_force / mass_kg
                velocity += acceleration * time_step
                altitude += velocity * time_step
                
                if altitude <= 0.0:
                    altitude = 0.0
                    velocity = 0.0
                    time_series.append(round(current_time, 3))
                    altitude_series.append(round(altitude, 3))
                    velocity_series.append(round(velocity, 3))
                    break
            
            time_series.append(round(current_time, 3))
            altitude_series.append(round(altitude, 3))
            velocity_series.append(round(velocity, 3))
            
            current_time += time_step

        apogee_alt = max(altitude_series) if altitude_series else 0.0
        apogee_time = time_series[altitude_series.index(apogee_alt)] if altitude_series else 0.0
        max_velocity = max(velocity_series) if velocity_series else 0.0
        
        return {
            "time": time_series,
            "altitude": altitude_series,
            "velocity": velocity_series,
            "apogee_m": round(apogee_alt, 2),
            "apogee_time_s": round(apogee_time, 2),
            "max_velocity_mps": round(max_velocity, 2)
        }