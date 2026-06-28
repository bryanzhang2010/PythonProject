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

    def simulate_trajectory(self, time_step=0.01, max_duration=12.0, wind_speed=0.0):
        """Simulates 2D flight profile including aerodynamic drag and horizontal wind drift."""
        
        g = 9.81
        rho = 1.225
        cd = 0.45


        # --- Get reference area from attached body tube or nose cone ---
        r_outer_m = 0.0121  # fallback default (BT-50 size)
        for part in self.components.values():
            if hasattr(part, 'outer_diameter'):
                r_outer_m = float(part.outer_diameter) / 2.0 / 1000.0
                break
            elif hasattr(part, 'outside_diameter'):
                r_outer_m = float(part.outside_diameter) / 2.0 / 1000.0
                break
        area = math.pi * (r_outer_m ** 2)


        # --- Mass ---
        dry_mass = self.get_dry_airframe_mass_kg()
        if dry_mass < 0.01:
            dry_mass = 0.05  # 50g fallback if no components attached


        # --- Liftoff guard ---
        initial_mass = dry_mass + self.motor_total_mass_kg
        max_thrust = max((pt[1] for pt in self.thrust_curve), default=0.0)
        if max_thrust <= initial_mass * g:
            return {
                "time": [0.0], "x_position": [0.0], "altitude": [0.0],
                "vx": [0.0], "vy": [0.0],
                "apogee_m": 0.0, "apogee_time_s": 0.0, "drift_m": 0.0
            }


        # --- State ---
        t = 0.0
        x, y = 0.0, 0.0
        vx, vy = 0.0, 0.0
        launched = False


        history = {
            "time": [], "x_position": [], "altitude": [],
            "vx": [], "vy": [],
            "apogee_m": 0.0, "apogee_time_s": 0.0, "drift_m": 0.0
        }


        while t < max_duration and y >= 0.0:
            thrust = self.get_thrust_at_time(t)
            current_mass = self.get_total_mass_at_time(t)


            # Liftoff check — hold on pad until thrust exceeds weight
            if not launched:
                if thrust > current_mass * g:
                    launched = True
                else:
                    history["time"].append(t)
                    history["x_position"].append(0.0)
                    history["altitude"].append(0.0)
                    history["vx"].append(0.0)
                    history["vy"].append(0.0)
                    t += time_step
                    continue


            # Drag — relative to wind
            v_rel_x = vx - wind_speed
            v_rel_y = vy
            v_mag = math.sqrt(v_rel_x**2 + v_rel_y**2)


            if v_mag > 0.001:
                f_drag = 0.5 * rho * v_mag**2 * area * cd
                fx_drag = -f_drag * (v_rel_x / v_mag)
                fy_drag = -f_drag * (v_rel_y / v_mag)
            else:
                fx_drag = 0.0
                fy_drag = 0.0


            # Thrust — always vertical (rocket self-stabilizes upward during burn)
            fx_thrust = 0.0
            fy_thrust = thrust


            # Equations of motion
            ax = (fx_thrust + fx_drag) / current_mass
            ay = (fy_thrust + fy_drag) / current_mass - g


            vx += ax * time_step
            vy += ay * time_step
            x  += vx * time_step
            y  += vy * time_step


            if y < 0.0:
                y = 0.0


            history["time"].append(round(t, 4))
            history["x_position"].append(round(x, 4))
            history["altitude"].append(round(y, 4))
            history["vx"].append(round(vx, 4))
            history["vy"].append(round(vy, 4))


            t += time_step


            # Stop once it lands after liftoff
            if launched and y <= 0.0 and vy <= 0.0 and t > 1.0:
                break


        # Summary
        if history["altitude"]:
            history["apogee_m"] = round(max(history["altitude"]), 2)
            max_idx = history["altitude"].index(max(history["altitude"]))
            history["apogee_time_s"] = round(history["time"][max_idx], 2)
            history["drift_m"] = round(history["x_position"][-1], 2)


        return history
