# Multi-Stage Flight Simulation Terminal

A responsive, Python-based desktop simulation application designed to model and graph 2D model rocket trajectories. The terminal features custom-engineered aerodynamic component selectors, interactive environmental wind profiles, and high-clearance, search-filtered dropdown mechanics for frictionless vehicle assembly.

---

## Key Features

* **Dynamic 2D Flight Trajectory Engine:** Simulates rocket flight kinematics from launch-rod release through motor burn, coast phase, apogee determination, and parachute descent.
* **Smart State Persistence:** Keeps all custom component selections, airframe selections, and environmental configurations perfectly intact when stepping back from the graph screen to the assembly bay.
* **Advanced Component Customization:** * Select from industry-standard motor profiles (e.g., Estes, Aerotech) and parse performance specifications.
  * Dynamically scale body tubes, nose cone profiles (Parabolic, Ogive, Conical), and fin geometries.
* **Frictionless UI Dropdowns:** Implements a custom, high-clearance grid menu with responsive hover highlighting, single-click item execution, and click-anywhere dismissal.
* **Interactive Wind Slider:** Includes a dual-input wind configuration bar (supporting high-precision slider snapping and automated text clearing upon typing selection).
* **Graph Animation:**  An animation on a 2-D plane showing the rockets height and drift in real time

---

##  UI & Interaction Design Highlights

* **Double-Click to Search:** Double-clicking any component dropdown fields instantly clears the text, forces cursor typing focus, and deploys a live-filtered canvas menu.
* **Click-to-Snap Slider:** Clicking anywhere on the horizontal wind scale track instantly warps the slider thumb to that precise value.
* **Click-to-Dismiss:** Tapping anywhere outside an open dropdown menu automatically collapses the active tray.
* **High-Accessibility Hitboxes:** Enhanced internal padding (`ipady=8`) across custom menu labels ensures buttons and selectors are prominent and effortless to click.

