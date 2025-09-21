import tkinter as tk

CELL = 24
GRID_W, GRID_H = 28, 31
WIDTH, HEIGHT = GRID_W * CELL, GRID_H * CELL

class Game:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()
        self.pacman_pos = [14, 23]

        # Bind keyboard events
        root.bind("<KeyPress>", self.handle_input)

    def start(self):
        self.draw()
        self.update()

    def draw(self):
        self.canvas.delete("all")
        # Draw Pac-Man
        x, y = self.pacman_pos
        self.canvas.create_oval(
            x*CELL, y*CELL, x*CELL + CELL, y*CELL + CELL,
            fill="yellow"
        )

    def handle_input(self, event):
        dx, dy = 0, 0
        if event.keysym == "Up": dy = -1
        elif event.keysym == "Down": dy = 1
        elif event.keysym == "Left": dx = -1
        elif event.keysym == "Right": dx = 1
        self.pacman_pos[0] += dx
        self.pacman_pos[1] += dy
        self.draw()

    def update(self):
        # Game loop logic will come later (AI, collisions, pellets, etc.)
        self.root.after(100, self.update)
