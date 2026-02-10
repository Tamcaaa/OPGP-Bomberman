class StateManager:
    def __init__(self, game):
        self.game = game
        self.state_map = {
            "GameOver": "states.singleplayer.game_over.GameOver",
            "TestField": "states.singleplayer.test_field.TestField",
            "MainMenu": "states.general.main_menu.MainMenu",
            "Pause": "states.singleplayer.pause_state.PauseState",
            "Settings": "states.general.settings.Settings",
            "MapSelector": "states.singleplayer.map_selector.MapSelector",
            "MultiplayerSelector": "states.multiplayer.multiplayer_selector.MultiplayerSelector",
            "MultiplayerLobby": "states.multiplayer.multiplayer_lobby.MultiplayerLobby",
            "InputPopup": "states.multiplayer.multiplayer_input_popup.InputPopup",
            "MultiplayerMapSelector": "states.multiplayer.multiplayer_map_selector.MultiplayerMapSelector",
            "SkinSelector": "states.singleplayer.skin_selector.SkinSelector",
            "MultiplayerTestField": "states.multiplayer.multiplayer_test_field.MultiplayerTestField",
            "MultiplayerGameOver": 'states.multiplayer.multiplayer_game_over.MultiplayerGameOver',
        }

    def change_state(self, class_path: str, *args, **kwargs) -> None:
        class_path = self.state_map.get(class_path, class_path)
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            state_class = getattr(module, class_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ImportError(f"Cannot import state '{class_path}': {e}")

        new_state = state_class(self.game, *args, **kwargs)
        new_state.enter_state()