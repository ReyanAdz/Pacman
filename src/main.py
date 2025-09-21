import tkinter as tk
from game import Game

def main():
    root = tk.Tk()
    root.title("Pac-Man AI")
    root.resizable(False, False)

    game = Game(root)
    game.start()

    root.mainloop()

if __name__ == "__main__":
    main()
