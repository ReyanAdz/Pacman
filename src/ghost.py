import random
from collections import deque
from typing import Tuple, List, Optional

DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

def neighbors(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if not board.is_wall(nr, nc):
            yield (nr, nc)

# ---------------- Base class ----------------
class Ghost:
    def __init__(self, start_rc: Tuple[int,int], color: str = "red", image: Optional[object] = None):
        self.r, self.c = start_rc
        self.color = color
        self.image = image  # Tk PhotoImage (if provided)
        self._prev = None   # previous cell (for simple backtracking avoidance)

    @property
    def pos(self) -> Tuple[int,int]:
        return (self.r, self.c)

    def set_pos(self, rc: Tuple[int,int]):
        self.r, self.c = rc

    def step(self, game) -> None:
        """Override in subclasses."""
        pass

# ---------------- Random ghost ----------------
class RandomGhost(Ghost):
    def step(self, game) -> None:
        opts = list(neighbors(game.board, self.r, self.c))
        if not opts:
            return
        # avoid immediately going back if we have other options
        if self._prev and len(opts) > 1 and self._prev in opts:
            opts.remove(self._prev)
        nxt = random.choice(opts)
        self._prev = (self.r, self.c)
        self.r, self.c = nxt

# ---------------- BFS ghost ----------------
class BFSGhost(Ghost):
    def __init__(self, start_rc, color="cyan", image: Optional[object]=None, replan_every=6):
        super().__init__(start_rc, color, image)
        self.replan_every = replan_every
        self._tick = 0
        self._path: List[Tuple[int,int]] = []

    def _bfs(self, start, goal, board) -> List[Tuple[int,int]]:
        q = deque([start])
        parent = {start: None}
        while q:
            cur = q.popleft()
            if cur == goal:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                return list(reversed(path))
            for nxt in neighbors(board, *cur):
                if nxt not in parent:
                    parent[nxt] = cur
                    q.append(nxt)
        return []

    def step(self, game) -> None:
        self._tick += 1
        pac = tuple(game.pacman_pos)
        # Recompute path periodically or if empty
        if self._tick % self.replan_every == 0 or not self._path:
            self._path = self._bfs((self.r, self.c), pac, game.board)
        # Follow one step along the path
        if self._path and len(self._path) > 1:
            self._path.pop(0)
            nr, nc = self._path[0]
            self._prev = (self.r, self.c)
            self.r, self.c = (nr, nc)
