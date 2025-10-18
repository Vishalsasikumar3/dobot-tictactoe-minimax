# main_tictactoe.py
# Orchestrates Tic-Tac-Toe with Dobot Magician Lite.
# - Draws grid using grid_module
# - Prompts human for symbol choice and who starts
# - Robot plays using minimax; human enters (i,j) and draws manually

# ---------------- Configuration ----------------
PORT = None                  # None => auto-detect; or set "COM4" / "/dev/tty.usbmodemXXXX"
SIDE_MM = 95.0               # outer grid side (<= 100 mm)
PAD_MM  = 2.0                # small inset margin for line starts/ends
Y_DOWN_IS_NEGATIVE = True    # True if Y decreases going “down” the page (typical Dobot)
Z_UP   = 20.0                # mm
Z_DRAW = 0.5                 # mm
VEL    = 60.0                # mm/s
ACC    = 60.0                # mm/s^2
# ------------------------------------------------

from serial.tools import list_ports

# Prefer pydobot; else pydobot2
try:
    from pydobot import Dobot
except ImportError:
    from pydobot2 import Dobot

# Your modules
from grid_module import draw_grid
import draw_symbols as dm               # we'll set dm.CELL to match the grid
from draw_symbols import draw_x, draw_o
from ttt_minimax_ij import decide_next_ij

# ---------------- Robot helpers ----------------
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

def print_pose_and_joints(bot, p):
    x, y, z, r = p[:4]
    print(f"Pose:   x={x:.2f}  y={y:.2f}  z={z:.2f}  r={r:.2f}")
    joints = None
    for name in ("angles", "get_angles", "joint_angles", "get_joint_angles"):
        if hasattr(bot, name):
            try:
                a = getattr(bot, name)()
                if a and len(a) >= 4:
                    joints = tuple(a[:4]); break
            except Exception:
                pass
    if joints is None and len(p) >= 8:
        joints = tuple(p[4:8])
    if joints:
        j1, j2, j3, j4 = joints
        print(f"Joints: j1={j1:.2f}  j2={j2:.2f}  j3={j3:.2f}  j4={j4:.2f}")
    else:
        print("Joints: unavailable from API")

def connect(port=None):
    sel = port
    if sel is None:
        for cand in list_ports.comports():
            try:
                b = Dobot(port=cand.device)
                _ = b.pose()
                sel = cand.device
                b.close()
                print(f"Auto-detected: {sel}")
                break
            except Exception:
                try: b.close()
                except Exception: pass
                continue
        if sel is None:
            raise RuntimeError("No Dobot found. Set PORT explicitly.")
    bot = Dobot(port=sel)
    try:
        bot.speed(VEL, ACC)
    except Exception:
        pass
    p = get_pose_tuple(bot)
    print(f"Connected on {sel}")
    print_pose_and_joints(bot, p)
    return bot

def pen_up(bot):
    x, y, z, r, *_ = get_pose_tuple(bot)
    bot.move_to(x, y, Z_UP, r, wait=True)

def pen_down(bot):
    x, y, z, r, *_ = get_pose_tuple(bot)
    bot.move_to(x, y, Z_DRAW, r, wait=True)

# --------------- Game helpers ------------------
def pretty_board(b):
    def cell(v): return (v or ' ').upper()
    return "\n".join([" | ".join(cell(x) for x in row) for row in b])

def other(sym): return 'O' if sym == 'X' else 'X'

def counts(board):
    xs = sum(1 for r in board for c in r if str(c).upper() == 'X')
    os = sum(1 for r in board for c in r if str(c).upper() in ('O','Y'))
    return xs, os

def current_turn_symbol(board):
    xs, os = counts(board)
    return 'X' if xs == os else 'O'

def human_move_input(board, expected_symbol):
    while True:
        raw = input(f"Your move for '{expected_symbol}' — enter i j (0-2 0-2): ").strip()
        try:
            parts = raw.replace(',', ' ').split()
            if len(parts) != 2: raise ValueError
            i, j = int(parts[0]), int(parts[1])
            if not (0 <= i <= 2 and 0 <= j <= 2):
                print("Indices must be 0..2."); continue
            if str(board[i][j]).strip():
                print("Cell is not empty. Choose another."); continue
            return i, j
        except Exception:
            print("Format example: 1 2 (row=1, col=2)")

def winner(board):
    W = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    flat = [str(board[i][j]).upper() if str(board[i][j]) else ' ' for i in range(3) for j in range(3)]
    for a,b,c in W:
        if flat[a] != ' ' and flat[a] == flat[b] == flat[c]:
            return flat[a]
    return None

def is_draw(board):
    return all(str(board[i][j]).strip() for i in range(3) for j in range(3)) and winner(board) is None

def cell_index(i, j): return 3*i + j

