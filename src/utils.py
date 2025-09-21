DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

def neighbors(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r+dr, c+dc
        if not board.is_wall(nr, nc):
            yield (nr, nc)
