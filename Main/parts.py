import math
import json
import os
from abc import ABC, abstractmethod

class Thruster:
    def __init__(self, designation, propellant_mass, total_mass, burn_time, thrust_curve):
        """
        Represents the rocket's propulsion engine component.
        """
        self.designation = str(designation).upper().strip()
        self.propellant_mass_g = float(propellant_mass)
        self.total_mass_g = float(total_mass)
        self.burn_time_s = float(burn_time)
        self.thrust_curve = thrust_curve if isinstance(thrust_curve, list) else []

    @classmethod
    def from_database(cls, designation, motors_db_path="./Main/motors.json"):
        """
        Factory method to initialize a Thruster directly from your parsed global JSON database.
        """
        desg_upper = str(designation).upper().strip()
        
        if not os.path.exists(motors_db_path):
            print(f"[-] Warning: Motor database file missing at {motors_db_path}. Using fallback defaults.")
            return cls(desg_upper, 20.0, 60.0, 1.5, [])

        with open(motors_db_path, 'r', encoding='utf-8') as f:
            database = json.load(f)
            
        profile = database.get(desg_upper)
        if profile and isinstance(profile, dict):
            return cls(
                designation=desg_upper,
                propellant_mass=profile.get("propellant_mass_g", 0.0),
                total_mass=profile.get("total_mass_g", 0.0),
                burn_time=profile.get("burn_time_s", 1.0),
                thrust_curve=profile.get("thrust_curve", [])
            )
        else:
            print(f"[-] Warning: '{desg_upper}' not found in database. Using fallback defaults.")
            return cls(desg_upper, 20.0, 60.0, 1.5, [])

    def getMass(self):
        """Returns the static liftoff total mass in grams (matching NoseCone/BodyTube style)."""
        return self.total_mass_g

    def getMassAtTime(self, current_time):
        """Calculates the dynamic mass in grams as propellant burns away."""
        if current_time <= 0:
            return self.total_mass_g
        if current_time >= self.burn_time_s:
            return self.total_mass_g - self.propellant_mass_g
            
        remaining_propellant = self.propellant_mass_g * (1.0 - (current_time / self.burn_time_s))
        empty_casing_mass = self.total_mass_g - self.propellant_mass_g
        return empty_casing_mass + remaining_propellant

    def getThrustAtTime(self, current_time):
        """Linearly interpolates your time vs force list points."""
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

    def getModel(self):
        return self.designation


class NoseCone:
    def __init__(self, name, material, height, radius, wall_thickness, density):
        self.name = name
        self.material = material
        self.height = height
        self.radius = radius
        self.wall_thickness = wall_thickness 
        
        slant_height = math.sqrt(self.radius**2 + self.height**2)
        surface_area = math.pi * self.radius * slant_height
        volume = surface_area * self.wall_thickness
        
        self.mass = density * volume

    @classmethod
    def from_catalog(cls, name, data, materials_db):
        """Safely parses cross-platform key variables from the catalog dict layout."""
        # Check both millimeter (Length) and inch (length) format indicators
        length_val = data.get('Length', data.get('length', 0))
        od_val = data.get('OutsideDiameter', data.get('outer_diameter', data.get('inner_diameter', 0)))
        thickness_val = data.get('WallThickness', data.get('wall_thickness', 1.0))
        mat_name = str(data.get('Material', data.get('material', 'cardboard'))).lower().strip()
        
        # Unit normalization safety valve (If numbers are small, they are likely in inches; convert to meters)
        is_inches = float(length_val) < 2.0 or float(od_val) < 2.0
        unit_scale = 0.0254 if is_inches else 0.001
        
        h = float(length_val) * unit_scale
        r = (float(od_val) * unit_scale) / 2.0
        t = float(thickness_val) * unit_scale
        
        density = materials_db.get(mat_name, 680.0)
        return cls(name, mat_name, h, r, t, density)

    def getMass(self):
        return self.mass


class BodyTube:
    def __init__(self, name, material, height, radius, wall_thickness, density):
        self.name = name
        self.material = material
        self.height = height 
        self.radius = radius 
        self.wall_thickness = wall_thickness 
        
        r_outer = self.radius
        r_inner = r_outer - self.wall_thickness
        volume = math.pi * (r_outer**2 - r_inner**2) * self.height
        self.mass = density * volume

    @classmethod
    def from_catalog(cls, name, data, materials_db):
        """Safely handles metric vs imperial structures coming from catalog files."""
        length_val = data.get('Length', data.get('length', 0))
        od_val = data.get('OutsideDiameter', data.get('outer_diameter', 0))
        thickness_val = data.get('WallThickness', data.get('wall_thickness', None))
        mat_name = str(data.get('Material', data.get('material', 'cardboard'))).lower().strip()
        
        is_inches = float(length_val) < 2.0 or float(od_val) < 2.0
        unit_scale = 0.0254 if is_inches else 0.001
        
        # If thickness is missing but we have inner diameter, calculate thickness instead
        if thickness_val is None and ('inner_diameter' in data or 'InsideDiameter' in data):
            id_val = data.get('inner_diameter', data.get('InsideDiameter', 0))
            t = (float(od_val) - float(id_val)) * unit_scale / 2.0
        else:
            t = float(thickness_val if thickness_val else 1.0) * unit_scale

        h = float(length_val) * unit_scale
        r = (float(od_val) * unit_scale) / 2.0
        
        density = materials_db.get(mat_name, 680.0)
        return cls(name, mat_name, h, r, t, density)

    def getMass(self):
        return self.mass


