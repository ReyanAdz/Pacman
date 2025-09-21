class Board:
    """
    ASCII map legend:
      '#': wall
      '.': pellet
      'P': pacman start
      'G': ghost start
      ' ': empty
    """
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
        self.grid = lines
        self.height = len(lines)
        self.width = max(len(row) for row in lines)
        # normalize rows to same width
        self.grid = [row.ljust(self.width) for row in self.grid]

        self.pellets = []
        self.ghost_starts = []
        self.player_start = (1, 1)

        for r, row in enumerate(self.grid):
            for c, ch in enumerate(row):
                if ch == '.': self.pellets.append((r, c))
                elif ch == 'P': self.player_start = (r, c)
                elif ch == 'G': self.ghost_starts.append((r, c))

        self.pellet_set = set(self.pellets)

    def in_bounds(self, r, c):
        return 0 <= r < self.height and 0 <= c < self.width

    def is_wall(self, r, c):
        if not self.in_bounds(r, c): return True
        return self.grid[r][c] == '#'
