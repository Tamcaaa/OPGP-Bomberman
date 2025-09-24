class StateManager:
    def __init__(self, game):
        self.game = game
        self.state_map = {
            "GameOver": "states.game_over.GameOver",
            "TestField": "states.test_field.TestField",
            "MainMenu": "states.main_menu.MainMenu",
            "Pause": "states.pause_state.PauseState",
            "Settings": "states.settings.Settings",
            "MapSelector": "states.map_selector.MapSelector",
            "MultiplayerSelector": "states.multiplayer_selector.MultiplayerSelector",
            "MultiplayerLobby": "states.multiplayer_lobby.MultiplayerLobby",
            "InputPopup": "states.input_popup.InputPopup",
            "MultiplayerMapSelector": "states.multiplayer_map_selector.MultiplayerMapSelector",
            "MultiplayerTestField": "states.multiplayer_test_field.MultiplayerTestField",
        }

    def change_state(self, class_path: str, *args) -> None:
        class_path = self.state_map.get(class_path, class_path)
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            state_class = getattr(module, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Cannot import state '{class_path}': {e}")

        new_state = state_class(self.game, *args) if args else state_class(self.game)
        new_state.enter_state()