class FinSet(ABC):
    def __init__(self, count, body_diameter, name="Generic Fin Set"):
        self.name = name
        self.count = int(count)
        self.body_diameter = float(body_diameter)

    def calculate_interference_factor(self, semi_span):
        radius = self.body_diameter / 2.0
        return 1.0 + (radius / (radius + float(semi_span)))

    @abstractmethod
    def calculate_aerodynamics(self):
        pass


class TrapezoidalFinSet(FinSet):
    def __init__(self, count, body_diameter, root_chord, tip_chord, semi_span, sweep_length=0.0, name="Trapezoidal Fins"):
        super().__init__(count, body_diameter, name)
        self.root_chord = float(root_chord)
        self.tip_chord = float(tip_chord)
        self.semi_span = float(semi_span)
        self.sweep_length = float(sweep_length)

    def calculate_aerodynamics(self):
        delta_x_mid = self.sweep_length + (self.tip_chord / 2.0) - (self.root_chord / 2.0)
        l_m = math.sqrt((delta_x_mid ** 2) + (self.semi_span ** 2))
        
        span_ratio = self.semi_span / self.body_diameter
        numerator = 4.0 * self.count * (span_ratio ** 2)
        denominator = 1.0 + math.sqrt(1.0 + ((2.0 * l_m) / (self.root_chord + self.tip_chord)) ** 2)
        c_n_alpha = numerator / denominator
        
        c_n_alpha_corrected = c_n_alpha * self.calculate_interference_factor(self.semi_span)

        chord_sum = self.root_chord + self.tip_chord
        term_1 = (self.sweep_length * (self.root_chord + (2.0 * self.tip_chord))) / (3.0 * chord_sum)
        term_2 = (1.0 / 6.0) * (self.root_chord + self.tip_chord - ((self.root_chord * self.tip_chord) / chord_sum))
        x_cp = term_1 + term_2
        
        return {
            "C_N_alpha": round(c_n_alpha_corrected, 4),
            "X_cp_mm": round(x_cp, 2)
        }


class EllipticalFinSet(FinSet):
    def __init__(self, count, body_diameter, root_chord, semi_span, name="Elliptical Fins"):
        super().__init__(count, body_diameter, name)
        self.root_chord = float(root_chord)
        self.semi_span = float(semi_span)

    def calculate_aerodynamics(self):
        l_m = self.semi_span 
        span_ratio = self.semi_span / self.body_diameter
        numerator = 4.0 * self.count * (span_ratio ** 2)
        denominator = 1.0 + math.sqrt(1.0 + ((2.0 * l_m) / self.root_chord) ** 2)
        c_n_alpha = numerator / denominator
        
        c_n_alpha_corrected = c_n_alpha * self.calculate_interference_factor(self.semi_span)
        x_cp = 0.288 * self.root_chord
        
        return {
            "C_N_alpha": round(c_n_alpha_corrected, 4),
            "X_cp_mm": round(x_cp, 2)
        }


class FreeformFinSet(FinSet):
    def __init__(self, count, body_diameter, points, name="Freeform Fins"):
        super().__init__(count, body_diameter, name)
        self.points = [(float(p[0]), float(p[1])) for p in points]
        self.semi_span = max(p[1] for p in self.points)

    def _get_chord_boundaries(self, y):
        intersections = []
        n = len(self.points)
        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]
            if min(p1[1], p2[1]) <= y <= max(p1[1], p2[1]):
                if p1[1] != p2[1]:
                    x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                    intersections.append(x)
                    
        if len(intersections) >= 2:
            return min(intersections), max(intersections)
        elif len(intersections) == 1:
            return intersections[0], intersections[0]
        return None

    def calculate_aerodynamics(self, intervals=150):
        total_area = 0.0
        weighted_x_cp = 0.0
        mid_chord_points = []
        dy = self.semi_span / intervals
        
        for i in range(intervals):
            y_bottom = i * dy
            y_top = (i + 1) * dy
            
            bot_bounds = self._get_chord_boundaries(y_bottom)
            top_bounds = self._get_chord_boundaries(y_top)
            
            if not bot_bounds or not top_bounds:
                continue
                
            c_bottom = bot_bounds[1] - bot_bounds[0]
            c_top = top_bounds[1] - top_bounds[0]
            
            slice_area = 0.5 * (c_bottom + c_top) * dy
            total_area += slice_area
            
            x_mid_bot = (bot_bounds[1] + bot_bounds[0]) / 2.0
            x_mid_top = (top_bounds[1] + top_bounds[0]) / 2.0
            mid_chord_points.append((x_mid_bot, x_mid_top))
            
            slice_x_cp = (x_mid_bot + x_mid_top) / 2.0
            weighted_x_cp += slice_x_cp * slice_area

        if total_area == 0:
            return {"C_N_alpha": 0.0, "X_cp_mm": 0.0}

        l_m = 0.0
        for x_bot, x_top in mid_chord_points:
            l_m += math.sqrt((x_top - x_bot)**2 + dy**2)

        span_ratio = self.semi_span / self.body_diameter
        numerator = 4.0 * self.count * (span_ratio ** 2)
        denominator = 1.0 + math.sqrt(1.0 + ((l_m * self.semi_span) / total_area) ** 2)
        c_n_alpha = numerator / denominator
        
        c_n_alpha_corrected = c_n_alpha * self.calculate_interference_factor(self.semi_span)
        final_x_cp = weighted_x_cp / total_area
        
        return {
            "C_N_alpha": round(c_n_alpha_corrected, 4),
            "X_cp_mm": round(final_x_cp, 2),
            "Calculated_Area_mm2": round(total_area, 2)
        }