class State:
    def __init__(self, game):
        self.game = game
        self.prev_state = None

    def render(self, screen):
        pass

    def update(self):
        pass

    def handle_events(self,event):
        pass

    def enter_state(self):
        if len(self.game.state_stack) > 1:
            self.prev_state = self.game.state_stack[-1]
        self.game.state_stack.append(self)

    def exit_state(self):
        self.game.state_stack.pop()
