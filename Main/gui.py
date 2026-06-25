import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from calculations import Rocket

class RocketGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AeroCompute: Rocket Configuration & Flight Simulation")
        self.root.geometry("1150x700")
        self.root.configure(bg="#1e1e1e")
        
        self.rocket = Rocket()
        
        # Default fin geometry attributes (in meters)
        self.custom_fin_data = {
            "num_fins": "4",
            "cr": "0.05",
            "ct": "0.02",
            "ss": "0.035",
            "sl": "0.015",
            "material": "Balsa Wood"
        }
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#1e1e1e", foreground="#ffffff")
        self.style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Arial", 11))
        self.style.configure("TButton", background="#3c3c3c", foreground="#ffffff", font=("Arial", 11, "bold"))
        self.style.configure("Launch.TButton", background="#00ff66", foreground="#000000", font=("Arial", 12, "bold"))
        self.style.configure("Gear.TButton", background="#3a3a3a", foreground="#00ff66", font=("Arial", 11, "bold"))
        
        self.style.configure("TEntry", foreground="#000000", fieldbackground="#ffffff")
        self.style.configure("TCombobox", foreground="#000000", fieldbackground="#ffffff")
        
        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        self.current_frame = None
        self.parse_catalog_assets()
        self.show_selection_screen()

    def parse_catalog_assets(self):
        self.motor_options = sorted(list(self.rocket.motor_database.keys())) if self.rocket.motor_database else ["C3.4T"]
        self.material_options = sorted(list(self.rocket.materials_db.keys())) if self.rocket.materials_db else ["Balsa Wood", "Cardboard", "Fiberglass"]
        
        self.nosecone_ids = []
        self.bodytube_ids = []
        
        target_catalog = self.rocket.catalog_db.get("Components", self.rocket.catalog_db)
        for category_name, category_items in target_catalog.items():
            cat_lower = str(category_name).lower()
            if isinstance(category_items, dict):
                for part_id in category_items.keys():
                    part_id_str = str(part_id)
                    part_id_lower = part_id_str.lower()
                    if "nose" in cat_lower or "nose" in part_id_lower:
                        self.nosecone_ids.append(part_id_str)
                    elif "tube" in cat_lower or "coupler" in cat_lower or "tube" in part_id_lower:
                        if "ring" not in part_id_lower:
                            self.bodytube_ids.append(part_id_str)

        self.nosecone_ids = sorted(self.nosecone_ids) if self.nosecone_ids else ["None"]
        self.bodytube_ids = sorted(self.bodytube_ids) if self.bodytube_ids else ["None"]

    def show_selection_screen(self):
        """SCREEN 1: Unified dashboard design containing dropdown selectors."""
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self.container, bg="#1e1e1e")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        self.main_layout_frame = tk.Frame(self.current_frame, bg="#1e1e1e")
        self.main_layout_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.card = tk.Frame(self.main_layout_frame, bg="#2d2d2d", padx=35, pady=35, relief=tk.RIDGE, borderwidth=1)
        self.card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=540, height=480)
        
        tk.Label(self.card, text="VEHICLE ASSEMBLY DASHBOARD", bg="#2d2d2d", fg="#00ff66", font=("Arial", 15, "bold")).pack(pady=(0, 20))
        
        # 1. Motor
        ttk.Label(self.card, text="Select Propulsion Motor:", background="#2d2d2d").pack(anchor=tk.W)
        self.motor_dropdown = ttk.Combobox(self.card, values=self.motor_options, state="readonly")
        self.motor_dropdown.pack(fill=tk.X, pady=(0, 15))
        self.motor_dropdown.current(0)
        self.motor_dropdown.bind("<<ComboboxSelected>>", self.close_dropdown_list)
        
        # 2. Nose Cone
        ttk.Label(self.card, text="Select Nose Cone Structure:", background="#2d2d2d").pack(anchor=tk.W)
        self.nose_dropdown = ttk.Combobox(self.card, values=self.nosecone_ids, state="readonly")
        self.nose_dropdown.pack(fill=tk.X, pady=(0, 15))
        self.nose_dropdown.current(0)
        self.nose_dropdown.bind("<<ComboboxSelected>>", self.close_dropdown_list)
        
        # 3. Body Tube
        ttk.Label(self.card, text="Select Airframe Body Tube:", background="#2d2d2d").pack(anchor=tk.W)
        self.tube_dropdown = ttk.Combobox(self.card, values=self.bodytube_ids, state="readonly")
        self.tube_dropdown.pack(fill=tk.X, pady=(0, 15))
        self.tube_dropdown.current(0)
        self.tube_dropdown.bind("<<ComboboxSelected>>", self.close_dropdown_list)
        
        # 4. Fins Setup (Matches layout of the other dropdown lines with an added side button)
        ttk.Label(self.card, text="Select Fin Set Assembly:", background="#2d2d2d").pack(anchor=tk.W)
        
        fin_row = tk.Frame(self.card, bg="#2d2d2d")
        fin_row.pack(fill=tk.X, pady=(0, 25))
        
        self.fin_dropdown = ttk.Combobox(fin_row, values=["Custom Fin Set"], state="readonly")
        self.fin_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.fin_dropdown.current(0)
        self.fin_dropdown.bind("<<ComboboxSelected>>", self.close_dropdown_list)
        
        # Compact side editing trigger button
        self.edit_fin_btn = ttk.Button(fin_row, text="⚙️ Edit Specs", style="Gear.TButton", command=self.open_fin_drawer, width=12)
        self.edit_fin_btn.pack(side=tk.RIGHT, padx=(8, 0))

        # Launch Button
        self.launch_btn = ttk.Button(self.card, text="🚀 ASSEMBLE & LAUNCH SIMULATION", style="Launch.TButton", command=self.process_launch_data)
        self.launch_btn.pack(fill=tk.X, ipady=6)
        
        self.drawer_frame = None

    def open_fin_drawer(self):
        """Slides open full-width drawer workspace to focus exclusively on fin modifications."""
        if self.drawer_frame is not None:
            return
            
        self.main_layout_frame.pack_forget()
        
        self.drawer_frame = tk.Frame(self.current_frame, bg="#252526", padx=30, pady=30)
        self.drawer_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        controls_panel = tk.Frame(self.drawer_frame, bg="#252526", width=380)
        controls_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        controls_panel.pack_propagate(False)
        
        tk.Label(controls_panel, text="FIN GEOMETRY MODELER", bg="#252526", fg="#00ff66", font=("Arial", 14, "bold")).pack(anchor=tk.W, pady=(0, 20))
        
        self.drawer_entries = {}
        fields = [
            ("Number of Fins:", self.custom_fin_data["num_fins"]),
            ("Root Chord (cr):", self.custom_fin_data["cr"]),
            ("Tip Chord (ct):", self.custom_fin_data["ct"]),
            ("Semi-Span (ss):", self.custom_fin_data["ss"]),
            ("Sweep Length (sl):", self.custom_fin_data["sl"])
        ]
        
        for label_text, last_val in fields:
            row_frame = tk.Frame(controls_panel, bg="#252526")
            row_frame.pack(fill=tk.X, pady=6)
            
            tk.Label(row_frame, text=label_text, bg="#252526", fg="#ffffff", font=("Arial", 10)).pack(side=tk.LEFT)
            
            entry = tk.Entry(row_frame, width=12, font=("Arial", 10), fg="#000000", bg="#ffffff", insertbackground="black")
            entry.insert(0, last_val)
            entry.pack(side=tk.RIGHT)
            
            entry.bind("<KeyRelease>", lambda event: self.update_fin_preview())
            self.drawer_entries[label_text] = entry
            
        mat_row = tk.Frame(controls_panel, bg="#252526")
        mat_row.pack(fill=tk.X, pady=(15, 25))
        tk.Label(mat_row, text="Fin Material Selection:", bg="#252526", fg="#ffffff", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 4))
        
        self.mat_dropdown = ttk.Combobox(mat_row, values=self.material_options, state="readonly", font=("Arial", 10))
        self.mat_dropdown.pack(fill=tk.X)
        try:
            idx = self.material_options.index(self.custom_fin_data["material"])
            self.mat_dropdown.current(idx)
        except ValueError:
            self.mat_dropdown.current(0)
            
        done_btn = ttk.Button(controls_panel, text="✅ DONE (SAVE MODEL)", command=self.close_fin_drawer)
        done_btn.pack(fill=tk.X, ipady=5)
        
        self.preview_panel = tk.Frame(self.drawer_frame, bg="#1e1e1e", relief=tk.SOLID, borderwidth=1)
        self.preview_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.preview_fig, self.preview_ax = plt.subplots(figsize=(4, 4), facecolor="#1e1e1e")
        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, master=self.preview_panel)
        self.preview_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_fin_preview()

    def update_fin_preview(self):
        try:
            num_fins = int(self.drawer_entries["Number of Fins:"].get())
            cr = float(self.drawer_entries["Root Chord (cr):"].get())
            ct = float(self.drawer_entries["Tip Chord (ct):"].get())
            ss = float(self.drawer_entries["Semi-Span (ss):"].get())
            sl = float(self.drawer_entries["Sweep Length (sl):"].get())
        except ValueError:
            return 
            
        self.preview_ax.clear()
        self.preview_ax.set_facecolor("#252526")
        self.preview_ax.tick_params(colors="#ffffff", labelsize=9)
        self.preview_ax.grid(True, color="#3c3c3c", linestyle="--")
        
        x_points = [0, cr, sl + ct, sl]
        y_points = [0, 0, ss, ss]
        x_closed = x_points + [0]
        y_closed = y_points + [0]
        
        self.preview_ax.fill(x_closed, y_closed, color="#00ff66", alpha=0.3)
        self.preview_ax.plot(x_closed, y_closed, color="#00ff66", linewidth=2.5)
        
        self.preview_ax.text(0.05, 0.92, f"Total Fin Set Count: {num_fins}", 
                             color="#ffffff", transform=self.preview_ax.transAxes, 
                             weight="bold", fontsize=10)
        
        self.preview_ax.set_title("Aerodynamic Blade Geometry Model", color="#ffffff", fontsize=11, pad=10)
        self.preview_ax.set_xlabel("Chord Length Axis (meters)", color="#ffffff", fontsize=9)
        self.preview_ax.set_ylabel("Span Height Axis (meters)", color="#ffffff", fontsize=9)
        
        max_dim = max(cr, sl + ct, ss) * 1.2
        self.preview_ax.set_xlim(-max_dim * 0.1, max_dim)
        self.preview_ax.set_ylim(-max_dim * 0.1, max_dim)
        self.preview_ax.set_aspect('equal', adjustable='box')
        
        self.preview_fig.tight_layout()
        self.preview_canvas.draw()

    def close_fin_drawer(self):
        if self.drawer_frame is None:
            return
            
        self.custom_fin_data["num_fins"] = self.drawer_entries["Number of Fins:"].get()
        self.custom_fin_data["cr"] = self.drawer_entries["Root Chord (cr):"].get()
        self.custom_fin_data["ct"] = self.drawer_entries["Tip Chord (ct):"].get()
        self.custom_fin_data["ss"] = self.drawer_entries["Semi-Span (ss):"].get()
        self.custom_fin_data["sl"] = self.drawer_entries["Sweep Length (sl):"].get()
        self.custom_fin_data["material"] = self.mat_dropdown.get()
        
        self.drawer_frame.destroy()
        self.drawer_frame = None
        
        self.main_layout_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def close_dropdown_list(self, event):
        self.card.focus_set()

    def process_launch_data(self):
        selected_motor = self.motor_dropdown.get()
        selected_nose = self.nose_dropdown.get()
        selected_tube = self.tube_dropdown.get()
        
        self.rocket = Rocket(designation=selected_motor)
        if selected_nose != "None": self.rocket.add_nose_cone(selected_nose)
        if selected_tube != "None": self.rocket.add_body_tube(selected_tube)
        
        try:
            num_fins = int(self.custom_fin_data["num_fins"])
            cr = float(self.custom_fin_data["cr"])
            ct = float(self.custom_fin_data["ct"])
            ss = float(self.custom_fin_data["ss"])
            sl = float(self.custom_fin_data["sl"])
            
            from parts import TrapezoidalFinSet
            configured_fins = TrapezoidalFinSet(
                count=num_fins, 
                body_diameter=0.024, 
                root_chord=cr, 
                tip_chord=ct, 
                semi_span=ss, 
                sweep_length=sl
            )
            self.rocket.set_fins(configured_fins)
        except ValueError:
            print("[-] Warning: Geometry parsing fault. Using baseline metrics.")
                
        results = self.rocket.simulate_trajectory(time_step=0.01, max_duration=6.0)
        self.show_graph_screen(selected_motor, results)

    def show_graph_screen(self, selected_motor, results):
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self.container, bg="#1e1e1e")
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        nav_bar = tk.Frame(self.current_frame, bg="#1e1e1e")
        nav_bar.pack(fill=tk.X, pady=(0, 10))
        
        back_btn = ttk.Button(nav_bar, text="⬅ BACK TO PARTS CONFIGURATION", command=self.show_selection_screen)
        back_btn.pack(side=tk.LEFT)
        
        fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#1e1e1e")
        ax.set_facecolor("#252526")
        ax.tick_params(colors="#ffffff")
        ax.grid(True, color="#3c3c3c", linestyle="--")
        ax.set_title(f"Flight Trajectory Profile: Engine [{selected_motor}]", color="#00ff66", fontsize=13, weight="bold", pad=15)
        ax.set_xlabel("Time (seconds)", color="#ffffff", labelpad=10)
        ax.set_ylabel("Altitude (meters)", color="#ffffff", labelpad=10)
        
        time_data = results["time"]
        altitude_data = results["altitude"]
        apogee_alt = results["apogee_m"]
        apogee_time = results["apogee_time_s"]
        
        if apogee_alt == 0.0:
            ax.text(0.5, 0.5, "⚠️ ENGINE THRUST INSUFFICIENT FOR LIFTOFF\n\nThe combined airframe weight exceeds liftoff parameters.",
                    color="#ff3333", fontsize=12, weight="bold", ha="center", va="center", transform=ax.transAxes)
            ax.set_xlim(-0.1, 1.0)
            ax.set_ylim(-1, 10)
        else:
            ax.plot(time_data, altitude_data, color="#00ff66", linewidth=2.5)
            ax.plot(apogee_time, apogee_alt, 'ro', markersize=6)
            ax.annotate(f" Apogee: {apogee_alt}m\n Time: {apogee_time}s", 
                        xy=(apogee_time, apogee_alt), color="#ffffff", weight="bold",
                        xytext=(15, -5), textcoords='offset points')
            ax.set_xlim(-0.2, max(time_data) * 1.2)
            ax.set_ylim(-2, max(altitude_data) * 1.2)
            
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.current_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

if __name__ == "__main__":
    window = tk.Tk()
    app = RocketGuiApp(window)
    window.mainloop()