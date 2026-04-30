import os
import socket
import pygame
import config
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from states.general.state import State
from custom_classes.button import Button
from managers.music_manager import MusicManager
from managers.state_manager import StateManager
from managers.network_manager import NetworkManager
from image_loader import load_images, load_hat_images, load_bomb_images, load_explosion_images

# --------------------------------------------------------------------------- #
# Type aliases
# --------------------------------------------------------------------------- #
Addr   = Tuple[str, int]
Packet = Dict[str, Any]

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
PANEL_WIDTH  = 200
PANEL_HEIGHT = 300

# State / scope names
LOBBY_SCOPE            = "MultiplayerLobby"
LOBBY_DISCOVERY_SCOPE  = "LobbyDiscovery"
MAP_SELECTOR_SCOPE     = "MultiplayerMapSelector"
TEST_FIELD_SCOPE       = "MultiplayerTestField"

# Packet type identifiers
PKT_READY_TOGGLE  = "READY_TOGGLE"
PKT_SKIN_UPDATE   = "SKIN_UPDATE"
PKT_STATE_CHANGE  = "STATE_CHANGE"
PKT_PLAYER_LIST   = "PLAYER_LIST"
PKT_JOIN          = "JOIN"
PKT_LEAVE         = "LEAVE"
PKT_HOST_OFFER    = "HOST_OFFER"
PKT_SAME_DATA     = "SAME_DATA"

COLOR_NAMES: Dict[tuple, str] = {
    config.WHITE_PLAYER:       "White",
    config.BLACK_PLAYER:       "Black",
    config.RED_PLAYER:         "Red",
    config.BLUE_PLAYER:        "Blue",
    config.DARK_GREEN_PLAYER:  "Green",
    config.LIGHT_GREEN_PLAYER: "Light Green",
    config.YELLOW_PLAYER:      "Yellow",
    config.PINK_PLAYER:        "Pink",
    config.ORANGE_PLAYER:      "Orange",
    config.PURPLE_PLAYER:      "Purple",
    config.BROWN_PLAYER:       "Brown",
    config.CYAN_PLAYER:        "Cyan",
}

AVAILABLE_HATS_KEYS = list(config.AVAILABLE_HATS.keys())

FONT_PATH = "CaveatBrush-Regular.ttf"

# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class PlayerData:
    name:             str
    addr:             Tuple[str, int]
    is_host:          bool
    is_ready:         bool                 = False
    selection_index:  int                  = 0
    vote_index:       Optional[int]        = None
    color_index:      int                  = 0
    hat_index:        int                  = 0
    bomb_index:       int                  = 0
    explosion_index:  int                  = 0
    final_color:      Tuple[int, int, int] = (0, 0, 0)
    final_hat:        str                  = "None"
    final_bomb:       str                  = "Classic"
    final_explosion:  str                  = "Classic"


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
class MultiplayerLobby(State):
    def __init__(
        self,
        game,
        player_name: str,
        network_manager: NetworkManager,
        players_list: Optional[Dict[str, dict]] = None,
        *,
        is_host: bool = False,
        lobby_name: str = "",
    ) -> None:
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Multiplayer Lobby")

        # Managers
        self.music_manager   = MusicManager()
        self.state_manager   = StateManager(game)
        self.network_manager = network_manager

        # Identity
        self.player_name = player_name
        self.is_host     = is_host
        self.lobby_name  = (lobby_name.strip() if isinstance(lobby_name, str) else "") \
                           or f"{player_name}'s Lobby"

        # Network / state-change bookkeeping
        self.leave_seq:                Optional[int]          = None
        self.leave_target_addr:        Optional[Addr]         = None
        self.pending_state_change:     Optional[str]          = None
        self.state_change_seq_by_addr: Dict[Addr, int]        = {}
        self.host_setup_failed = False
        self.host_setup_error  = ""

        # Player roster
        self.players_list: Dict[str, PlayerData] = (
            self._deserialize_player_list(players_list) if players_list else {}
        )
        self.max_players = 2

        # Animation
        self.last_idle_update = pygame.time.get_ticks()
        self.idle_index = 0
        self.idle_fps   = 4

        # Fonts
        self.skin_font  = pygame.font.Font(FONT_PATH, 20)
        self.info_font  = pygame.font.Font(FONT_PATH, 18)
        self.small_font = pygame.font.Font(FONT_PATH, 16)
        self.large_font = pygame.font.Font(FONT_PATH, 32)
        self.host_font  = pygame.font.Font(None, 40)

        # Available customisation options
        self.available_colors     = list(config.AVAILABLE_COLORS)
        self.available_hats       = list(config.AVAILABLE_HATS.keys())
        self.available_bombs      = list(config.BOMBS)
        self.available_explosions = list(config.EXPLOSIONS)

        # Shared back button (visible for both host and guest)
        self.back_button = Button(
            20, 20,
            config.BUTTON_WIDTH // 1.2, config.BUTTON_HEIGHT,
            "Back",
            font=FONT_PATH,
            button_color=config.COLOR_BEIGE,
        )

        # Role-specific setup
        self._setup_host() if is_host else self._setup_guest()

        # Resolve local player reference (must come after host setup adds the entry)
        self.my_player = self.players_list.get(self.player_name)
        if self.my_player is None:
            raise RuntimeError("my_player is None in MultiplayerLobby – player not in roster.")

        # Skin-selection state (player-slot → category → index)
        self.selected_index: Dict[int, Dict[str, int]] = {
            1: {"color": 0, "hat": 0, "bomb": 0, "explosion": 0},
            2: {"color": 0, "hat": 0, "bomb": 0, "explosion": 0},
        }

        self._sync_indexes_from_player()

        # Assets
        self.images = load_images()
        self.bg     = self.images["skinselector_bg"]
        self._load_skin_assets()
        self.tinted_idle_images: Dict[int, Tuple[pygame.Surface, ...]] = {}
        self._cache_tinted_frames()
        self._sync_player_from_indexes()

    # ---------------------------------------------------------------------- #
    # Setup helpers
    # ---------------------------------------------------------------------- #
    def _setup_host(self) -> None:
        """Bind the socket and register the host's own PlayerData entry."""
        resolved_ip  = self._get_local_ip()
        self.host_ip = resolved_ip or "127.0.0.1"

        try:
            self.network_manager.socket.bind(("", config.SERVER_PORT))
        except OSError as exc:
            self.host_setup_failed = True
            self.host_setup_error  = (
                f"Could not start lobby on port {config.SERVER_PORT}. "
                "Another game instance may already be running."
            )
            print(f"[LOBBY ERROR] {self.host_setup_error} ({exc})")

        if not resolved_ip:
            print("[LOBBY WARNING] Could not resolve a LAN IP – falling back to 127.0.0.1.")

        host_addr = (self.host_ip, config.SERVER_PORT)
        print(f"[LOBBY CREATED] host={self.host_ip}  lobby='{self.lobby_name}'")

        self.players_list[self.player_name] = PlayerData(
            self.player_name, host_addr, is_host=True, is_ready=True
        )

        self.start_button = self._make_bottom_button("Start Game")
        self.start_button.set_visible(False)
        self.start_button.set_enabled(False)

    def _setup_guest(self) -> None:
        """Create the ready button for a non-host player."""
        self.ready_button = self._make_bottom_button("Ready")
        self.ready_button.set_visible(True)
        self.ready_button.set_enabled(True)

    def _make_bottom_button(self, label: str) -> Button:
        return Button(
            config.SCREEN_WIDTH  // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT - 90,
            config.BUTTON_WIDTH  + 10,
            config.BUTTON_HEIGHT + 10,
            label,
            font=FONT_PATH,
            button_color=config.COLOR_BEIGE,
        )

    # ---------------------------------------------------------------------- #
    # Asset loading
    # ---------------------------------------------------------------------- #
    def _load_skin_assets(self) -> None:
        """Load and scale idle frames plus all cosmetic thumbnail images."""
        self.idle_frames: list[pygame.Surface] = []
        for i in range(3):
            path  = os.path.join(self.game.photos_dir, "player_animations", f"p_1_idle_{i}.png")
            frame = pygame.image.load(path).convert_alpha()
            w, h  = frame.get_size()
            self.idle_frames.append(pygame.transform.scale(frame, (w * 4, h * 4)))

        self.hat_images,       self.hat_thumbs       = load_hat_images()
        self.bomb_images,      self.bomb_thumbs      = load_bomb_images()
        self.explosion_images, self.explosion_thumbs = load_explosion_images()

    def _cache_tinted_frames(self, color_index: Optional[int] = None) -> None:
        """
        Pre-generate tinted idle sprites for every player's current color,
        or for a single *color_index* when one is supplied.
        Already-cached indices are skipped.
        """
        if not self.players_list:
            return

        indices_to_cache = (
            [color_index] if color_index is not None
            else [p.color_index for p in self.players_list.values()]
        )

        for idx in indices_to_cache:
            if idx in self.tinted_idle_images:
                continue
            color  = self.available_colors[idx]
            frames = tuple(self._tint_surface(f, color) for f in self.idle_frames)
            self.tinted_idle_images[idx] = frames

    @staticmethod
    def _tint_surface(image: pygame.Surface, color: tuple) -> pygame.Surface:
        tinted = image.copy()
        overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        overlay.fill((*color, 255))
        tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_MULT)
        return tinted

    # ---------------------------------------------------------------------- #
    # Index / selection sync helpers
    # ---------------------------------------------------------------------- #
    def _sync_indexes_from_player(self) -> None:
        """Copy the player's stored indices into the local selection dict."""
        if not self.my_player:
            return
        slot = self.selected_index[1]
        slot["color"]     = self.my_player.color_index
        slot["hat"]       = self.my_player.hat_index
        slot["bomb"]      = self.my_player.bomb_index
        slot["explosion"] = self.my_player.explosion_index

    def _sync_player_from_indexes(self) -> None:
        """Push the local selection indices back onto my_player, resolving final names."""
        if not self.my_player:
            return
        slot = self.selected_index[1]
        p = self.my_player
        p.color_index      = slot["color"]
        p.hat_index        = slot["hat"]
        p.bomb_index       = slot["bomb"]
        p.explosion_index  = slot["explosion"]
        p.final_color      = self.available_colors[p.color_index]
        p.final_hat        = self.available_hats[p.hat_index]
        p.final_bomb       = self.available_bombs[p.bomb_index]["name"]
        p.final_explosion  = self.available_explosions[p.explosion_index]["name"]

    def _apply_skin_packet_to_player(self, player: PlayerData, data: dict) -> None:
        """Update a player's skin indices and resolve their display names."""
        player.color_index     = data.get("color_index",     0)
        player.hat_index       = data.get("hat_index",       0)
        player.bomb_index      = data.get("bomb_index",      0)
        player.explosion_index = data.get("explosion_index", 0)
        player.final_color     = self.available_colors[player.color_index]
        player.final_hat       = self.available_hats[player.hat_index]
        player.final_bomb      = self.available_bombs[player.bomb_index]["name"]
        player.final_explosion = self.available_explosions[player.explosion_index]["name"]

    # ---------------------------------------------------------------------- #
    # Skin selection
    # ---------------------------------------------------------------------- #
    def _cycle_color(self, step: int) -> None:
        """Advance the local player's color, skipping colors already taken."""
        if not self.my_player:
            return
        taken  = {p.color_index for name, p in self.players_list.items() if name != self.player_name}
        index  = self.selected_index[1]["color"]
        n      = len(self.available_colors)
        for _ in range(n):
            index = (index + step) % n
            if index not in taken:
                self.selected_index[1]["color"] = index
                self._cache_tinted_frames(index)
                self._sync_player_from_indexes()
                self.broadcast_skin_update()
                return

    def _cycle_hat(self, step: int) -> None:
        if not self.my_player:
            return
        n = len(self.available_hats)
        self.selected_index[1]["hat"] = (self.selected_index[1]["hat"] + step) % n
        self._sync_player_from_indexes()
        self.broadcast_skin_update()

    def _cycle_bomb(self, step: int) -> None:
        if not self.my_player:
            return
        n = len(self.available_bombs)
        self.selected_index[1]["bomb"] = (self.selected_index[1]["bomb"] + step) % n
        self._sync_player_from_indexes()
        self.broadcast_skin_update()

    def _cycle_explosion(self, step: int) -> None:
        if not self.my_player:
            return
        n = len(self.available_explosions)
        self.selected_index[1]["explosion"] = (self.selected_index[1]["explosion"] + step) % n
        self._sync_player_from_indexes()
        self.broadcast_skin_update()

    # ---------------------------------------------------------------------- #
    # Animation
    # ---------------------------------------------------------------------- #
    def _update_idle_animation(self) -> None:
        now = pygame.time.get_ticks()
        if now - self.last_idle_update >= 1000 // self.idle_fps:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_update = now

    # ---------------------------------------------------------------------- #
    # Network – broadcasting
    # ---------------------------------------------------------------------- #
    def broadcast_skin_update(self) -> None:
        if not self.my_player:
            return
        data = {
            "player_name":     self.my_player.name,
            "color_index":     self.my_player.color_index,
            "hat_index":       self.my_player.hat_index,
            "bomb_index":      self.my_player.bomb_index,
            "explosion_index": self.my_player.explosion_index,
        }
        self._broadcast_to_peers(PKT_SKIN_UPDATE, data)

    def _broadcast_player_list(self) -> None:
        if not self.my_player:
            return
        data = {"player_list": self._serialize_player_list(self.players_list)}
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            print(f"[PLAYER_LIST] Sending to {player.addr}")
            self.network_manager.send_packet(player.addr, PKT_PLAYER_LIST, data, LOBBY_SCOPE)

    def _begin_state_change(self, new_state: str) -> None:
        """Host-only: notify all peers and wait for ACKs before transitioning."""
        if not (self.my_player and self.my_player.is_host):
            return
        if self.pending_state_change:
            return

        self.pending_state_change     = new_state
        self.state_change_seq_by_addr = {}

        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            seq = self.network_manager.send_packet(
                player.addr, PKT_STATE_CHANGE, {"state": new_state}, LOBBY_SCOPE
            )
            self.state_change_seq_by_addr[player.addr] = seq

        if not self.state_change_seq_by_addr:
            self._complete_state_change()

    def _complete_state_change(self) -> None:
        if not self.pending_state_change:
            return
        new_state = self.pending_state_change
        self.pending_state_change = None
        self.state_change_seq_by_addr.clear()
        self.exit_state()
        self.state_manager.change_state(
            new_state, self.players_list, self.network_manager, self.player_name
        )

    # ---------------------------------------------------------------------- #
    # Network – helpers
    # ---------------------------------------------------------------------- #
    def _broadcast_to_peers(self, packet_type: str, data: dict, scope: str = LOBBY_SCOPE) -> None:
        if not self.my_player:
            return
        for player in self.players_list.values():
            if player.addr != self.my_player.addr:
                self.network_manager.send_packet(player.addr, packet_type, data, scope)

    def _send_to_host(self, packet_type: str, data: dict, scope: str = LOBBY_SCOPE) -> None:
        for player in self.players_list.values():
            if player.is_host:
                self.network_manager.send_packet(player.addr, packet_type, data, scope)
                return

    def _get_peer_player(self) -> Optional[PlayerData]:
        """Return the first player that is not the local player, or None."""
        return next(
            (p for name, p in self.players_list.items() if name != self.player_name),
            None,
        )

    def _get_host_player(self) -> Optional[PlayerData]:
        return next((p for p in self.players_list.values() if p.is_host), None)

    @staticmethod
    def _get_local_ip() -> Optional[str]:
        """Resolve the LAN IP via a dummy UDP socket (no data is sent)."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except OSError:
            return None

    # ---------------------------------------------------------------------- #
    # Network – serialisation
    # ---------------------------------------------------------------------- #
    @staticmethod
    def _serialize_player_list(player_list: Dict[str, "PlayerData"]) -> Dict[str, dict]:
        return {name: asdict(data) for name, data in player_list.items()}

    @staticmethod
    def _deserialize_player_list(raw: Dict[str, dict]) -> Dict[str, "PlayerData"]:
        result: Dict[str, PlayerData] = {}
        for name, data in raw.items():
            d = dict(data)
            d["addr"] = tuple(d["addr"])
            result[name] = PlayerData(**d)
        return result

    # ---------------------------------------------------------------------- #
    # Network – packet dispatch
    # ---------------------------------------------------------------------- #
    def _drain_network_packets(self) -> None:
        while True:
            poll_data = self.network_manager.poll()
            if not poll_data:
                break
            self._dispatch_packet(poll_data)

    def _dispatch_packet(self, poll_data: Tuple[Packet, Addr]) -> None:
        packet, addr = poll_data
        scope        = packet.get("scope")
        ptype        = packet.get("type")
        data         = packet.get("data")

        # Discovery packets are handled separately and early-returned
        if scope == LOBBY_DISCOVERY_SCOPE:
            if ptype == "DISCOVER_HOSTS":
                self._on_discover_hosts(addr)
            return

        # Ignore packets addressed to other scopes (e.g. map selector in flight)
        if scope != LOBBY_SCOPE:
            return

        if not ptype or not data:
            raise ValueError(f"Malformed packet (missing type or data): {packet!r} from {addr}")

        handlers = {
            PKT_JOIN:         self._on_join,
            PKT_LEAVE:        self._on_leave,
            PKT_PLAYER_LIST:  self._on_player_list,
            PKT_STATE_CHANGE: self._on_state_change,
            PKT_SKIN_UPDATE:  self._on_skin_update,
            PKT_READY_TOGGLE: self._on_ready_toggle,
        }
        handler = handlers.get(ptype)
        if handler:
            handler(data, addr)

    # ---------------------------------------------------------------------- #
    # Network – packet handlers
    # ---------------------------------------------------------------------- #
    def _on_discover_hosts(self, addr: Addr) -> None:
        if not self.is_host:
            return
        data = {
            "host_name":       self.player_name,
            "lobby_name":      self.lobby_name,
            "current_players": len(self.players_list),
            "max_players":     self.max_players,
        }
        self.network_manager.send_packet(addr, PKT_HOST_OFFER, data, LOBBY_DISCOVERY_SCOPE)

    def _on_join(self, data: dict, addr: Addr) -> None:
        player_name = data.get("player_name", "UNKNOWN")

        if len(self.players_list) >= self.max_players:
            print(f"[JOIN REJECTED] Lobby full – {player_name} from {addr}")
            return

        if player_name in self.players_list:
            print(f"[JOIN REJECTED] Name taken – {player_name} from {addr}")
            self.network_manager.send_packet(
                addr, PKT_SAME_DATA,
                {"msg": f"Player '{player_name}' is already in the lobby."},
                LOBBY_SCOPE,
            )
            return

        if any(p.addr == addr for p in self.players_list.values()):
            print(f"[JOIN REJECTED] Address already present – {addr}")
            return

        # Build new player with a unique color
        new_player = PlayerData(player_name, addr, is_host=False)
        taken_colors = {p.color_index for p in self.players_list.values()}
        new_player.color_index = next(
            (i for i in range(len(self.available_colors)) if i not in taken_colors), 0
        )
        self._apply_skin_packet_to_player(new_player, {
            "color_index":     new_player.color_index,
            "hat_index":       new_player.hat_index,
            "bomb_index":      new_player.bomb_index,
            "explosion_index": new_player.explosion_index,
        })

        self.players_list[player_name] = new_player
        self.network_manager.register_peer(addr)
        print(f"[JOIN] {player_name} joined from {addr}")
        self._broadcast_player_list()

    def _on_leave(self, data: dict, addr: Addr) -> None:
        player_name = data.get("player_name")
        if player_name in self.players_list:
            del self.players_list[player_name]
            print(f"[LEAVE] {player_name} left from {addr}")

    def _on_player_list(self, data: dict, addr: Addr) -> None:
        self.players_list = self._deserialize_player_list(data.get("player_list", {}))
        print(f"[PLAYER_LIST] Updated: {list(self.players_list.keys())}")

    def _on_state_change(self, data: dict, addr: Addr) -> None:
        state = data.get("state")
        print(f"[STATE_CHANGE] → {state} from {addr}")
        self.exit_state()
        self.state_manager.change_state(
            MAP_SELECTOR_SCOPE, self.players_list, self.network_manager, self.player_name, self.lobby_name
        )

    def _on_skin_update(self, data: dict, addr: Addr) -> None:
        player_name = data.get("player_name")
        if player_name not in self.players_list:
            print(f"[SKIN_UPDATE ERROR] Unknown player '{player_name}' from {addr}")
            return
        self._apply_skin_packet_to_player(self.players_list[player_name], data)
        print(f"[SKIN_UPDATE] {player_name} updated skin.")

    def _on_ready_toggle(self, data: dict, addr: Addr) -> None:
        player_name = data.get("player_name")
        if player_name not in self.players_list:
            print(f"[READY_TOGGLE ERROR] Unknown player '{player_name}' from {addr}")
            return
        player = self.players_list[player_name]
        player.is_ready = not player.is_ready
        print(f"[READY_TOGGLE] {player_name} is_ready={player.is_ready}")

    # ---------------------------------------------------------------------- #
    # Periodic checks (called from update)
    # ---------------------------------------------------------------------- #
    def _handle_failed_host_setup(self) -> bool:
        if not self.host_setup_failed:
            return False
        print(f"[LOBBY EXIT] {self.host_setup_error} Returning to MainMenu.")
        self.host_setup_failed = False
        self.exit_state()
        return True

    def _check_state_change_acks(self) -> None:
        if not self.pending_state_change:
            return
        all_acked = all(
            self.network_manager.get_completed_seq(addr, seq=seq)
            for addr, seq in self.state_change_seq_by_addr.items()
        )
        if all_acked:
            self._complete_state_change()

    def _check_leave_seq(self) -> None:
        if not (self.leave_seq and self.leave_target_addr):
            return
        if self.network_manager.get_completed_seq(self.leave_target_addr, seq=self.leave_seq):
            print(f"[LEFT LOBBY] {self.my_player.name} has left the lobby.")
            self.network_manager.close_socket()
            self.exit_state()

    def _check_timed_out_peer(self) -> None:
        if not self.network_manager.peer_timedout:
            return
        if self.my_player.is_host:
            # Remove the first non-host player that timed out
            for name in list(self.players_list):
                if name != self.my_player.name:
                    del self.players_list[name]
                    print(f"[TIMEOUT] {name} timed out – removed from lobby.")
                    break
        else:
            print("[TIMEOUT] Host timed out – returning to MainMenu.")
            self.network_manager.close_socket()
            self.exit_state()
            self.exit_state()

    # ---------------------------------------------------------------------- #
    # Main loop hooks
    # ---------------------------------------------------------------------- #
    def update(self) -> None:
        if self._handle_failed_host_setup():
            return
        self._check_timed_out_peer()
        self._check_leave_seq()
        self._check_state_change_acks()
        self._update_idle_animation()
        self._drain_network_packets()
        self.network_manager.update()

    def handle_events(self, event: pygame.event.Event) -> None:
        if not self.my_player:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_click(event.pos)

        elif event.type == pygame.KEYDOWN and self.player_name in self.players_list:
            self._handle_keydown(event.key)

    def _handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        if self.back_button.rect.collidepoint(pos):
            self._leave_lobby()
            return

        if self.is_host and self.start_button.rect.collidepoint(pos):
            self._begin_state_change(MAP_SELECTOR_SCOPE)
            return

        if not self.is_host and self.ready_button.rect.collidepoint(pos):
            self.my_player.is_ready = not self.my_player.is_ready
            self._send_to_host(PKT_READY_TOGGLE, {"player_name": self.my_player.name})

    def _handle_keydown(self, key: int) -> None:
        bindings = {
            pygame.K_LEFT:  (self._cycle_color, -1),
            pygame.K_a:     (self._cycle_color, -1),
            pygame.K_RIGHT: (self._cycle_color, 1),
            pygame.K_d:     (self._cycle_color, 1),
            pygame.K_UP:    (self._cycle_hat, -1),
            pygame.K_w:     (self._cycle_hat, -1),
            pygame.K_DOWN:  (self._cycle_hat, 1),
            pygame.K_s:     (self._cycle_hat, 1),
            pygame.K_q:     (self._cycle_bomb, -1),
            pygame.K_z:     (self._cycle_bomb, -1),
            pygame.K_e:     (self._cycle_bomb, 1),
            pygame.K_c:     (self._cycle_bomb, 1),
            pygame.K_r:     (self._cycle_explosion, -1),
            pygame.K_f:     (self._cycle_explosion, 1),
        }
        action = bindings.get(key)
        if action:
            fn, step = action
            fn(step)

    def _leave_lobby(self) -> None:
        packet_data = {"player_name": self.my_player.name}
        if self.my_player.is_host:
            peer = self._get_peer_player()
            if not peer:
                self.network_manager.close_socket()
                self.exit_state()
                return
            self.leave_target_addr = peer.addr
            self.leave_seq = self.network_manager.send_packet(
                peer.addr, PKT_LEAVE, packet_data, LOBBY_SCOPE
            )
        else:
            host = self._get_host_player()
            self.leave_target_addr = host.addr
            self.leave_seq = self.network_manager.send_packet(
                host.addr, PKT_LEAVE, packet_data, LOBBY_SCOPE
            )

    # ---------------------------------------------------------------------- #
    # Rendering
    # ---------------------------------------------------------------------- #
    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self.bg, (0, 0))
        self._draw_header(screen)
        self._draw_player_panels(screen)
        self._draw_instructions(screen)
        self._draw_action_button(screen)
        self.back_button.draw(screen)

    def _draw_header(self, screen: pygame.Surface) -> None:
        cx = config.SCREEN_WIDTH // 2
        title_surf = self.host_font.render("MULTIPLAYER LOBBY", True, config.COLOR_BLACK)
        subtitle_surf = self.large_font.render(self.lobby_name, True, config.COLOR_BLACK)
        screen.blit(title_surf, title_surf.get_rect(center=(cx, 32)))
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(cx, 56)))

    def _draw_player_panels(self, screen: pygame.Surface) -> None:
        for idx, player in enumerate(list(self.players_list.values())[:2]):
            x, y = self._panel_position(idx)
            self._draw_player_panel(screen, player, x, y)

    def _draw_instructions(self, screen: pygame.Surface) -> None:
        if not self.players_list:
            return
        lines = [
            "Arrow Keys / WASD: Change Color",
            "Up/Down or W/S: Change Hat",
            "Q/E: Change Bomb   R/F: Change Explosion",
        ]
        base_y = config.SCREEN_HEIGHT - 160
        
        # Create semi-transparent black background for instructions
        text_surfaces = [self.info_font.render(line, True, config.COLOR_WHITE) for line in lines]
        max_width = max(surf.get_width() for surf in text_surfaces)
        total_height = len(lines) * 22 + 10
        
        # Calculate background position
        bg_x = (config.SCREEN_WIDTH - max_width) // 2 - 10
        bg_y = base_y - 15
        bg_width = max_width + 20
        bg_height = total_height
        
        # Draw semi-transparent black background
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))
        screen.blit(bg_surface, (bg_x, bg_y))
        
        # Draw instruction text on top
        for i, surf in enumerate(text_surfaces):
            screen.blit(surf, surf.get_rect(center=(config.SCREEN_WIDTH // 2, base_y + i * 22)))

    def _draw_action_button(self, screen: pygame.Surface) -> None:
        if self.is_host:
            can_start = (
                len(self.players_list) >= 2
                and all(p.is_ready for p in self.players_list.values())
            )
            self.start_button.set_visible(can_start)
            self.start_button.set_enabled(can_start)
            self.start_button.draw(screen)
        else:
            self.ready_button.draw(screen)

    def _draw_player_panel(
        self, screen: pygame.Surface, player: PlayerData, x: int, y: int
    ) -> None:
        accent = self.available_colors[player.color_index]

        # Background panel
        panel_surf = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (18, 22, 34, 228), panel_surf.get_rect(), border_radius=18)
        pygame.draw.rect(panel_surf, (*accent, 200), panel_surf.get_rect(), width=2, border_radius=18)
        screen.blit(panel_surf, (x, y))

        # Top accent glow
        glow = pygame.Surface((PANEL_WIDTH, 8), pygame.SRCALPHA)
        half = PANEL_WIDTH / 2
        for gx in range(PANEL_WIDTH):
            alpha = int(80 * (1 - abs(gx - half) / half))
            pygame.draw.line(glow, (*accent, alpha), (gx, 0), (gx, 7))
        screen.blit(glow, (x, y))

        # Player name
        name_text = player.name if len(player.name) <= 14 else player.name[:14] + "…"
        name_surf = self.skin_font.render(name_text, True, config.COLOR_WHITE)
        screen.blit(name_surf, name_surf.get_rect(center=(x + PANEL_WIDTH // 2, y + 24)))

        # Character preview
        preview_y = y + 100
        if player.color_index not in self.tinted_idle_images:
            self._cache_tinted_frames(player.color_index)
        frames = self.tinted_idle_images.get(player.color_index, ())
        frame  = frames[self.idle_index] if frames else self.idle_frames[self.idle_index]

        circle = pygame.Surface((92, 92), pygame.SRCALPHA)
        pygame.draw.circle(circle, (*accent, 40), (46, 46), 46)
        screen.blit(circle, (x + PANEL_WIDTH // 2 - 46, preview_y - 40))
        preview_rect = frame.get_rect(center=(x + PANEL_WIDTH // 2, preview_y))
        screen.blit(frame, preview_rect)

        # Hat overlay
        if player.final_hat != "None":
            hat_img = self.hat_images.get(player.final_hat)
            if hat_img:
                screen.blit(hat_img, (preview_rect.centerx - hat_img.get_width() // 2, preview_rect.top - 10))

        # Stats rows
        rows = [
            ("Color",     COLOR_NAMES.get(self.available_colors[player.color_index], "?"), None, self.available_colors[player.color_index]),
            ("Hat",       player.final_hat,         self.hat_thumbs.get(player.final_hat),   None),
            ("Bomb",      player.final_bomb,        self.bomb_thumbs.get(player.final_bomb), None),
            ("Explosion", player.final_explosion,   self.explosion_thumbs.get(player.final_explosion), None),
        ]
        row_y = y + 150
        for label, value, thumb, chip_color in rows:
            row_rect = pygame.Rect(x + 10, row_y, PANEL_WIDTH - 20, 27)
            pygame.draw.rect(screen, (12, 14, 22), row_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255, 14), row_rect, width=1, border_radius=8)
            screen.blit(self.small_font.render(label, True, config.TEXT_MUTED), (row_rect.x + 8,   row_rect.y + 5))
            if thumb is not None:
                screen.blit(thumb, (row_rect.x + 68, row_rect.y - 4))
            elif chip_color is not None:
                pygame.draw.circle(screen, chip_color, (row_rect.x + 85, row_rect.y + 13), 8)
            screen.blit(self.small_font.render(value, True, config.TEXT_PRIMARY), (row_rect.x + 104, row_rect.y + 5))
            row_y += 31

        # Ready / YOU indicator
        if not self.my_player:
            return
        is_me        = player.name == self.my_player.name
        status_color = config.COLOR_LIGHT_GREEN if player.is_ready else config.COLOR_RED
        status_text  = "YOU" if is_me else "READY"
        status_surf  = self.small_font.render(status_text, True, status_color)
        screen.blit(status_surf, status_surf.get_rect(center=(x + PANEL_WIDTH // 2, y + PANEL_HEIGHT - 20)))

    @staticmethod
    def _panel_position(index: int) -> Tuple[int, int]:
        x = 80 if index == 0 else config.SCREEN_WIDTH - 280
        return x, 120