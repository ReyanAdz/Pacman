import tkinter as tk
from board import Board
from ghost import RandomGhost, BFSGhost

CELL = 24

DIRS = {
    "Up":    (-1, 0),
    "Down":  ( 1, 0),
    "Left":  ( 0,-1),
    "Right": ( 0, 1),
}

def dir_to_name(dr, dc):
    """Convert a direction tuple to a string key for sprite images."""
    if (dr, dc) == (-1, 0):
        return "up"
    elif (dr, dc) == (1, 0):
        return "down"
    elif (dr, dc) == (0, -1):
        return "left"
    elif (dr, dc) == (0, 1):
        return "right"
    else:
        return "right"  # default facing

class Game:
    def __init__(self, root):
        self.root = root
        self.board = Board("maps/default_map.txt")
        self.rows, self.cols = self.board.height, self.board.width
        self.canvas = tk.Canvas(root, width=self.cols*CELL, height=self.rows*CELL, bg="black")
        self.canvas.pack()

        # Make sure we get keyboard events
        self.canvas.focus_set()
        self.canvas.bind("<KeyPress>", self.handle_input)
        root.bind("<KeyPress>", self.handle_input)  # belt & suspenders

        # --- Pac-Man ---
        self.pacman_pos = list(self.board.player_start)   # (r, c)
        self.pac_dir    = (0, 1)      # auto-move to the right initially
        self.next_dir   = None        # buffered desired direction
        self.pac_step_every = 5       # lower=faster; higher=slower

        # Pac-Man sprites (your pack uses files 1..3)
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
        # Animation state
        self.pac_frame = 0
        self._last_facing = "right"

        # --- Ghost sprites ---
        self.ghost_images = {
            "blinky": PhotoImage(file="assets/ghosts/blinky.png"),
            "pinky":  PhotoImage(file="assets/ghosts/pinky.png"),
            "inky":   PhotoImage(file="assets/ghosts/inky.png"),
            "clyde":  PhotoImage(file="assets/ghosts/clyde.png"),
            "blue":   PhotoImage(file="assets/ghosts/blue_ghost.png"),  # frightened mode
        }

        # --- Ghosts list ---
        starts = self.board.ghost_starts or [(self.pacman_pos[0], max(1, self.pacman_pos[1]-3))]
        # Pick up to four start positions (reuse first if not enough in the map)
        start_a = starts[0]
        start_b = starts[1] if len(starts) > 1 else starts[0]
        start_c = starts[2] if len(starts) > 2 else starts[0]
        start_d = starts[3] if len(starts) > 3 else starts[0]

        self.ghosts = [
            BFSGhost(start_a, image=self.ghost_images["blinky"], replan_every=6),
            RandomGhost(start_b, image=self.ghost_images["pinky"]),
            RandomGhost(start_c, image=self.ghost_images["inky"]),
            RandomGhost(start_d, image=self.ghost_images["clyde"]),
        ]
        self.ghost_step_every = 6  # lower=faster; higher=slower

        # timing
        self._tick = 0
        self._alive = True

    # ---------------- Utils ----------------
    def passable(self, r, c):
        """True if (r,c) (with wrap) is not a wall."""
        r2, c2 = r, c
        # Horizontal wrap
        if c2 < 0:            c2 = self.cols - 1
        elif c2 >= self.cols: c2 = 0
        # Vertical wrap (optional; keep or remove for your map)
        if r2 < 0:            r2 = self.rows - 1
        elif r2 >= self.rows: r2 = 0
        return not self.board.is_wall(r2, c2)

    def step_pos(self, r, c, dr, dc):
        """Advance one cell with wrap if not a wall; otherwise stay."""
        nr, nc = r + dr, c + dc
        # Wrap
        if nc < 0:            nc = self.cols - 1
        elif nc >= self.cols: nc = 0
        if nr < 0:            nr = self.rows - 1
        elif nr >= self.rows: nr = 0
        if not self.board.is_wall(nr, nc):
            return nr, nc
        return r, c

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

        # pacman (sprite)
        pr, pc = self.pacman_pos
        facing = dir_to_name(*self.pac_dir) if self.pac_dir != (0,0) else self._last_facing
        self.pac_frame = (self.pac_frame + 1) % 3
        img = self.pac_images[facing][self.pac_frame]
        if self.pac_dir != (0,0):
            self._last_facing = facing
        self.canvas.create_image(pc*CELL, pr*CELL, image=img, anchor="nw")

        # ghosts
        for g in self.ghosts:
            gr, gc = g.pos
            gx0, gy0 = gc*CELL, gr*CELL
            if getattr(g, "image", None) is not None:
                self.canvas.create_image(gx0, gy0, image=g.image, anchor="nw")
            else:
                # fallback: draw as colored blob
                self.canvas.create_oval(gx0+4, gy0+4, gx0+CELL-4, gy0+CELL-4, fill=g.color, width=0)

        # game over overlay
        if not self._alive:
            cx, cy = self.cols*CELL//2, self.rows*CELL//2
            self.canvas.create_text(cx, cy, text="GAME OVER", fill="red", font=("Arial", 28, "bold"))

    # ---------------- Input ----------------
    def handle_input(self, event):
        if event.keysym in DIRS:
            self.next_dir = DIRS[event.keysym]

    # ---------------- Tick/update ----------------
    def update(self):
        if self._alive:
            self._tick += 1

            # --- PAC-MAN AUTO MOVE ---
            if self._tick % self.pac_step_every == 0:
                r, c = self.pacman_pos

                # try to turn into next_dir if possible from current cell
                if self.next_dir:
                    ndr, ndc = self.next_dir
                    if self.passable(r + ndr, c + ndc):
                        self.pac_dir = self.next_dir

                # move one cell along current dir if possible
                dr, dc = self.pac_dir
                if dr != 0 or dc != 0:
                    nr, nc = self.step_pos(r, c, dr, dc)
                    self.pacman_pos = [nr, nc]

                    # eat pellet
                    if (nr, nc) in self.board.pellet_set:
                        self.board.pellet_set.remove((nr, nc))
                        self.board.pellets.remove((nr, nc))

            # --- GHOSTS ---
            if self._tick % self.ghost_step_every == 0:
                for g in self.ghosts:
                    g.step(self)

            # --- collision ---
            pr, pc = self.pacman_pos
            for g in self.ghosts:
                if (pr, pc) == g.pos:
                    self._alive = False
                    break

        self.draw()
        self.root.after(50, self.update)  # global tick rate (ms); tune with *_step_every
