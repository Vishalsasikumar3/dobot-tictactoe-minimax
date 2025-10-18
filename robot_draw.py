# draw_symbols.py
import math
import argparse

# prefer pydobot, else pydobot2
try:
    from pydobot import Dobot
except ImportError:
    from pydobot2 import Dobot

HOME_X =""
HOME_Y = ""
HOME_Z = ""
HOME_R = ""

pen_z = ""

# ------- tune to your setup -------
CELL   = 35.0   # mm, cell side
MARGIN = 0.70   # 0..1, symbol size vs cell
Z_UP   = 20.0   # mm, safe height
Z_DRAW = 0.5    # mm, drawing height
VEL    = 60.0   # mm/s
ACC    = 60.0   # mm/s^2
R_TOOL = 0.0    # end-effector rotation
# ----------------------------------

def connect(port: str):
    bot = Dobot(port=port)
    try:
        bot.speed(VEL, ACC)
    except Exception:
        pass
    pose = bot.pose()
    print(f"Connected to {port}")
    if len(pose) >= 4:
        x, y, z, r = pose[:4]
        print(f"Pose:   x={x:.2f}  y={y:.2f}  z={z:.2f}  r={r:.2f}")
    if len(pose) >= 8:
        j1, j2, j3, j4 = pose[4:8]
        print(f"Joints: j1={j1:.2f}  j2={j2:.2f}  j3={j3:.2f}  j4={j4:.2f}")
    return bot

def get_pose(bot):
    x, y, z, r, *_ = bot.pose()
    return x, y, z, r

def move(bot, x, y, z=None, r=None, wait=True):
    _, _, zc, rc = get_pose(bot)
    bot.move_to(x, y, z if z is not None else zc, r if r is not None else rc, wait=wait)

def pen_up(bot):
    x, y, _, _ = get_pose(bot)
    bot.move_to(x, y, Z_UP, R_TOOL, wait=True)

def pen_down(bot):
    x, y, _, _ = get_pose(bot)
    bot.move_to(x, y, Z_DRAW, R_TOOL, wait=True)

def line(bot, x1, y1, x2, y2):
    pen_up(bot);  move(bot, x1, y1, Z_UP);  pen_down(bot)
    move(bot, x2, y2, Z_DRAW, wait=True)
    pen_up(bot)

def circle(bot, cx, cy, radius, segments=48):
    pts = [(cx + radius*math.cos(2*math.pi*i/segments),
            cy + radius*math.sin(2*math.pi*i/segments))
           for i in range(segments+1)]
    pen_up(bot); move(bot, pts[0][0], pts[0][1], Z_UP); pen_down(bot)
    for (x, y) in pts[1:]:
        move(bot, x, y, Z_DRAW, wait=False)
    pen_up(bot)

def cell_center(origin, idx: int):
    """idx: 0..8, left→right, top→bottom."""
    ox, oy = origin
    row, col = divmod(idx, 3)
    cx = ox + col * CELL
    cy = oy - row * CELL   # flip to + if your Y increases downward
    return cx, cy

def draw_x(bot, origin, idx: int):
    cx, cy = cell_center(origin, idx)
    d = 0.5 * CELL * MARGIN / math.sqrt(2)
    line(bot, cx - d, cy - d, cx + d, cy + d)
    line(bot, cx - d, cy + d, cx + d, cy - d)

def draw_o(bot, origin, idx: int):
    cx, cy = cell_center(origin, idx)
    r = 0.5 * CELL * MARGIN
    circle(bot, cx, cy, r)

def parse_moves(move_args):
    """e.g. ['X0','O4','X8'] -> [('X',0),('O',4),('X',8)]"""
    parsed = []
    for m in move_args:
        s = m.strip().upper()
        if not s or s[0] not in ('X', 'O'):
            continue
        sym = s[0]
        idx = int(s[1:])
        if 0 <= idx <= 8:
            parsed.append((sym, idx))
    return parsed

def main():
    port = ""
    bot = connect(port)
    try:
        # Calibration: jog pen over TOP-LEFT cell center at Z_UP before running
        x0, y0, _, _ = get_pose(bot)
        origin = (x0, y0)

        for sym, idx in parse_moves(args.moves):
            if sym == 'X':
                draw_x(bot, origin, idx)
            else:
                draw_o(bot, origin, idx)

        pen_up(bot)
    finally:
        bot.close()

if __name__ == "__main__":
    main()