def compute_symbol_origin_from_corner(top_left_corner_xy, side_mm, y_down_is_negative=True):
    ox, oy = top_left_corner_xy
    cell = side_mm / 3.0
    sign = -1.0 if y_down_is_NEGATIVE else +1.0  # (spelled below as constant)
    cx = ox + 0.5 * cell
    cy = oy + sign * (0.5 * cell)
    return (cx, cy)

# --------------- Orchestration -----------------
def load_and_draw_grid(bot):
    """
    1) Ask operator to jog pen ABOVE the OUTER top-left corner.
    2) Draw the 3x3 grid using grid_module.draw_grid.
    3) Set draw_symbols.CELL to match the grid and compute symbol-origin (top-left cell center).
    """
    input("\nJog the pen ABOVE the OUTER TOP-LEFT corner at safe Z, then press <Enter>...")
    x0, y0, z0, r0 = get_pose_tuple(bot)[:4]
    top_left_corner = (x0, y0)
    print(f"Captured top-left corner: ({x0:.2f}, {y0:.2f})")

    # Draw the grid (8 lines total)
    draw_grid(bot, top_left_corner, SIDE_MM, PAD_MM, y_down_is_negative=Y_DOWN_IS_NEGATIVE)
    pen_up(bot)

    # Make draw module use matching cell size
    dm.CELL = SIDE_MM / 3.0
    # If your Y direction is opposite, edit draw_symbols.cell_center accordingly.

    # Compute the origin for draw_symbols (center of top-left cell)
    cell_origin = compute_symbol_origin_from_corner(top_left_corner, SIDE_MM, y_down_is_negative=Y_DOWN_IS_NEGATIVE)
    print(f"Symbol origin (top-left cell center): ({cell_origin[0]:.2f}, {cell_origin[1]:.2f})  CELL={dm.CELL:.2f} mm")
    return cell_origin

def robot_move(bot, board, cell_origin):
    # Minimax decides based on current board (which implies the symbol to play)
    i, j = decide_next_ij(board)
    sym = current_turn_symbol(board)  # should match minimax’s turn
    idx = cell_index(i, j)
    print(f"[Robot] plays '{sym}' at (i={i}, j={j}) (idx={idx})")
    if sym == 'X':
        draw_x(bot, cell_origin, idx)
    else:
        draw_o(bot, cell_origin, idx)
    board[i][j] = sym
    pen_up(bot)

def human_turn(board, human_symbol):
    print("\nCurrent board:\n" + pretty_board(board))
    i, j = human_move_input(board, human_symbol)
    board[i][j] = human_symbol
    input("Please draw your symbol on the paper at that cell, then press <Enter> to continue...")

def game_loop(bot, cell_origin):
    # Initialize empty board
    board = [['', '', ''], ['', '', ''], ['', '', '']]

    # Ask human which symbol they want
    while True:
        human = input("Choose your symbol ('X' or 'O'): ").strip().upper()
        if human == 'Y': human = 'O'
        if human in ('X','O'): break
        print("Please enter X or O.")
    robot = other(human)

    # Ask who starts
    while True:
        starter = input("Who starts first? ('human' or 'robot'): ").strip().lower()
        if starter in ('human','robot'): break
        print("Please enter 'human' or 'robot'.")

    print(f"\nYou are '{human}'. Robot is '{robot}'. {starter.capitalize()} starts.\n")

    turn = starter
    while True:
        if turn == 'human':
            # Make sure the internal “whose turn” matches counts
            expected = current_turn_symbol(board)
            if expected != human:
                print(f"[Note] Board indicates '{expected}' should move, but human is '{human}'. Proceeding anyway.")
            human_turn(board, human)
        else:
            expected = current_turn_symbol(board)
            if expected != robot:
                print(f"[Note] Board indicates '{expected}' should move, but robot is '{robot}'. Proceeding anyway.")
            robot_move(bot, board, cell_origin)

        # Check end states
        w = winner(board)
        if w:
            print("\nFinal board:\n" + pretty_board(board))
            print(f"\nGame over — '{w}' wins!")
            break
        if is_draw(board):
            print("\nFinal board:\n" + pretty_board(board))
            print("\nGame over — draw.")
            break

        # Next turn
        turn = 'robot' if turn == 'human' else 'human'

def main():
    bot = connect(PORT)
    try:
        # 1) Load & draw grid; compute symbol origin (top-left cell center)
        origin = load_and_draw_grid(bot)

        # 2) Run the interactive game loop
        game_loop(bot, origin)

    finally:
        bot.close()

if __name__ == "__main__":
    # internal constant used in compute_symbol_origin_from_corner
    Y_DOWN_IS_NEGATIVE_CONST = Y_DOWN_IS_NEGATIVE
    # fix name used inside the helper (to avoid shadowing error)
    global y_down_is_NEGATIVE
    y_down_is_NEGATIVE = Y_DOWN_IS_NEGATIVE_CONST
    main()
