from collections import deque

def bfs(start, goal, board):
    """
    start, goal: (r,c)
    board: Board
    returns: list[(r,c)] path including start->goal, or [] if none
    """
    q = deque([start])
    parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
    while q:
        cur = q.popleft()
        if cur == goal:
            # reconstruct
            path = []
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return list(reversed(path))
        r, c = cur
        for nr in [ (r-1,c),(r+1,c),(r,c-1),(r,c+1) ]:
            if nr in parent: 
                continue
            rr, cc = nr
            if board.is_wall(rr, cc): 
                continue
            parent[nr] = (r, c)
            q.append(nr)
    return []
