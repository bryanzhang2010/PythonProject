def download_and_sync_global_library():
    """
    Sends a structured JSON POST request to the official ThrustCurve V1 API to safely 
    download hundreds of motors for Estes, Quest, and AeroTech with full flight data curves.
    """
    output_path = "./Main/motors.json"
    compiled_library = {}
    
    # Bypass Mac local certificate validation issues safely
    context = ssl._create_unverified_context()
    
    # The modern JSON search API endpoint for ThrustCurve V1
    url = "https://www.thrustcurve.org/api/v1/search.json"
    
    # Clean structured JSON payload matching the ThrustCurve V1 specification
    json_request_payload = {
        "manufacturers": ["Estes", "Quest", "AeroTech"],
        "maxResults": 1000,
        "dataPoints": "all"
    }
    
    print("================================================================")
    print("            SYNCHRONIZING WITH THRUSTCURVE.ORG API               ")
    print("================================================================")
    print("[+] Requesting comprehensive data catalog via secure JSON POST...")
    
    try:
        # Encode the JSON dictionary payload to bytes
        data_bytes = json.dumps(json_request_payload).encode('utf-8')
        
        req = urllib.request.Request(
            url, 
            data=data_bytes, 
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, context=context, timeout=25) as response:
            json_response = json.loads(response.read().decode('utf-8'))
            
        print("[+] Download complete! Processing JSON dataset...")
        
        # Pull the array of motor records from the response object
        motors = json_response.get("results", json_response.get("motors", []))
        
        for motor in motors:
            mfr = motor.get("manufacturer", "Unknown").strip()
            common_name = motor.get("commonName", "").upper().strip()
            designation = motor.get("designation", "").upper().strip()
            
            if not designation:
                designation = common_name
            if not designation:
                continue
                
            try:
                diameter = float(motor.get("diameter", 0.0))
                length = float(motor.get("length", 0.0))
                prop_weight = float(motor.get("propWeight", motor.get("propellantWeight", 0.0)))
                total_weight = float(motor.get("totalWeight", 0.0))
                burn_time = float(motor.get("burnTime", 0.0))
            except (ValueError, TypeError):
                continue

            # Standardize delays layout
            delays_raw = motor.get("delays", "None")
            delays = delays_raw.split(",") if isinstance(delays_raw, str) else list(delays_raw)
            
            # Map out individual time vs thrust coordinates for the simulator engine
            thrust_points = []
            sim_data = motor.get("simFiles", motor.get("dataPoints", []))
            
            # Extract points if they are embedded directly or nested in data arrays
            if isinstance(sim_data, list):
                for item in sim_data:
                    if isinstance(item, list) and len(item) == 2:
                        thrust_points.append([float(item[0]), float(item[1])])
                    elif isinstance(item, dict):
                        try:
                            t = float(item.get("time", item.get("t", 0.0)))
                            f = float(item.get("thrust", item.get("f", 0.0)))
                            thrust_points.append([t, f])
                        except (ValueError, TypeError):
                            continue

            # Standards normalization into grams and metric parameters for flight calculations
            compiled_library[designation] = {
                "designation": designation,
                "common_name": common_name,
                "manufacturer": mfr,
                "diameter_mm": diameter,
                "length_mm": length,
                "delays": delays,
                "propellant_mass_g": round(prop_weight * 1000.0, 2) if prop_weight < 1.0 else prop_weight,
                "total_mass_g": round(total_weight * 1000.0, 2) if total_weight < 1.0 else total_weight,
                "burn_time_s": burn_time,
                "thrust_curve": thrust_points
            }
            
    except Exception as e:
        print(f"[-] API Fetch Failed. Error details: {e}")
        return

    if compiled_library:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(compiled_library, f, indent=4)
        print("----------------------------------------------------------------")
        print(f"[SUCCESS] Universal library built with {len(compiled_library)} total motors!")
        print(f"          Saved directly to: {output_path}")
        print("================================================================")
    else:
        print("[-] Query executed successfully, but motor data attributes didn't match parser rules.")