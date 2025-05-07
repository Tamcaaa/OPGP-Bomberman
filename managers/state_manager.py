class StateManager:
    def __init__(self, game):
        self.game = game
        self.state_map = {
            "GameOver": "states.game_over.GameOver",
            "TestField": "states.test_field.TestField",
            "MainMenu": "states.main_menu.MainMenu",
            "Victory": "states.victory.Victory"
        }

    def change_state(self, class_path: str, arg: int | None = None) -> None:
        class_path = self.state_map.get(class_path, class_path)
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            state_class = getattr(module, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Cannot import state '{class_path}': {e}")

        new_state = state_class(self.game, arg) if arg else state_class(self.game)
        new_state.enter_state()
