import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from animation import run_animation

from calculations import Rocket


class SearchableDropdown(tk.Frame):
    def __init__(self, parent, values, on_select_callback=None, **kwargs):
        super().__init__(parent, bg="#2d2d2d")
        self.all_values = values
        self.filtered_values = values
        self.current_selection = values[0] if values else ""
        self.on_select_callback = on_select_callback

        # 1. Main text field box - Larger internal padding (ipady=4) for a bigger hit box
        self.entry = tk.Entry(self, fg="#000000", bg="#e0e0e0", font=("Arial", 10), 
                              insertbackground="black", state="disabled")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        
        self.entry.config(state="normal")
        self.entry.insert(0, self.current_selection)
        self.entry.config(state="disabled")
        
        # 2. Dropdown Arrow Button - Wider hit box (ipadx=4) to make clicking easy
        self.btn = tk.Button(self, text=" ▼ ", font=("Arial", 9, "bold"), 
                             fg="#000000", bg="#00cc55", activebackground="#00aa44", activeforeground="#000000",
                             relief=tk.RAISED, bd=1, command=self.toggle_dropdown)
        self.btn.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0), ipadx=4)
        
        self.entry.bind("<Double-Button-1>", self.unlock_entry_field)
        self.entry.bind("<KeyRelease>", self.on_key_type)
        
        self.listbox_window = None
        self.listbox = None  # Tracks the active popup list element

        # Global listener: Closes the dropdown if a click happens anywhere else in the application window
        self.window_click_bind = self.winfo_toplevel().bind("<Button-1>", self.check_click_outside, add="+")

    def toggle_dropdown(self):
        """Opens or closes the dropdown menu tray popup."""
        if self.listbox_window and self.listbox_window.winfo_exists():
            self.close_dropdown()
        else:
            self.open_dropdown()

    def open_dropdown(self):
        """Spawns a highly responsive, easily clickable grid menu beneath the entry box."""
        if self.listbox_window:
            return

        # 1. Create a borderless floating popup window frame structure
        self.listbox_window = tk.Toplevel(self)
        self.listbox_window.wm_overrideredirect(True)
        
        # Position the window directly beneath our entry bar container
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.winfo_width()
        
        # Give it plenty of vertical room depending on your catalog size
        window_height = min(200, max(60, len(self.filtered_values) * 36))
        self.listbox_window.wm_geometry(f"{w}x{window_height}+{x}+{y}")
        
        # 2. Outer container box with scroll canvas
        container = tk.Frame(self.listbox_window, bg="#1e1e1e", bd=1, relief=tk.SOLID)
        container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(container, bg="#2d2d2d", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#2d2d2d")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=w-16)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        if len(self.filtered_values) > 5:
            scrollbar.pack(side="right", fill="y")

        # ========================================================================
        # MOUSE WHEEL SCROLLING INTEGRATION
        # ========================================================================
        def _on_mousewheel(event):
            """Diverts mousewheel scroll deltas directly into the layout canvas view viewport."""
            # Handles macOS trackpad scrolling vs Windows mousewheel triggers natively
            if event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")

        # Bind scroll triggers to the window tray complex
        self.listbox_window.bind("<MouseWheel>", _on_mousewheel)
        # Linux compatibility channels
        self.listbox_window.bind("<Button-4>", _on_mousewheel)
        self.listbox_window.bind("<Button-5>", _on_mousewheel)

        # 3. Build prominent, padded action blocks for every part choice
        def make_select_callback(value):
            return lambda event: self.execute_click_selection(value)

        for val in self.filtered_values:
            # Create a dedicated, distinct row frame for every item entry option
            item_row = tk.Label(scrollable_frame, text=f"  {val}", anchor="w",
                                bg="#2d2d2d", fg="#ffffff", font=("Arial", 10),
                                cursor="hand2")
            # SIGNIFICANTLY LARGER HITBOX: ipady=8 creates massive button fields
            item_row.pack(fill=tk.X, ipady=8, pady=1)

            # Bind tactile hover highlights to the labels
            item_row.bind("<Enter>", lambda e, w=item_row: w.config(bg="#00cc55", fg="#000000"))
            item_row.bind("<Leave>", lambda e, w=item_row: w.config(bg="#2d2d2d", fg="#ffffff"))
            
            # Direct instant single-click binding channel
            item_row.bind("<ButtonRelease-1>", make_select_callback(val))

    def execute_click_selection(self, selected_value):
        """Safely commits the chosen row item back into your application data streams."""
        self.current_selection = selected_value
        
        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.current_selection)
        self.entry.config(state="disabled")
        
        if self.on_select_callback:
            self.on_select_callback(self.current_selection)
        self.close_dropdown()

    def close_dropdown(self):
        """Safely tears down the active popup list window tray framework."""
        if self.listbox_window:
            self.listbox_window.destroy()
            self.listbox_window = None
            self.listbox = None

    def check_click_outside(self, event):
        """Monitors global click events to dismiss the dropdown list if clicking outside."""
        if self.listbox_window and self.listbox_window.winfo_exists():
            clicked_widget = event.widget
            
            # If the clicked element is part of this dropdown complex, do nothing and keep it open
            try:
                if clicked_widget in [self, self.btn, self.entry, self.listbox, self.listbox_window]:
                    return
            except AttributeError:
                pass
                
            # Otherwise, pull down the menu
            self.close_dropdown()

    def on_select_item(self, event):
        """Handles selecting an item from the list box popup."""
        if self.listbox:
            selection = self.listbox.curselection()
            if selection:
                self.current_selection = self.listbox.get(selection[0])
                
                self.entry.config(state="normal")
                self.entry.delete(0, tk.END)
                self.entry.insert(0, self.current_selection)
                self.entry.config(state="disabled")
                
                if self.on_select_callback:
                    self.on_select_callback(self.current_selection)
                self.close_dropdown()

    def unlock_entry_field(self, event):
        """Unlocks the text box for user search filtering on double click and forces typing focus."""
        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        
        # Clear out previous filtering state so it opens fresh
        self.filtered_values = self.all_values
        
        # FORCE TYPING FOCUS: Snaps the blinking cursor inside instantly
        self.entry.focus_set()
        
        # Display the padded selection options underneath
        self.open_dropdown()

    def on_key_type(self, event):
        """Filters available options based on typing input and rebuilds the custom list row components."""
        search_term = self.entry.get().lower()
        self.filtered_values = [v for v in self.all_values if search_term in v.lower()]
        
        if not self.listbox_window or not self.listbox_window.winfo_exists():
            # If the dropdown window isn't visible yet, deploy it
            self.open_dropdown()
        else:
            # Re-fetch references to our container widgets to wipe out outdated rows
            # Find the inner scrollable frame inside the active popup geometry
            try:
                # Traverse: Toplevel -> Frame -> Canvas -> Inner Scrollable Frame
                outer_frame = self.listbox_window.winfo_children()[0]
                canvas_widget = [w for w in outer_frame.winfo_children() if isinstance(w, tk.Canvas)][0]
                
                # To clear the old items safely, we find the frame inside the canvas window
                # Instead of destroying everything, let's just clear the canvas items and rebuild them cleanly:
                for child in outer_frame.winfo_children():
                    child.destroy()
                
                # Close and redeploy the dropdown window frame to cleanly repaint the new matches
                self.listbox_window.destroy()
                self.listbox_window = None
                self.open_dropdown()
            except Exception:
                # Ultimate fallback: if structural traversal slips, force reset the layout window cleanly
                if self.listbox_window:
                    self.listbox_window.destroy()
                self.listbox_window = None
                self.open_dropdown()

    def get(self):
        return self.current_selection

    def set(self, value):
        self.current_selection = value
        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.entry.config(state="disabled")


class RocketGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AeroCompute: Rocket Configuration & Flight Simulation")
        self.root.geometry("1150x700")
        self.root.configure(bg="#1e1e1e")
        
        self.rocket = Rocket()
        
        self.custom_fin_data = {
            "num_fins": "4",
            "cr": "0.05",
            "ct": "0.02",
            "ss": "0.035",
            "sl": "0.015",
            "material": "Balsa Wood"
        }

        self.saved_motor = None
        self.saved_nose = None
        self.saved_tube = None
        self.saved_wind = 0.00
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#1e1e1e", foreground="#ffffff")
        self.style.configure("TLabel", background="#1e1e1e", foreground="#ffffff", font=("Arial", 11))
        self.style.configure("TButton", background="#3c3c3c", foreground="#ffffff", font=("Arial", 11, "bold"))
        self.style.configure("Launch.TButton", background="#00ff66", foreground="#000000", font=("Arial", 12, "bold"))
        self.style.configure("Gear.TButton", background="#3a3a3a", foreground="#00ff66", font=("Arial", 11, "bold"))
        
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
        """SCREEN 1: Vehicle Assembly Terminal with live engine, nose, and body tube specs monitoring."""
        if self.current_frame:
            self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self.container, bg="#1e1e1e")
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        self.main_layout_frame = tk.Frame(self.current_frame, bg="#1e1e1e")
        self.main_layout_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Expanded height and width slightly to fit detailed structural parameters cleanly
        self.card = tk.Frame(self.main_layout_frame, bg="#2d2d2d", padx=35, pady=15, relief=tk.RIDGE, borderwidth=1)
        self.card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=620, height=660)
        
        tk.Label(self.card, text="VEHICLE ASSEMBLY DASHBOARD", bg="#2d2d2d", fg="#00ff66", font=("Arial", 14, "bold")).pack(pady=(0, 5))
        
        # ==================== 1. MOTOR PROPULSION SECTION ====================
        ttk.Label(self.card, text="Search & Select Propulsion Motor:", background="#2d2d2d").pack(anchor=tk.W)
        self.motor_dropdown = SearchableDropdown(self.card, values=self.motor_options, on_select_callback=self.update_live_motor_stats)
        self.motor_dropdown.pack(fill=tk.X, pady=(0, 2))
        
        self.stats_box = tk.LabelFrame(self.card, text=" Live Propulsion Specs ", bg="#2d2d2d", fg="#00ff66", 
                                       font=("Arial", 9, "bold"), padx=10, pady=4, relief=tk.GROOVE)
        self.stats_box.pack(fill=tk.X, pady=(0, 8))
        
        self.stat_labels = {}
        stat_titles = ["Total Impulse:", "Peak Thrust:", "Burn Duration:", "Total Mass:"]
        grid_frame = tk.Frame(self.stats_box, bg="#2d2d2d")
        grid_frame.pack(fill=tk.X)
        for i, title in enumerate(stat_titles):
            row, col = i // 2, (i % 2) * 2
            lbl = tk.Label(grid_frame, text=title, bg="#2d2d2d", fg="#aaaaaa", font=("Arial", 9, "bold"))
            lbl.grid(row=row, column=col, sticky=tk.W, padx=(15 if col > 0 else 0, 5), pady=1)
            val_lbl = tk.Label(grid_frame, text="--", bg="#2d2d2d", fg="#ffffff", font=("Arial", 9))
            val_lbl.grid(row=row, column=col+1, sticky=tk.W, pady=1)
            self.stat_labels[title] = val_lbl

        # ==================== 2. NOSE CONE AERODYNAMICS SECTION ====================
        ttk.Label(self.card, text="Search & Select Nose Cone Structure:", background="#2d2d2d").pack(anchor=tk.W)
        self.nose_dropdown = SearchableDropdown(self.card, values=self.nosecone_ids, on_select_callback=self.update_live_nose_stats)
        self.nose_dropdown.pack(fill=tk.X, pady=(0, 2))
        
        self.nose_stats_box = tk.LabelFrame(self.card, text=" Live Nose Cone Dimensions ", bg="#2d2d2d", fg="#00ff66", 
                                            font=("Arial", 9, "bold"), padx=10, pady=4, relief=tk.GROOVE)
        self.nose_stats_box.pack(fill=tk.X, pady=(0, 8))
        
        self.nose_stat_labels = {}
        nose_titles = ["Component Mass:", "Drag Coeff. (Cd):", "Inside Radius:", "Outside Radius:"]
        nose_grid_frame = tk.Frame(self.nose_stats_box, bg="#2d2d2d")
        nose_grid_frame.pack(fill=tk.X)
        for i, title in enumerate(nose_titles):
            row, col = i // 2, (i % 2) * 2
            lbl = tk.Label(nose_grid_frame, text=title, bg="#2d2d2d", fg="#aaaaaa", font=("Arial", 9, "bold"))
            lbl.grid(row=row, column=col, sticky=tk.W, padx=(15 if col > 0 else 0, 5), pady=1)
            val_lbl = tk.Label(nose_grid_frame, text="--", bg="#2d2d2d", fg="#ffffff", font=("Arial", 9))
            val_lbl.grid(row=row, column=col+1, sticky=tk.W, pady=1)
            self.nose_stat_labels[title] = val_lbl

        # ==================== 3. AIRFRAME BODY TUBE SECTION ====================
        ttk.Label(self.card, text="Search & Select Airframe Body Tube:", background="#2d2d2d").pack(anchor=tk.W)
        self.tube_dropdown = SearchableDropdown(self.card, values=self.bodytube_ids, on_select_callback=self.update_live_tube_stats)
        self.tube_dropdown.pack(fill=tk.X, pady=(0, 2))
        
        self.tube_stats_box = tk.LabelFrame(self.card, text=" Live Airframe Tube Dimensions ", bg="#2d2d2d", fg="#00ff66", 
                                            font=("Arial", 9, "bold"), padx=10, pady=4, relief=tk.GROOVE)
        self.tube_stats_box.pack(fill=tk.X, pady=(0, 8))
        
        self.tube_stat_labels = {}
        tube_titles = ["Tube Mass:", "Tube Length:", "Inside Radius:", "Outside Radius:"]
        tube_grid_frame = tk.Frame(self.tube_stats_box, bg="#2d2d2d")
        tube_grid_frame.pack(fill=tk.X)
        for i, title in enumerate(tube_titles):
            row, col = i // 2, (i % 2) * 2
            lbl = tk.Label(tube_grid_frame, text=title, bg="#2d2d2d", fg="#aaaaaa", font=("Arial", 9, "bold"))
            lbl.grid(row=row, column=col, sticky=tk.W, padx=(15 if col > 0 else 0, 5), pady=1)
            val_lbl = tk.Label(tube_grid_frame, text="--", bg="#2d2d2d", fg="#ffffff", font=("Arial", 9))
            val_lbl.grid(row=row, column=col+1, sticky=tk.W, pady=1)
            self.tube_stat_labels[title] = val_lbl

        # ==================== 4. FIN STABILIZER ROW SECTION ====================
        ttk.Label(self.card, text="Select Fin Set Assembly:", background="#2d2d2d").pack(anchor=tk.W)
        fin_row = tk.Frame(self.card, bg="#2d2d2d")
        fin_row.pack(fill=tk.X, pady=(0, 10))
        
        self.fin_display = tk.Entry(fin_row, font=("Arial", 10), fg="#888888", bg="#e0e0e0")
        self.fin_display.insert(0, f"Custom Fin Set ({self.custom_fin_data['num_fins']} Fins, {self.custom_fin_data['material']})")
        self.fin_display.config(state="disabled")
        self.fin_display.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.edit_fin_btn = ttk.Button(fin_row, text="⚙️ Edit Specs", style="Gear.TButton", command=self.open_fin_drawer, width=12)
        self.edit_fin_btn.pack(side=tk.RIGHT, padx=(8, 0))

        # ==================== 5. ENVIRONMENTAL CONFIGURATION ====================
        ttk.Label(self.card, text="Environmental Horizontal Wind Speed:", background="#2d2d2d").pack(anchor=tk.W)
        self.wind_frame = tk.Frame(self.card, bg="#2d2d2d")
        self.wind_frame.pack(fill=tk.X, pady=(0, 15))
        
        def sync_slider_to_entry(val):
            """Updates the entry box text when the slider moves."""
            try:
                if self.container.focus_get() != self.wind_entry:
                    self.wind_entry.delete(0, tk.END)
                    self.wind_entry.insert(0, f"{float(val):.2f}")
            except ValueError:
                pass

        def sync_entry_to_slider(event):
            """Parses user input on key release to dynamically reposition the slider thumb."""
            raw_input = self.wind_entry.get().strip()
            try:
                if raw_input:
                    val = float(raw_input)
                    if 0.0 <= val <= 25.0:
                        self.wind_slider.set(val)
            except ValueError:
                pass

        def clear_entry_placeholder(event):
            """Clears out the 0.00 value entirely when clicked so the user can start typing instantly."""
            try:
                if float(self.wind_entry.get()) == 0.0:
                    self.wind_entry.delete(0, tk.END)
            except ValueError:
                pass

        def restore_entry_placeholder(event):
            """Restores a clean 0.00 format if the user clicks away leaving it empty."""
            if not self.wind_entry.get().strip():
                self.wind_entry.insert(0, f"{self.wind_slider.get():.2f}")

        def snap_slider_to_click(event):
            """Forces the slider thumb to instantly warp to the absolute coordinates of a track click."""
            if event.widget == self.wind_slider:
                # Calculate relative horizontal position clicked on the widget track scale
                track_length = self.wind_slider.winfo_width()
                relative_x = event.x / track_length
                scale_range = self.wind_slider.cget("to") - self.wind_slider.cget("from")
                clicked_value = self.wind_slider.cget("from") + (relative_x * scale_range)
                
                # Snap values inside clean boundaries
                clicked_value = max(0.0, min(25.0, clicked_value))
                self.wind_slider.set(clicked_value)

        # 1. High-precision Slider with Click-To-Snap track binding
        self.wind_slider = tk.Scale(self.wind_frame, from_=0.0, to=25.0, resolution=0.01, orient=tk.HORIZONTAL,
                                    bg="#2d2d2d", fg="#ffffff", highlightthickness=0,
                                    troughcolor="#3c3c3c", activebackground="#00ff66", 
                                    showvalue=False, command=sync_slider_to_entry)
        
        # Restore saved wind speed state if it exists, otherwise default to zero
        self.wind_slider.set(self.saved_wind if self.saved_wind else 0.00)
        self.wind_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.wind_slider.bind("<Button-1>", snap_slider_to_click)  # Instantly moves thumb to mouse pointer position
        
        # 2. Digital Entry Input Box with Clear-On-Click focus utilities
        self.wind_entry = tk.Entry(self.wind_frame, width=7, font=("Arial", 10, "bold"), 
                                   bg="#e0e0e0", fg="#1e1e1e", justify=tk.CENTER, relief=tk.FLAT)
        self.wind_entry.insert(0, f"{self.wind_slider.get():.2f}")
        self.wind_entry.pack(side=tk.LEFT, padx=(0, 5), ipady=2)
        
        # Event utility chains
        self.wind_entry.bind("<KeyRelease>", sync_entry_to_slider)
        self.wind_entry.bind("<FocusIn>", clear_entry_placeholder)
        self.wind_entry.bind("<FocusOut>", restore_entry_placeholder)
        
        tk.Label(self.wind_frame, text="m/s", bg="#2d2d2d", fg="#aaaaaa", font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

        # ==================== 6. SIMULATION ACTION ====================
        self.launch_btn = ttk.Button(self.card, text="🚀 ASSEMBLE & LAUNCH SIMULATION", style="Launch.TButton", command=self.process_launch_data)
        self.launch_btn.pack(fill=tk.X, ipady=4)
        
        # Restore previous component choices from memory cache if returning from a run
        if self.saved_motor: self.motor_dropdown.set(self.saved_motor)
        if self.saved_nose: self.nose_dropdown.set(self.saved_nose)
        if self.saved_tube: self.tube_dropdown.set(self.saved_tube)
        
        # Pull initial display profiles down instantly on boot
        self.update_live_motor_stats(self.motor_dropdown.get())
        self.update_live_nose_stats(self.nose_dropdown.get())
        self.update_live_tube_stats(self.tube_dropdown.get())
        self.drawer_frame = None


    def update_live_nose_stats(self, nose_name):
        """Reads actual dimensions from master_catalog.json for the selected nose cone."""
        noses = self.rocket.catalog_db.get("Components", {}).get("NoseCone", {})
        part = noses.get(nose_name, None)

        if part is None or "none" in str(nose_name).lower() or nose_name == "":
            mass, cd, r_in, r_out = 0.0, 0.00, 0.0, 0.0
        else:
            # Mass: catalog stores oz, convert to grams (1 oz = 28.35 g)
            raw_mass = part.get("Mass", None)
            mass = float(raw_mass) * 28.35 if raw_mass else 0.0

            # Cd: approximate by shape
            shape = part.get("Shape", "").upper()
            cd_map = {"OGIVE": 0.10, "PARABOLIC": 0.11, "CONICAL": 0.20,
                    "ELLIPSOID": 0.12, "POWER": 0.13}
            cd = cd_map.get(shape, 0.15)

            # Radii: catalog stores inches OD/shoulder, convert to mm
            od_in = float(part.get("OutsideDiameter", 0))
            shoulder_in = float(part.get("ShoulderDiameter", od_in * 0.95))
            r_out = (od_in / 2) * 25.4
            r_in  = (shoulder_in / 2) * 25.4

        self.nose_stat_labels["Component Mass:"].config(text=f"{mass:.1f} g")
        self.nose_stat_labels["Drag Coeff. (Cd):"].config(text=f"{cd:.2f}")
        self.nose_stat_labels["Inside Radius:"].config(text=f"{r_in:.1f} mm")
        self.nose_stat_labels["Outside Radius:"].config(text=f"{r_out:.1f} mm")


    def update_live_tube_stats(self, tube_name):
        """Reads actual dimensions from master_catalog.json for the selected body tube."""
        tubes = self.rocket.catalog_db.get("Components", {}).get("BodyTube", {})
        part = tubes.get(tube_name, None)

        if part is None or "none" in str(tube_name).lower() or tube_name == "":
            mass, length, r_in, r_out = 0.0, 0.0, 0.0, 0.0
        else:
            # Dimensions: catalog stores inches, convert to mm
            od_in  = float(part.get("OutsideDiameter", 0))
            id_in  = float(part.get("InsideDiameter", 0))
            len_in = float(part.get("Length", 0))

            r_out  = (od_in / 2) * 25.4
            r_in   = (id_in / 2) * 25.4
            length = len_in * 2.54  # inches to cm

            # Mass: estimate from material density * wall volume
            material_key = part.get("Material", "").lower()
            density = self.rocket.materials_db.get(material_key, 800.0)  # kg/m3

            wall_thickness_m = (od_in - id_in) / 2 * 0.0254
            id_m  = id_in * 0.0254
            len_m = len_in * 0.0254
            import math
            volume_m3 = math.pi * ((id_m/2 + wall_thickness_m)**2 - (id_m/2)**2) * len_m
            mass = density * volume_m3 * 1000  # grams

        self.tube_stat_labels["Tube Mass:"].config(text=f"{mass:.1f} g")
        self.tube_stat_labels["Tube Length:"].config(text=f"{length:.1f} cm")
        self.tube_stat_labels["Inside Radius:"].config(text=f"{r_in:.1f} mm")
        self.tube_stat_labels["Outside Radius:"].config(text=f"{r_out:.1f} mm")




    def update_live_motor_stats(self, motor_name):
        """Calculates and displays engine performance metrics directly from the raw thrust curve."""
        motor_profile = self.rocket.motor_database.get(motor_name, None)
        
        if motor_profile and isinstance(motor_profile, dict):
            thrust_curve = motor_profile.get("thrust_curve", [])
            
            # 1. Calculate Peak Thrust (maximum Y-value in the curve)
            if thrust_curve:
                peak_thrust = max(point[1] for point in thrust_curve)
            else:
                peak_thrust = 0.0
                
            # 2. Calculate Total Impulse (Area under the thrust-time curve using Trapezoidal Rule)
            total_impulse = 0.0
            if thrust_curve and len(thrust_curve) > 1:
                for i in range(len(thrust_curve) - 1):
                    t0, f0 = thrust_curve[i]
                    t1, f1 = thrust_curve[i+1]
                    # Area of trapezoid: (width) * (average height)
                    dt = t1 - t0
                    avg_force = (f0 + f1) / 2.0
                    total_impulse += dt * avg_force
            
            # 3. Extract Burn Duration and Total Mass safely
            burn_time = float(motor_profile.get("burn_time_s", 0.0))
            total_mass = float(motor_profile.get("total_mass_g", 0.0))
            
            # Update display labels dynamically
            self.stat_labels["Total Impulse:"].config(text=f"{total_impulse:.2f} N·s")
            self.stat_labels["Peak Thrust:"].config(text=f"{peak_thrust:.1f} N")
            self.stat_labels["Burn Duration:"].config(text=f"{burn_time:.2f} s")
            self.stat_labels["Total Mass:"].config(text=f"{total_mass:.1f} g")
        else:
            for title in self.stat_labels:
                self.stat_labels[title].config(text="Unknown")

    def open_fin_drawer(self):
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
        
        self.fin_display.config(state="normal")
        self.fin_display.delete(0, tk.END)
        self.fin_display.insert(0, f"Custom Fin Set ({self.custom_fin_data['num_fins']} Fins, {self.custom_fin_data['material']})")
        self.fin_display.config(state="disabled")

    def process_launch_data(self):
        """Processes selection states, reads structural dimensions, and calls the 2D trajectory simulation."""
        self.saved_motor = self.motor_dropdown.get()
        self.saved_nose = self.nose_dropdown.get()
        self.saved_tube = self.tube_dropdown.get()
        self.saved_wind = float(self.wind_slider.get())

        selected_motor = self.motor_dropdown.get()
        selected_nose = self.nose_dropdown.get()
        selected_tube = self.tube_dropdown.get()
        current_wind = float(self.wind_slider.get())  # Read wind input from slider
        
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
                count=num_fins, body_diameter=0.024, 
                root_chord=cr, tip_chord=ct, semi_span=ss, sweep_length=sl
            )
            self.rocket.set_fins(configured_fins)
        except ValueError:
            print("[-] Warning: Configuration reading fault. Reverting to basic metrics.")
                
        # Run flight simulation passing the wind vector parameter
        results = self.rocket.simulate_trajectory(time_step=0.01, max_duration=12.0, wind_speed=current_wind)
        self.show_graph_screen(selected_motor, results)


    def show_graph_screen(self, selected_motor, results):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = tk.Frame(self.container, bg="#1e1e1e")
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        nav_bar = tk.Frame(self.current_frame, bg="#1e1e1e")
        nav_bar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(nav_bar, text="⬅ BACK",
                command=self.show_selection_screen).pack(side=tk.LEFT)

        # Build the matplotlib figure once — shared by both views
        fig, ax = plt.subplots(figsize=(7, 4.5), facecolor="#1e1e1e")
        canvas = FigureCanvasTkAgg(fig, master=self.current_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Store anim reference so garbage collector doesn't kill it
        self._anim = None

        def draw_static():
            ax.clear()
            ax.set_facecolor("#252526")
            ax.tick_params(colors="#ffffff")
            ax.grid(True, color="#3c3c3c", linestyle="--")
            ax.set_title(f"2D Flight Profile: [{selected_motor}]",
                        color="#00ff66", fontsize=13, weight="bold", pad=15)
            ax.set_xlabel("Horizontal Downrange Drift (m)",
                        color="#ffffff", labelpad=10)
            ax.set_ylabel("Altitude (m)", color="#ffffff", labelpad=10)

            x_data = results["x_position"]
            y_data = results["altitude"]
            apogee_alt = results["apogee_m"]
            drift = results["drift_m"]

            if apogee_alt == 0.0:
                ax.text(0.5, 0.5,
                        "⚠️ THRUST INSUFFICIENT FOR LIFTOFF",
                        color="#ff3333", fontsize=12, weight="bold",
                        ha="center", va="center", transform=ax.transAxes)
            else:
                ax.plot(x_data, y_data, color="#00ff66",
                        linewidth=2.5, label="Trajectory")
                max_y_idx = y_data.index(max(y_data))
                ax.plot(x_data[max_y_idx], apogee_alt,
                        'ro', markersize=6)
                ax.annotate(
                    f" Apogee: {apogee_alt}m\n T: {results['apogee_time_s']}s",
                    xy=(x_data[max_y_idx], apogee_alt),
                    color="#ffffff", weight="bold",
                    xytext=(10, -5), textcoords="offset points"
                )
                ax.plot(drift, 0.0, 'bx', markersize=8, markeredgewidth=2)
                ax.text(drift, apogee_alt * 0.05,
                        f" Landing:\n {drift}m", color="#66ccff", weight="bold")
                ax.set_ylim(-2, apogee_alt * 1.2)

            fig.tight_layout()
            canvas.draw()

        def play_animation():
            from animation import run_animation
            self._anim = run_animation(
                results, selected_motor, ax=ax, canvas=canvas
            )

        # Buttons
        ttk.Button(nav_bar, text="📊 STATIC GRAPH",
                command=draw_static).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(nav_bar, text="▶ PLAY ANIMATION",
                command=play_animation).pack(side=tk.LEFT, padx=(8, 0))

        # Start with static graph
        draw_static()




if __name__ == "__main__":
    window = tk.Tk()
    app = RocketGuiApp(window)
    window.mainloop()