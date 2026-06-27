import os
import json
import math
import numpy as np

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

    def simulate_trajectory(self, time_step=0.01, max_duration=10.0, wind_speed=0.0):
        """Simulates 2D flight profile including aerodynamic drag and horizontal wind drag."""
        # Baseline physical properties extracted from chosen UI layout specs
        # (Assuming mass calculations sum your motor, nose, tube, and fin selections)
        dry_mass = 0.050  # 50 grams baseline airframe sample
        
        # Pull geometric parameters safely from your active selections
        # Convert outer radius from mm to meters for cross-sectional area: A = pi * r^2
        r_outer_m = 0.0121  # Sample default (BT-50 / PNC-50 outer profile)
        area = np.pi * (r_outer_m ** 2)
        cd = 0.45  # Default total drag coeff coefficient (sum of nose + airframe friction)
        rho = 1.225  # Air density at sea level (kg/m^3)
        g = 9.81
        
        # Initialize 2D Kinematic States
        t = 0.0
        x, y = 0.0, 0.0
        vx, vy = 0.0, 0.0
        
        # Data storage channels
        history = {
            "time": [],
            "x_position": [],
            "altitude": [],
            "vx": [],
            "vy": [],
            "apogee_m": 0.0,
            "apogee_time_s": 0.0,
            "drift_m": 0.0
        }
        
        # Extract motor thrust curve array safely
        # Sample format: [[0.0, 0.0], [0.1, 6.0], [0.36, 0.0]]
        # Ensure we have the selected motor profile loaded safely
        motor_profile = {}
        if hasattr(self, "current_motor"):
            motor_profile = self.current_motor
        elif hasattr(self, "motor"):
            motor_profile = self.motor
        elif hasattr(self, "motor_database") and hasattr(self, "designation"):
            # Fallback direct lookup if the profile wasn't stored as an instance attribute
            motor_profile = self.motor_database.get(self.designation, {})

        # Extract motor configuration arrays safely from your parser dictionary
        thrust_curve = motor_profile.get("thrust_curve", [[0.0, 0.0]])
        motor_mass_total = motor_profile.get("total_mass_g", 6.6) / 1000.0
        propellant_mass = motor_profile.get("propellant_mass_g", 2.0) / 1000.0
        burn_duration = motor_profile.get("burn_time_s", 0.36)
        
        def get_thrust(current_time):
            for i in range(len(thrust_curve) - 1):
                t0, f0 = thrust_curve[i]
                t1, f1 = thrust_curve[i+1]
                if t0 <= current_time <= t1:
                    # Linear interpolation across curve timestamps
                    return f0 + (f1 - f0) * ((current_time - t0) / (t1 - t0))
            return 0.0

        # Run flight simulation iteration loop
        while t < max_duration and y >= 0.0:
            # 1. Determine changing mass profile during motor burn
            if t < burn_duration:
                current_propellant_spent = (t / burn_duration) * propellant_mass
                current_mass = dry_mass + motor_mass_total - current_propellant_spent
                thrust = get_thrust(t)
            else:
                current_mass = dry_mass + (motor_mass_total - propellant_mass)
                thrust = 0.0
                
            # 2. Calculate Aerodynamics relative to wind vector
            # Wind travels horizontally; rocket flows against or with it
            v_rel_x = vx - wind_speed
            v_rel_y = vy
            v_mag = np.sqrt(v_rel_x**2 + v_rel_y**2)
            
            if v_mag > 0.001:
                # Calculate angle of attack vector axis
                sin_alpha = v_rel_x / v_mag
                cos_alpha = v_rel_y / v_mag
                
                # Compute total drag magnitude
                f_drag = 0.5 * rho * (v_mag**2) * area * cd
                fx_drag = f_drag * sin_alpha
                fy_drag = f_drag * cos_alpha
            else:
                fx_drag = 0.0
                fy_drag = 0.0
                sin_alpha = 0.0
                cos_alpha = 1.0

            # 3. Handle Thrust Direction (Assumes vehicle self-stabilizes into air velocity vector)
            fx_thrust = thrust * (-sin_alpha) if t < burn_duration else 0.0
            fy_thrust = thrust * cos_alpha if t < burn_duration else 0.0
            
            # Guard liftoff condition: cannot launch unless vertical force clears gravity threshold
            if y == 0.0 and fy_thrust <= (current_mass * g):
                fx_thrust, fy_thrust = 0.0, 0.0
                vx, vy = 0.0, 0.0
            
            # 4. Sum Forces & Integrate Equations of Motion (Euler Method)
            ax = (fx_thrust - fx_drag) / current_mass
            ay = (fy_thrust - fy_drag - (current_mass * g)) / current_mass
            
            vx += ax * time_step
            vy += ay * time_step
            
            x += vx * time_step
            y += vy * time_step
            
            # Prevent underground clip values
            if y < 0.0:
                y = 0.0
                vy = 0.0
                vx = 0.0
                
            # Log metrics tracking channels
            history["time"].append(t)
            history["x_position"].append(x)
            history["altitude"].append(y)
            history["vx"].append(vx)
            history["vy"].append(vy)
            
            t += time_step
            
        # Compile summary parameters
        if history["altitude"]:
            history["apogee_m"] = round(max(history["altitude"]), 2)
            max_idx = history["altitude"].index(max(history["altitude"]))
            history["apogee_time_s"] = round(history["time"][max_idx], 2)
            history["drift_m"] = round(x, 2)
            
        return history