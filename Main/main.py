import os
import json
from rocket import Rocket
from parts import TrapezoidalFinSet, Thruster

def run_flight_simulation(rocket_instance, time_step=0.01, max_duration=5.0):
    """
    Simulates a 1D vertical flight trajectory to test how structural mass, 
    dynamic motor weight degradation, and thrust curve interpolation interact.
    """
    print("\n=========================================================")
    print(f"  LAUNCH SIMULATION RUNNER: ENGINE MODEL [{rocket_instance.designation}]")
    print("=========================================================")
    
    # Extract aerodynamic baseline calculated from your parts file
    aero_properties = rocket_instance.get_aerodynamics()
    print(f"[AERO] Barrowman C_N_alpha: {aero_properties.get('C_N_alpha', 0.0)}")
    print(f"[AERO] Center of Pressure (CP): {aero_properties.get('X_cp_mm', 0.0)} mm from root LE")
    print(f"[MASS] Initial Dry Airframe Weight: {rocket_instance.get_dry_airframe_mass_kg() * 1000.0:.2f}g")
    print("---------------------------------------------------------")

    # Kinematic Initial Flight Conditions
    current_time = 0.0
    altitude = 0.0
    velocity = 0.0
    g = 9.80665 # Standard Earth gravity acceleration (m/s^2)
    
    print(f"{'Time (s)':<10}{'Thrust (N)':<12}{'Mass (g)':<12}{'Accel (m/s²)':<15}{'Velocity (m/s)':<18}{'Altitude (m)':<12}")
    print("-" * 80)

    # Telemetry interval logging constraint
    sample_rate = 0.1  # Log updates to terminal every 100ms
    last_logged_time = -sample_rate

    # Run loop until rocket hits the ground or duration limit passes
    while current_time <= max_duration:
        # 1. Fetch live metrics from integrated parts layout
        thrust = rocket_instance.get_thrust_at_time(current_time)
        mass_kg = rocket_instance.get_total_mass_at_time(current_time)
        
        # 2. Physics Force Balance: F_net = Thrust - Weight (Ignoring drag for this baseline script verification)
        weight_force = mass_kg * g
        net_force = thrust - weight_force
        
        # 3. Kinematic Integration (Euler-Cromer Method)
        # If rocket is sitting cold on the launch pad with insufficient thrust, don't drop negative altitude
        if altitude <= 0.0 and net_force <= 0.0:
            acceleration = 0.0
            velocity = 0.0
            altitude = 0.0
        else:
            acceleration = net_force / mass_kg
            velocity += acceleration * time_step
            altitude += velocity * time_step

        # 4. Format telemetry lines at sampling intervals
        if current_time - last_logged_time >= (sample_rate - 1e-5):
            print(f"{current_time:<10.2f}{thrust:<12.3f}{mass_kg*1000:<12.1f}{acceleration:<15.2f}{velocity:<18.2f}{altitude:<12.2f}")
            last_logged_time = current_time

        # Break simulation cleanly if rocket hits apogee and returns to earth baseline
        if current_time > rocket_instance.burn_time_s and altitude <= 0.0 and velocity <= 0.0:
            break

        current_time += time_step

    print("=========================================================")
    print("SIMULATION EXHAUSTED: Rocket profile telemetry compiled successfully.")
    print("=========================================================\n")


if __name__ == "__main__":
    # Ensure your paths mirror your local repo structure
    # Instantiate a rocket configuration testing out the high-burn C3.4T motor
    test_rocket = Rocket(designation="C3.4T")
    
    # 1. Automatically parse structural tube and nose variables from master inventory
    test_rocket.attach_structure_from_catalog()
    
    # 2. Construct a real geometric fin planform configuration layout
    # Params: count, body_diameter, root_chord, tip_chord, semi_span, sweep_length
    test_fins = TrapezoidalFinSet(
        count=4, 
        body_diameter=0.024, # 24mm mounting step diameter alignment
        root_chord=0.050, 
        tip_chord=0.020, 
        semi_span=0.035, 
        sweep_length=0.015
    )
    
    # Bind the aerodynamics block to the active airframe engine
    test_rocket.set_fins(test_fins)
    
    # 3. Execute the flight solver routine
    run_flight_simulation(test_rocket, time_step=0.01, max_duration=4.0)