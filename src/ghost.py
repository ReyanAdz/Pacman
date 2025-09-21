class Ghost:
    def __init__(self, start_rc, controller):
        self.r, self.c = start_rc
        self.controller = controller  # e.g., BFSController()

    def step(self, game_state):
        # ask controller for next (r,c) or direction
        pass
