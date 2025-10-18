# ttt_minimax_ij.py
# Input: 3x3 matrix with 'X', 'O' (or 'Y' treated as 'O'), and empty ('', '.', '_', None, ' ').
# Output: (i, j) for the best next move (row, col in 0..2).

from typing import List, Optional, Tuple

WIN = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def _norm_cell(c) -> str:
    if c is None: return ' '
    s = str(c).strip().upper()
    if s in ('', '.', '_'): return ' '
    if s == 'Y': return 'O'  # tolerate 'Y'
    return s if s in ('X', 'O') else ' '

def _to_flat(board3: List[List[object]]) -> List[str]:
    if (not isinstance(board3, list) or len(board3) != 3 or
        any(not isinstance(r, list) or len(r) != 3 for r in board3)):
        raise ValueError("Board must be a 3x3 matrix.")
    return [_norm_cell(board3[i][j]) for i in range(3) for j in range(3)]

def _winner(b: List[str]) -> Optional[str]:
    for a,b1,c in WIN:
        if b[a] != ' ' and b[a] == b[b1] == b[c]:
            return b[a]
    return None

def _terminal(b: List[str]) -> bool:
    return _winner(b) is not None or all(x != ' ' for x in b)

def _turn(b: List[str]) -> str:
    return 'X' if b.count('X') == b.count('O') else 'O'

def _score(b: List[str], me: str, depth: int) -> int:
    w = _winner(b)
    if w == me:        return 10 - depth   # quicker wins better
    if w and w != me:  return depth - 10   # later losses better
    return 0

def _moves(b: List[str]) -> List[int]:
    return [i for i,v in enumerate(b) if v == ' ']

def _other(p: str) -> str:
    return 'O' if p == 'X' else 'X'

def _minimax(b: List[str], me: str, turn: str, depth: int, alpha: int, beta: int) -> Tuple[int, Optional[int]]:
    if _terminal(b):
        return _score(b, me, depth), None
    best_move = None
    if turn == me:  # maximize
        best = -10**9
        for m in _moves(b):
            b[m] = turn
            val, _ = _minimax(b, me, _other(turn), depth+1, alpha, beta)
            b[m] = ' '
            if val > best:
                best, best_move = val, m
            alpha = max(alpha, val)
            if beta <= alpha: break
        return best, best_move
    else:           # minimize
        best = 10**9
        for m in _moves(b):
            b[m] = turn
            val, _ = _minimax(b, me, _other(turn), depth+1, alpha, beta)
            b[m] = ' '
            if val < best:
                best, best_move = val, m
            beta = min(beta, val)
            if beta <= alpha: break
        return best, best_move

def decide_next_ij(board3x3: List[List[object]]) -> Tuple[int, int]:
    """
    Returns (i, j) for the best immediate move for the player whose turn it is.
    i, j are 0..2 (row, col).
    """
    b = _to_flat(board3x3)
    player = _turn(b)               # figure out whose move it is
    _, move = _minimax(b, player, player, 0, -10**9, 10**9)
    if move is None:
        raise RuntimeError("Game over or no legal moves.")
    i, j = divmod(move, 3)
    return i, j


def run_minimax(board=None):
    
    if board is None:
        return None
    else:
        i, j = decide_next_ij(board)
        return i,j 

# ---- demo ----
# if __name__ == "__main__":
#     board = [
#         ['X', '', 'O'],
#         ['', '0', ''],
#         ['', '', 'X']
#     ]
#     i, j = decide_next_ij(board)
#     print(f"Next move: (i={i}, j={j})")
    # Then call your robot:
    # idx = 3*i + j
    # draw_x(bot, origin, idx) or draw_o(bot, origin, idx) based on whose turn it is.


if __name__ == "__main__":
    board = ""
    run_minimax(board)
