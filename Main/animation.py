import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np

def run_animation(results, motor_name="", ax=None, canvas=None):
    """
    Runs the flight animation inside an existing ax/canvas if provided,
    or opens a standalone window if called directly.
    """
    x_data = results["x_position"]
    y_data = results["altitude"]
    apogee_time = results["apogee_time_s"]
    time_data = results["time"]
    apogee_m = results["apogee_m"]

    # Find parachute deploy index
    chute_idx = 0
    for i, t in enumerate(time_data):
        if t >= apogee_time:
            chute_idx = i
            break

    # --- Use existing ax or create new figure ---
    standalone = (ax is None)
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 6), facecolor="#1e1e1e")
        canvas = None

    ax.clear()
    ax.set_facecolor("#252526")
    ax.tick_params(colors="#ffffff")
    ax.grid(True, color="#3c3c3c", linestyle="--")
    ax.set_title(f"Flight Animation: [{motor_name}]",
                 color="#00ff66", fontsize=13, weight="bold")
    ax.set_xlabel("Horizontal Drift (m)", color="#ffffff")
    ax.set_ylabel("Altitude (m)", color="#ffffff")

    x_pad = max(abs(min(x_data)), abs(max(x_data))) * 0.2 + 1
    y_pad = apogee_m * 0.15 + 1
    ax.set_xlim(min(x_data) - x_pad, max(x_data) + x_pad)
    ax.set_ylim(-2, apogee_m + y_pad)

    # Faint path in background
    ax.plot(x_data, y_data, color="#00ff66", linewidth=1,
            alpha=0.15, linestyle="--")

    # Scale marker sizes to apogee height
    rocket_size = max(apogee_m * 0.012, 0.5)

    # --- Animated elements ---
    # Rocket: just a white dot
    rocket_dot, = ax.plot([], [], 'o', color="#ffffff",
                          markersize=8, zorder=5, label="Rocket")

    # Flame: orange dot below rocket, visible during burn
    flame_dot, = ax.plot([], [], 'o', color="#ff4400",
                         markersize=5, zorder=4)

    # Parachute: two lines forming an arc (simple inverted V)
    chute_left, = ax.plot([], [], color="#ff6600",
                          linewidth=2.5, zorder=4)
    chute_right, = ax.plot([], [], color="#ff6600",
                           linewidth=2.5, zorder=4)
    chute_lines, = ax.plot([], [], color="#ffaa66",
                           linewidth=1, zorder=4)

    # Trail
    trail_line, = ax.plot([], [], color="#00ff66",
                          linewidth=2, alpha=0.8)

    # Info box
    info_text = ax.text(
        0.02, 0.95, "", transform=ax.transAxes,
        color="#ffffff", fontsize=10, verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="#1e1e1e", alpha=0.7)
    )

    chute_deployed = [False]

    SKIP = max(1, len(x_data) // 300)
    frame_indices = list(range(0, len(x_data), SKIP))

    def update(frame_num):
        i = frame_indices[frame_num]
        x = x_data[i]
        y = y_data[i]
        t = time_data[i]

        # Rocket dot
        rocket_dot.set_data([x], [y])

        # Trail
        trail_line.set_data(x_data[:i], y_data[:i])

        # Flame: visible while thrust is producing (before apogee, roughly first half)
        burn_end = apogee_time * 0.55
        if t < burn_end:
            flame_dot.set_data([x], [y - rocket_size])
            flame_dot.set_alpha(1.0)
        else:
            flame_dot.set_data([], [])

        # Parachute deploy at apogee
        if i >= chute_idx:
            chute_deployed[0] = True

        if chute_deployed[0]:
            # Draw simple inverted-V parachute above rocket
            s = rocket_size * 2.5
            chute_left.set_data([x, x - s], [y + s * 0.3, y + s])
            chute_right.set_data([x, x + s], [y + s * 0.3, y + s])
            # Suspension lines from rocket to chute edges
            chute_lines.set_data([x - s, x, x + s],
                                 [y + s, y, y + s])
        else:
            chute_left.set_data([], [])
            chute_right.set_data([], [])
            chute_lines.set_data([], [])

        # Status text
        status = "🪂 CHUTE DEPLOYED" if chute_deployed[0] else "🚀 ASCENDING"
        info_text.set_text(
            f"T+{t:.2f}s\n"
            f"Alt: {y:.1f} m\n"
            f"Drift: {x:.1f} m\n"
            f"{status}"
        )

        # Redraw into existing canvas if embedded
        if canvas:
            canvas.draw()

        return (rocket_dot, flame_dot, chute_left, chute_right,
                chute_lines, trail_line, info_text)

    fig_to_use = ax.get_figure()
    anim = FuncAnimation(
        fig_to_use,
        update,
        frames=len(frame_indices),
        interval=20,
        blit=False,
        repeat=False
    )

    if standalone:
        plt.tight_layout()
        plt.show()

    return anim


