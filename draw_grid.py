# draw_grid_hardcoded.py
# Draws a 3x3 grid (8 lines) with margin using Dobot Magician Lite via pydobot/pydobot2.
# Place the pen ABOVE the TOP-LEFT OUTER CORNER of the grid before running.

# --------- SETTINGS (edit these) ---------
PORT = "/dev/tty.usbmodem14101"   # e.g., "COM4" on Windows
SIDE_MM = 95.0                    # outer square side (mm), will be clamped to <= 100
PAD_MM  = 2.0                     # small inset margin (mm) to avoid edge blots
Y_DOWN_IS_NEGATIVE = True         # True: Y decreases when moving down (typical); False if Y increases down
Z_UP   = 20.0                     # safe height above paper (mm)
Z_DRAW = 0.5                      # drawing height (mm) — tune to your pen
VEL    = 60.0                     # mm/s
ACC    = 60.0                     # mm/s^2
# -----------------------------------------

# Prefer pydobot; else pydobot2
try:
    from pydobot import Dobot
except ImportError:
    from pydobot2 import Dobot

# --- pose/joint utilities ---
def get_pose_tuple(bot):
    if hasattr(bot, "pose"):
        p = bot.pose()
    elif hasattr(bot, "get_pose"):
        p = bot.get_pose()
    else:
        raise RuntimeError("No pose() method on Dobot object")
    if not p or len(p) < 4:
        raise RuntimeError("Pose not available")
    return p

def get_joints(bot, full_pose):
    for name in ("angles", "get_angles", "joint_angles", "get_joint_angles"):
        if hasattr(bot, name):
            try:
                a = getattr(bot, name)()
                if a and len(a) >= 4:
                    return tuple(a[:4])
            except Exception:
                pass
    if full_pose and len(full_pose) >= 8:
        return tuple(full_pose[4:8])
    return None

def print_pose_and_joints(bot, p):
    x, y, z, r = p[:4]
    print(f"Pose:   x={x:.2f}  y={y:.2f}  z={z:.2f}  r={r:.2f}")
    joints = get_joints(bot, p)
    if joints:
        j1, j2, j3, j4 = joints
        print(f"Joints: j1={j1:.2f}  j2={j2:.2f}  j3={j3:.2f}  j4={j4:.2f}")
    else:
        print("Joints: unavailable from API")

# --- motion helpers ---
def move_to(bot, x, y, z, r, wait=True):
    bot.move_to(x, y, z, r, wait=wait)

def pen_up(bot, r=None):
    x, y, z, r0, *_ = get_pose_tuple(bot)
    move_to(bot, x, y, Z_UP, r if r is not None else r0, wait=True)

def pen_down(bot, r=None):
    x, y, z, r0, *_ = get_pose_tuple(bot)
    move_to(bot, x, y, Z_DRAW, r if r is not None else r0, wait=True)

def line(bot, x1, y1, x2, y2, r=None):
    # Lift, go to start, draw to end, lift
    pen_up(bot, r=r)
    r_curr = get_pose_tuple(bot)[3] if r is None else r
    move_to(bot, x1, y1, Z_UP, r_curr, wait=True)
    pen_down(bot, r=r)
    move_to(bot, x2, y2, Z_DRAW, r_curr, wait=True)
    pen_up(bot, r=r)

# --- grid drawing (8 lines total) ---
def draw_grid(bot, top_left_xy, side_mm, pad_mm, y_down_is_negative=True):
    """
    Draws a 3x3 grid with outer box + 2 inner vertical + 2 inner horizontal lines.
    top_left_xy: (ox, oy) is the OUTER grid top-left corner in the robot's XY frame.
    """
    side = min(float(side_mm), 100.0)
    pad  = max(0.0, float(pad_mm))
    if pad * 2 >= side:
        raise ValueError("PAD_MM too large relative to SIDE_MM")

    ox, oy = top_left_xy
    sign = -1.0 if y_down_is_negative else +1.0  # controls 'down' direction

    # Inset bounds for nicer line ends
    x_left  = ox + pad
    x_right = ox + side - pad
    y_top   = oy + sign * pad
    y_bot   = oy + sign * (side - pad)

    cell = side / 3.0

    # Vertical lines at x = ox + i*cell (i=0..3)
    for i in range(4):
        xv = ox + i * cell
        line(bot, xv, y_top, xv, y_bot)

    # Horizontal lines at y = oy + sign*i*cell (i=0..3)
    for i in range(4):
        yh = oy + sign * (i * cell)
        line(bot, x_left, yh, x_right, yh)

def connect(port):
    bot = Dobot(port=port)
    try:
        bot.speed(VEL, ACC)
    except Exception:
        pass
    p = get_pose_tuple(bot)
    print(f"Connected to {port}")
    print_pose_and_joints(bot, p)
    return bot , p

def main():
    bot, p = connect(PORT)
    try:
        # Anchor: jog pen above TOP-LEFT outer corner before running
        x0, y0, z0, r0 = p[:4]
        top_left = (x0, y0)

        draw_grid(bot, top_left, SIDE_MM, PAD_MM, y_down_is_negative=Y_DOWN IS Y_DOWN_IS_NEGATIVE)

        pen_up(bot, r=r0)  # park safely
    finally:
        bot.close()

if __name__ == "__main__":
    main()
