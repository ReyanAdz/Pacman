import math
import tkinter as tk
from board import Board
from ghost import RandomGhost, BFSGhost

CELL = 24

# timing
TICK_MS = 16                   # ~60 ticks/sec
PAC_SPEED = 120                # pixels per second (tune)
GHOST_TICK_EVERY = 6           # ghost step interval (ticks)

DIRS = {
    "Up":    (-1, 0),
    "Down":  ( 1, 0),
    "Left":  ( 0,-1),
    "Right": ( 0, 1),
}

def dir_to_name(dr, dc):
    if (dr, dc) == (-1, 0): return "up"
    if (dr, dc) == ( 1, 0): return "down"
    if (dr, dc) == ( 0,-1): return "left"
    if (dr, dc) == ( 0, 1): return "right"
    return "right"

def tile_center_px(r, c):
    """Return the pixel coords (x,y) of the center of grid cell (r,c)."""
    return (c * CELL + CELL // 2, r * CELL + CELL // 2)

def same_tile(a, b):
    return a[0] == b[0] and a[1] == b[1]

class Game:
    def __init__(self, root):
        self.root = root
        self.map_path = "maps/default_map.txt"
        self.board = Board(self.map_path)
        self.rows, self.cols = self.board.height, self.board.width

        self.canvas = tk.Canvas(root, width=self.cols*CELL, height=self.rows*CELL, bg="black")
        self.canvas.pack()
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress>", self.handle_input)
        root.bind("<KeyPress>", self.handle_input)  # belt & suspenders

        # --- Pac-Man state (grid + pixel) ---
        self.pac_tile = list(self.board.player_start)   # [r, c]
        self.pac_dir  = (0, 1)                          # current committed dir
        self.next_dir = None                             # queued desired dir

        # pixel position at center of starting tile
        cx, cy = tile_center_px(self.pac_tile[0], self.pac_tile[1])
        self.pac_px, self.pac_py = float(cx), float(cy)

        # target tile we are moving toward (None means idle)
        self.pac_target = self._compute_next_target(self.pac_tile, self.pac_dir)

        # --- Pac-Man sprites (your pack uses 1..3) ---
        from tkinter import PhotoImage
        self.pac_images = {
            "up": [
                PhotoImage(file="assets/pacman-up/1.png"),
                PhotoImage(file="assets/pacman-up/2.png"),
                PhotoImage(file="assets/pacman-up/3.png"),
            ],
            "down": [
                PhotoImage(file="assets/pacman-down/1.png"),
                PhotoImage(file="assets/pacman-down/2.png"),
                PhotoImage(file="assets/pacman-down/3.png"),
            ],
            "left": [
                PhotoImage(file="assets/pacman-left/1.png"),
                PhotoImage(file="assets/pacman-left/2.png"),
                PhotoImage(file="assets/pacman-left/3.png"),
            ],
            "right": [
                PhotoImage(file="assets/pacman-right/1.png"),
                PhotoImage(file="assets/pacman-right/2.png"),
                PhotoImage(file="assets/pacman-right/3.png"),
            ]
        }
        self.pac_frame = 0
        self._last_facing = "right"
        # chomp pacing: advance frame every N tile-centers reached (here: each center)
        self._chomp_on_arrival = True

        # --- Ghost sprites ---
        self.ghost_images = {
            "blinky": PhotoImage(file="assets/ghosts/blinky.png"),
            "pinky":  PhotoImage(file="assets/ghosts/pinky.png"),
            "inky":   PhotoImage(file="assets/ghosts/inky.png"),
            "clyde":  PhotoImage(file="assets/ghosts/clyde.png"),
            "blue":   PhotoImage(file="assets/ghosts/blue_ghost.png"),
        }

        # --- Ghosts ---
        self.ghosts = self._build_ghosts()
        self.ghost_step_every = GHOST_TICK_EVERY
        self._ghost_timer = 0

        # timing / life
        self._tick = 0
        self._alive = True

    # ---------------- Helpers ----------------
    def _build_ghosts(self):
        starts = self.board.ghost_starts or [(self.pac_tile[0], max(1, self.pac_tile[1]-3))]
        a = starts[0]
        b = starts[1] if len(starts) > 1 else starts[0]
        c = starts[2] if len(starts) > 2 else starts[0]
        d = starts[3] if len(starts) > 3 else starts[0]
        return [
            BFSGhost(a, image=self.ghost_images["blinky"], replan_every=6),
            RandomGhost(b, image=self.ghost_images["pinky"]),
            RandomGhost(c, image=self.ghost_images["inky"]),
            RandomGhost(d, image=self.ghost_images["clyde"]),
        ]

    def reset_game(self):
        self.board = Board(self.map_path)
        self.rows, self.cols = self.board.height, self.board.width
        self.pac_tile = list(self.board.player_start)
        self.pac_dir  = (0, 1)
        self.next_dir = None
        cx, cy = tile_center_px(self.pac_tile[0], self.pac_tile[1])
        self.pac_px, self.pac_py = float(cx), float(cy)
        self.pac_target = self._compute_next_target(self.pac_tile, self.pac_dir)
        self.pac_frame = 0
        self._last_facing = "right"
        self.ghosts = self._build_ghosts()
        self._tick = 0
        self._ghost_timer = 0
        self._alive = True

    def _wrap_tile(self, r, c):
        if c < 0: c = self.cols - 1
        elif c >= self.cols: c = 0
        if r < 0: r = self.rows - 1
        elif r >= self.rows: r = 0
        return r, c

    def passable(self, r, c):
        r, c = self._wrap_tile(r, c)
        return not self.board.is_wall(r, c)

    def _compute_next_target(self, tile_rc, direction):
        """Return next target tile (r,c) from tile_rc moving 1 step in direction, or None if blocked."""
        dr, dc = direction
        if dr == 0 and dc == 0:
            return None
        tr, tc = self._wrap_tile(tile_rc[0] + dr, tile_rc[1] + dc)
        if self.board.is_wall(tr, tc):
            return None
        return (tr, tc)

    def _at_tile_center(self):
        """True if Pac-Man's pixel position is (close to) the center of his current tile."""
        cx, cy = tile_center_px(self.pac_tile[0], self.pac_tile[1])
        return abs(self.pac_px - cx) < 0.5 and abs(self.pac_py - cy) < 0.5

    # ---------------- Lifecycle ----------------
    def start(self):
        self.draw()
        self.update()

    # ---------------- Rendering ----------------
    def draw(self):
        self.canvas.delete("all")

        # walls
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board.is_wall(r, c):
                    x0, y0 = c*CELL, r*CELL
                    self.canvas.create_rectangle(x0, y0, x0+CELL, y0+CELL, fill="#2030ff", width=0)

        # pellets
        for (r, c) in self.board.pellets:
            x, y = c*CELL + CELL//2, r*CELL + CELL//2
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="white", width=0)

        # pacman (sprite at pixel position)
        facing = dir_to_name(*self.pac_dir) if self.pac_dir != (0,0) else self._last_facing
        img = self.pac_images[facing][self.pac_frame]
        if self.pac_dir != (0,0):
            self._last_facing = facing
        # convert pixel center to top-left for drawing
        top_left_x = int(self.pac_px - CELL//2)
        top_left_y = int(self.pac_py - CELL//2)
        self.canvas.create_image(top_left_x, top_left_y, image=img, anchor="nw")

        # ghosts (still tile-snapped; we can smooth later)
        for g in self.ghosts:
            gr, gc = g.pos
            gx0, gy0 = gc*CELL, gr*CELL
            if getattr(g, "image", None) is not None:
                self.canvas.create_image(gx0, gy0, image=g.image, anchor="nw")
            else:
                self.canvas.create_oval(gx0+4, gy0+4, gx0+CELL-4, gy0+CELL-4, fill=g.color, width=0)

        if not self._alive:
            cx, cy = self.cols*CELL//2, self.rows*CELL//2
            self.canvas.create_text(cx, cy-16, text="GAME OVER", fill="red", font=("Arial", 28, "bold"))
            self.canvas.create_text(cx, cy+16, text="Press R to Retry", fill="white", font=("Arial", 16, "bold"))

    # ---------------- Input ----------------
    def handle_input(self, event):
        if not self._alive and (event.keysym.lower() == 'r'):
            self.reset_game()
            return
        if event.keysym in DIRS:
            self.next_dir = DIRS[event.keysym]

    # ---------------- Tick/update ----------------
    def update(self):
        if self._alive:
            self._tick += 1

            # --- PAC-MAN MOVEMENT (smooth) ---
            if self._at_tile_center():
                r, c = self.pac_tile

                # try to turn into next_dir if possible
                if self.next_dir:
                    ndr, ndc = self.next_dir
                    if self.passable(r + ndr, c + ndc):
                        self.pac_dir = self.next_dir

                # recompute target
                self.pac_target = self._compute_next_target(self.pac_tile, self.pac_dir)
                if self.pac_target is None:
                    self.pac_dir = (0, 0)

            if self.pac_target is not None and self.pac_dir != (0,0):
                tx, ty = tile_center_px(self.pac_target[0], self.pac_target[1])
                dx, dy = tx - self.pac_px, ty - self.pac_py
                dist = math.hypot(dx, dy)
                if dist > 0:
                    step = PAC_SPEED * (TICK_MS / 1000.0)
                    if step >= dist:
                        # snap to target
                        self.pac_px, self.pac_py = float(tx), float(ty)
                        self.pac_tile = [self.pac_target[0], self.pac_target[1]]
                        if self._chomp_on_arrival:
                            self.pac_frame = (self.pac_frame + 1) % 3
                        tr, tc = self.pac_tile
                        if (tr, tc) in self.board.pellet_set:
                            self.board.pellet_set.remove((tr, tc))
                            self.board.pellets.remove((tr, tc))
                        self.pac_target = self._compute_next_target(self.pac_tile, self.pac_dir)
                        if self.pac_target is None:
                            self.pac_dir = (0, 0)
                    else:
                        ux, uy = dx / dist, dy / dist
                        self.pac_px += ux * step
                        self.pac_py += uy * step

            # --- GHOST MOVEMENT (timer-based) ---
            self._ghost_timer += 1
            if self._ghost_timer >= self.ghost_step_every:
                for g in self.ghosts:
                    g.step(self)
                    self.ghost_step_every = 12
                self._ghost_timer = 0

            # --- COLLISION CHECK ---
            pr, pc = self.pac_tile
            for g in self.ghosts:
                if (pr, pc) == g.pos:
                    self._alive = False
                    break

        self.draw()
        self.root.after(TICK_MS, self.update)

