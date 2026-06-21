import os
import json
import urllib.request
import ssl
import gzip
import sqlite3

def parse_local_eng_file(file_path):
    """
    Parses a single local RASP (.eng) text file if you ever manually drop one in.
    """
    if not os.path.exists(file_path):
        print(f"[-] Error: Engine file not found at {file_path}")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    return parse_raw_eng_text(raw_text)

def parse_raw_eng_text(raw_text):
    """
    Parses raw RASP text strings line-by-line.
    """
    engines_found = {}
    lines = raw_text.strip().split('\n')
    
    current_motor = None
    header_parsed = False
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        
        if not header_parsed:
            parts = line.split()
            if len(parts) >= 7:
                designation = parts[0].upper()
                current_motor = {
                    "designation": designation,
                    "manufacturer": parts[6],
                    "diameter_mm": float(parts[1]),
                    "length_mm": float(parts[2]),
                    "delays": parts[3].split('-'),
                    "propellant_mass_g": round(float(parts[4]) * 1000.0, 2),
                    "total_mass_g": round(float(parts[5]) * 1000.0, 2),
                    "thrust_curve": []
                }
                header_parsed = True
                engines_found[designation] = current_motor
            continue
        
        try:
            parts = line.split()
            if len(parts) >= 2:
                time_s = float(parts[0])
                thrust_n = float(parts[1])
                current_motor["thrust_curve"].append([time_s, thrust_n])
                if thrust_n == 0.0:
                    header_parsed = False 
        except (ValueError, TypeError):
            continue
            
    return engines_found

