import json, os

SETTINGS_FILE = "user_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            if "player1_keys" in data:
                import config
                config.PLAYER1_MOVE_KEYS[:] = data["player1_keys"]
                config.PLAYER2_MOVE_KEYS[:] = data["player2_keys"]
                config.PLAYER_CONFIG[1]['move_keys'] = config.PLAYER1_MOVE_KEYS
                config.PLAYER_CONFIG[2]['move_keys'] = config.PLAYER2_MOVE_KEYS
            return data
    return {}

def save_settings(settings: dict):
    import config
    settings["player1_keys"] = list(config.PLAYER1_MOVE_KEYS)
    settings["player2_keys"] = list(config.PLAYER2_MOVE_KEYS)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)