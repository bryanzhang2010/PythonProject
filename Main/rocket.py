from parts import Thruster, NoseCone, BodyTube, FinSet, TrapezoidalFinSet, EllipticalFinSet, FreeformFinSet
import math

class Rocket:
    """
    The physical vehicle container. Acts as the assembly line and coordinator
    for global rocket physics (CP, CG, Mass, and Stability).
    """
    def __init__(self, name="Custom Rocket"):
        self.name = name
        self.components = []  # List of tuples: (component_object, axial_position_mm)

    def add_component(self, component, axial_position_mm):
        """
        Attaches a component onto the rocket body frame and validates its type.
        
        Parameters:
        component: An instance of a class from parts.py
        axial_position_mm (float): Distance from the tip of the nose cone (0 mm)
                                  to the front edge of this component.
        """
        # Strict validation using your imported classes
        valid_types = (Thruster, NoseCone, BodyTube, FinSet, TrapezoidalFinSet, EllipticalFinSet, FreeformFinSet)
        if not isinstance(component, valid_types):
            print(f"[Warning] Adding an unrecognized component type: {type(component).__name__}")
            
        self.components.append((component, float(axial_position_mm)))
        print(f"[Assembly] Attached '{component.name}' ({type(component).__name__}) at {axial_position_mm} mm from tip.")

    def get_reference_diameter(self):
        """
        Finds the maximum outer diameter specifically from BodyTube components
        to use as the reference diameter (1 Caliber) for stability calculations.
        """
        max_diameter = 0.0
        for comp, _ in self.components:
            # Explicitly look for BodyTube objects to define our main caliber
            if isinstance(comp, BodyTube):
                max_diameter = max(max_diameter, comp.outer_diameter)
        
        # Fallback security check if no BodyTube is attached yet
        if max_diameter == 0.0:
            for comp, _ in self.components:
                if hasattr(comp, 'outer_diameter'):
                    max_diameter = max(max_diameter, comp.outer_diameter)
                elif hasattr(comp, 'body_diameter'):
                    max_diameter = max(max_diameter, comp.body_diameter)
        
        return max_diameter if max_diameter > 0 else 1.0

    def calculate_cp(self):
        """
        Computes the global aerodynamic Center of Pressure (CP) using Barrowman's method.
        """
        total_c_n_alpha = 0.0
        weighted_x_cp_sum = 0.0

        for comp, attachment_pos in self.components:
            # 1. Specialized rule: Thrusters live inside the tube and do not 
            # contribute positive normal aerodynamic force in Barrowman equations.
            if isinstance(comp, Thruster):
                continue
            
            # 2. Extract lift properties from aerodynamic parts (NoseCone, FinSets)
            if hasattr(comp, 'calculate_aerodynamics'):
                local_data = comp.calculate_aerodynamics()
                c_n = local_data.get("C_N_alpha", 0.0)
                local_cp = local_data.get("X_cp_mm", 0.0)

                # Translate the part's internal CP to the rocket's global coordinate map
                absolute_cp = attachment_pos + local_cp

                if c_n > 0:
                    total_c_n_alpha += c_n
                    weighted_x_cp_sum += c_n * absolute_cp

        if total_c_n_alpha == 0:
            return None
            
        return weighted_x_cp_sum / total_c_n_alpha

    def calculate_cg(self):
        """
        Computes the global Center of Gravity (CG) and Total Mass of the vehicle.
        All parts (including Thrusters) contribute heavy physical mass.
        """
        total_mass = 0.0
        weighted_cg_sum = 0.0

        for comp, attachment_pos in self.components:
            mass = getattr(comp, 'mass_g', 0.0)
            local_cg = getattr(comp, 'cg_mm', 0.0)

            # Translate local center of mass to absolute coordinate
            absolute_cg = attachment_pos + local_cg

            total_mass += mass
            weighted_cg_sum += mass * absolute_cg

        if total_mass == 0:
            return 0.0, 0.0

        global_cg = weighted_cg_sum / total_mass
        return total_mass, global_cg

    def get_stability_status(self):
        """
        Evaluates the relationship between CP and CG to determine if the rocket
        will fly straight or crash.
        """
        global_cp = self.calculate_cp()
        total_mass, global_cg = self.calculate_cg()
        ref_diameter = self.get_reference_diameter()

        print(f"\n======== PHYSICS REPORT: {self.name.upper()} ========")
        print(f"Total Vehicle Mass   : {total_mass:.2f} g")
        print(f"Center of Gravity(CG): {global_cg:.2f} mm from tip" if global_cg > 0 else "Center of Gravity(CG): [Missing mass data]")
        print(f"Center of Pressure(CP): {global_cp:.2f} mm from tip" if global_cp is not None else "Center of Pressure(CP): [Unstable / No Lift]")

        if global_cp is not None and global_cg > 0:
            # Stability margin = (CP - CG) / Reference Diameter
            margin_mm = global_cp - global_cg
            margin_calibers = margin_mm / ref_diameter
            
            print(f"Reference Diameter   : {ref_diameter:.2f} mm (1 Caliber)")
            print(f"Static Margin        : {margin_calibers:.2f} calibers")
            print("-" * 43)

            if margin_calibers < 0:
                print("🚨 WARNING: UNSTABLE! Rocket will loop/tumble. CP is ahead of CG.")
            elif 0 <= margin_calibers < 1.0:
                print("⚠️ WARNING: MARGINALLY STABLE. Vulnerable to high winds.")
            elif 1.0 <= margin_calibers <= 2.5:
                print("✅ STATUS: STABLE AND FLIGHT READY! (Ideal 1-2.5 caliber margin).")
            else:
                print("ℹ️ STATUS: OVER-STABLE. Rocket might weathercock aggressively in wind.")
        print("===========================================\n")
        
        return {
            "mass_g": total_mass,
            "cg_mm": global_cg,
            "cp_mm": global_cp,
            "ref_dia_mm": ref_diameter
        }