def download_and_sync_global_library():
    """
    Downloads OpenRocket's production database archive directly, decompresses it,
    and extracts all relational specifications and active thrust curves using text-matching fallbacks.
    """
    output_path = "./Main/motors.json"
    temp_db_path = "./Main/temp_motors.db"
    compiled_library = {}
    
    # Safely bypass local Mac SSL handshake validation rules
    context = ssl._create_unverified_context()
    
    # Official OpenRocket cloud production asset database archive URL
    url = "https://openrocket.github.io/motor-database/motors.db.gz"
    
    print("================================================================")
    print("          EXTRACTING MASTER OPENROCKET ENGINE DATABASE         ")
    print("================================================================")
    print("[+] Streaming compressed data archive from OpenRocket server CDN...")
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download the compressed binary archive stream
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context, timeout=20) as response:
            compressed_data = response.read()
            
        print("[+] Unpacking and decompressing archive bundle...")
        decompressed_db = gzip.decompress(compressed_data)
        
        # Save out the temporary SQLite file
        with open(temp_db_path, "wb") as f:
            f.write(decompressed_db)
            
        print("[+] Processing engine data structures...")
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Determine column names dynamically
        cursor.execute("PRAGMA table_info(motors);")
        motor_cols = [c[1] for c in cursor.fetchall()]
        
        mfr_col = "manufacturer" if "manufacturer" in motor_cols else "manufacturer_id"
        prop_col = "propellant_weight" if "propellant_weight" in motor_cols else "propellant_mass" if "propellant_mass" in motor_cols else "prop_weight"
        tot_col = "total_weight" if "total_weight" in motor_cols else "total_mass"
        burn_col = "burn_time" if "burn_time" in motor_cols else "burn_duration"

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        has_mfr_table = "manufacturers" in tables

        # Extract every motor record from the database core
        motor_query = f"SELECT id, designation, common_name, diameter, length, {prop_col}, {tot_col}, {burn_col}, {mfr_col} FROM motors"
        cursor.execute(motor_query)
        motor_rows = cursor.fetchall()
        
        mfr_map = {}
        if has_mfr_table:
            try:
                cursor.execute("SELECT id, name FROM manufacturers")
                mfr_map = {row[0]: row[1] for row in cursor.fetchall()}
            except:
                pass

        print("[+] Mapping localized time vs. force thrust curves...")
        
        cursor.execute("PRAGMA table_info(thrust_data);")
        td_cols = [c[1] for c in cursor.fetchall()]
        time_col = "time" if "time" in td_cols else "time_seconds" if "time_seconds" in td_cols else td_cols[1]
        force_col = "thrust" if "thrust" in td_cols else "force" if "force" in td_cols else td_cols[2]

        for row in motor_rows:
            motor_id, designation, common_name, diameter, length, prop_w, total_w, burn_time, mfr_raw = row
            
            desg = str(designation).upper().strip()
            cname = str(common_name).upper().strip() if common_name else desg
            
            # Resolve manufacturer string
            mfr_name = mfr_map.get(mfr_raw, str(mfr_raw)) if has_mfr_table else str(mfr_raw)
            mfr_clean = mfr_name.strip()
            
            # Fallback Manufacturer Logic for ambiguous markers
            if mfr_clean in ["Global Database", "Unknown", "", "None"] or mfr_clean.isdigit():
                # AeroTech uses code letters like 'J', 'W', 'R', 'NT' at the end of their designator strings
                if desg.endswith('J') or desg.endswith('W') or desg.endswith('R') or desg.endswith('NT') or "AEROTECH" in cname:
                    mfr_clean = "AeroTech"
                elif desg.startswith('Q') or "QUEST" in cname:
                    mfr_clean = "Quest"
                else:
                    mfr_clean = "Estes"

            # Filter for specific simulation options
            if not any(brand in mfr_clean for brand in ["Estes", "Quest", "AeroTech"]):
                continue
                
            if "Estes" in mfr_clean:
                mfr_clean = "Estes"

            thrust_points = []
            try:
                # Primary Query Strategy: Standard Relational Mapping
                cursor.execute("SELECT id FROM thrust_curves WHERE motor_id = ? LIMIT 1;", (motor_id,))
                curve_id_row = cursor.fetchone()
                
                if curve_id_row:
                    curve_id = curve_id_row[0]
                    cursor.execute(f"SELECT {time_col}, {force_col} FROM thrust_data WHERE thrust_curve_id = ? ORDER BY {time_col} ASC;", (curve_id,))
                    thrust_points = [[round(float(pt[0]), 4), round(float(pt[1]), 3)] for pt in cursor.fetchall()]
                
                # Backup Fallback Strategy: If relational links are missing, search thrust curves via designation tags text matching
                if not thrust_points:
                    cursor.execute("SELECT id FROM thrust_curves WHERE UPPER(designation) = ? OR UPPER(common_name) = ? LIMIT 1;", (desg, cname))
                    fallback_curve_row = cursor.fetchone()
                    if fallback_curve_row:
                        cursor.execute(f"SELECT {time_col}, {force_col} FROM thrust_data WHERE thrust_curve_id = ? ORDER BY {time_col} ASC;", (fallback_curve_row[0],))
                        thrust_points = [[round(float(pt[0]), 4), round(float(pt[1]), 3)] for pt in cursor.fetchall()]
                        
            except Exception:
                pass

            # Standardize mass values cleanly into grams
            p_mass = round(float(prop_w or 0.0) * 1000.0, 2) if float(prop_w or 0.0) < 5.0 else round(float(prop_w or 0.0), 2)
            t_mass = round(float(total_w or 0.0) * 1000.0, 2) if float(total_w or 0.0) < 5.0 else round(float(total_w or 0.0), 2)

            compiled_library[desg] = {
                "designation": desg,
                "common_name": cname,
                "manufacturer": mfr_clean,
                "diameter_mm": round(float(diameter or 0.0), 1),
                "length_mm": round(float(length or 0.0), 1),
                "delays": ["Variable"],
                "propellant_mass_g": p_mass,
                "total_mass_g": t_mass,
                "burn_time_s": round(float(burn_time or 0.0), 2),
                "thrust_curve": thrust_points
            }

        conn.close()
        
    except Exception as e:
        print(f"[-] Database Synchronization Failed. Error details: {e}")
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        return

    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)

    if compiled_library:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(compiled_library, f, indent=4)
        print("----------------------------------------------------------------")
        print(f"[SUCCESS] Universal library built with {len(compiled_library)} total motors!")
        print(f"          Saved directly to: {output_path}")
        print("================================================================")