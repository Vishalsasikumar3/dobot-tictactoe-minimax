# Dobot Magician Lite — Autonomous Tic-Tac-Toe Robot

**RAS 545 · Midterm 1 · Arizona State University · Fall 2025**

> A fully autonomous Tic-Tac-Toe-playing robot: Minimax AI computes optimal moves, the Dobot Magician Lite physically draws symbols on paper, and a computer vision pipeline detects the human player's moves via camera.

---

## Demo

[![Midterm 1 Demo](https://img.youtube.com/vi/SA_hQXTBo4I/0.jpg)](https://youtube.com/shorts/SA_hQXTBo4I)

---

## Overview

The Dobot Magician Lite (Serial: `DT-MGL-4R002-01E`) is programmed to play a physical game of Tic-Tac-Toe against a human opponent. The robot draws the 3×3 grid, executes its moves by physically drawing 'X' or 'O' symbols with a pen, and uses the **Minimax algorithm** to guarantee optimal play. The human player draws their symbol on the board and the system tracks game state via keyboard input with a planned CV integration via `opencv_to_gemini.py`.

---

## Repository Structure
```
.
├── main.py                  # Main game loop — orchestrates vision, AI, and robot control
├── minimax.py               # Minimax algorithm — optimal move selection
├── robot_draw.py            # Dobot drawing control — grid, X, O symbols
├── draw_grid.py             # Grid geometry and coordinate calculation
├── camera_det.py            # Camera detection and initialization
├── port_connec.py           # Serial port connection to Dobot
├── port_connection.py       # Improved serial port handler
├── Midterm_1_report.pdf     # 3-page project report (IEEE format)
└── README.md
```

---

## System Architecture
```
Human input / Camera → Board state update
                              ↓
                     Minimax algorithm
                              ↓
                    Optimal move (i, j)
                              ↓
              Grid index → Dobot XY coordinates
                              ↓
                   Robot draws symbol on board
```

---

## Technical Details

### Game Logic

- **Algorithm:** Minimax with full game tree search — guarantees robot never loses
- **Human symbol:** 'X' or 'O' (player choice at start)
- **Turn order:** Human first or Robot first (player choice at start)
- **Win detection:** Checks all rows, columns, and diagonals after every move
- **Draw detection:** Full board with no winner → "D" result

### Robot Drawing

| Parameter | Value |
|---|---|
| Robot | Dobot Magician Lite |
| End effector | Pen / marker |
| Grid size | 95.0 mm outer side |
| Z draw height | 0.5 mm |
| Z travel height | 20.0 mm |
| Repeatability | ±0.2 mm |
| Max reach | 340 mm |
| Software | Python + pydobot |

### Coordinate System

The operator jogs the pen to the **top-left corner** of the grid at startup. All subsequent cell coordinates are computed relative to this datum using grid cell size and padding offsets — no hardcoded absolute positions.

---

## Setup & Usage

### Requirements
```bash
pip install pydobot opencv-python
```

### Run
```bash
python main.py
```

On startup:
1. Robot auto-detects serial port and connects
2. Operator jogs pen to top-left grid corner and confirms
3. Robot draws the 3×3 grid
4. Player selects symbol and who goes first
5. Game loop begins — alternating human and robot turns
6. Robot announces win / draw at game end

---

## Lessons Learned

- Minimax guarantees optimal play but requires the internal board state to be accurate — human input errors bypass the strategy entirely
- Z-height calibration is critical: too high = no ink, too low = pen drag causes movement errors
- Defining a user-set coordinate datum at startup (top-left corner jog) is far more robust than hardcoded absolute positions — adapts to any table setup
- Replacing CV board detection with keyboard input simplified deployment but removed the autonomous sensing capability

---

## Course Info

- **Course:** RAS 545 — Robotic and Autonomous Systems
- **Instructor:** Prof. Mostafa Yourdkhani
- **University:** Arizona State University, Tempe AZ
- **Semester:** Fall 2025
- **Grade:** 30 / 40
