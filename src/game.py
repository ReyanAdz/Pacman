import tkinter as tk
from board import Board

CELL = 24

class Game:
    def __init__(self, root):
        self.root = root
        self.board = Board("maps/default_map.txt")
        self.rows, self.cols = self.board.height, self.board.width
        self.canvas = tk.Canvas(root, width=self.cols*CELL, height=self.rows*CELL, bg="black")
        self.canvas.pack()

        self.pacman_pos = list(self.board.player_start)  # (r, c)
        root.bind("<KeyPress>", self.handle_input)

    def start(self):
        self.draw()
        self.update()

    def draw(self):
        self.canvas.delete("all")
        # walls
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board.is_wall(r, c):
                    x0, y0 = c*CELL, r*CELL
                    self.canvas.create_rectangle(x0, y0, x0+CELL, y0+CELL, fill="#2030ff", width=0)
        # pellets (simple small dots)
        for (r, c) in self.board.pellets:
            x, y = c*CELL + CELL//2, r*CELL + CELL//2
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="white", width=0)

        # pacman
        pr, pc = self.pacman_pos
        x0, y0 = pc*CELL, pr*CELL
        self.canvas.create_oval(x0+3, y0+3, x0+CELL-3, y0+CELL-3, fill="yellow", width=0)

    def try_move(self, dr, dc):
        nr = self.pacman_pos[0] + dr
        nc = self.pacman_pos[1] + dc
        if not self.board.is_wall(nr, nc):
            self.pacman_pos = [nr, nc]
            # eat pellet if present
            if (nr, nc) in self.board.pellet_set:
                self.board.pellet_set.remove((nr, nc))
                self.board.pellets.remove((nr, nc))

    def handle_input(self, event):
        key = event.keysym
        if key == "Up":    self.try_move(-1, 0)
        if key == "Down":  self.try_move(1, 0)
        if key == "Left":  self.try_move(0, -1)
        if key == "Right": self.try_move(0, 1)
        self.draw()

    def update(self):
        # TODO: call ghost AI every N frames
        self.root.after(100, self.update)
