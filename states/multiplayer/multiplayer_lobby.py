import os
import socket
import pygame
import config
from typing import Tuple, Any, Dict, Optional
from dataclasses import dataclass, asdict
from states.general.state import State
from custom_classes.button import Button
from managers.music_manager import MusicManager
from managers.state_manager import StateManager
from managers.network_manager import NetworkManager

# Typing hints
Addr = Tuple[str, int]
Packet = Dict[str, Any]

# CONSTANTS
COLOR_NAMES = {
    config.WHITE_PLAYER: "White", config.BLACK_PLAYER: "Black",
    config.RED_PLAYER: "Red", config.BLUE_PLAYER: "Blue",
    config.DARK_GREEN_PLAYER: "Green", config.LIGHT_GREEN_PLAYER: "Light Green",
    config.YELLOW_PLAYER: "Yellow", config.PINK_PLAYER: "Pink",
    config.ORANGE_PLAYER: "Orange", config.PURPLE_PLAYER: "Purple",
    config.BROWN_PLAYER: "Brown", config.CYAN_PLAYER: "Cyan"
}

AVAILABLE_HATS_KEYS = list(config.AVAILABLE_HATS.keys())


PANEL_WIDTH = 200
PANEL_HEIGHT = 280
LOBBY_SCOPE = 'MultiplayerLobby'
LOBBY_DISCOVERY_SCOPE = 'LobbyDiscovery'
MAP_SELECTOR_SCOPE = 'MultiplayerMapSelector'
TEST_FIELD_SCOPE = 'MultiplayerTestField'
READY_PACKET_TYPE = 'READY_TOGGLE'
SKIN_PACKET_TYPE = 'SKIN_UPDATE'
STATE_CHANGE_PACKET_TYPE = 'STATE_CHANGE'
PLAYER_LIST_PACKET_TYPE = 'PLAYER_LIST'
JOIN_PACKET_TYPE = 'JOIN'
LEAVE_PACKET_TYPE = 'LEAVE'
HOST_OFFER_PACKET_TYPE = 'HOST_OFFER'
SAME_DATA_PACKET_TYPE = 'SAME_DATA'

@dataclass
class PlayerData:
    name : str
    addr : Tuple[str, int]
    is_host: bool
    is_ready: bool = False
    selection_index: int = 0
    vote_index: int | None = None
    color_index: int = 0  
    hat_index: int = 0 
    final_color: Tuple[int, int, int] = (0, 0, 0)
    final_hat: str = "None"


class MultiplayerLobby(State):
    def __init__(self, game, player_name, network_manager: NetworkManager, players_list=None, *, is_host=False, lobby_name=''):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Multiplayer Lobby")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)
        self.network_manager = network_manager

        # data from input
        self.player_name = player_name
        self.is_host = is_host
        self.lobby_name = lobby_name.strip() if isinstance(lobby_name, str) else ''
        if not self.lobby_name:
            self.lobby_name = f"{self.player_name}'s Lobby"

        self.leave_seq = None
        self.leave_target_addr: Addr | None = None
        self.pending_state_change: str | None = None
        self.state_change_seq_by_addr: Dict[Addr, int] = {}
        self.host_setup_failed = False
        self.host_setup_error = ''
        
        self.players_list: Dict[str, PlayerData] = self.convert_player_list_to_Player(players_list) if players_list else {}
        self.max_players = 2
        
        # Animation
        self.last_idle_update = pygame.time.get_ticks()
        self.idle_index = 0
        self.idle_fps = 4

        # Shared text surfaces
        self.skin_font = pygame.font.Font("CaveatBrush-Regular.ttf", 20)
        self.info_font = pygame.font.Font("CaveatBrush-Regular.ttf", 18)
        self.small_font = pygame.font.Font("CaveatBrush-Regular.ttf", 16)
        self.host_font = pygame.font.Font(None, 24)

        # Buttons
        self.back_button = Button(20, 20, config.BUTTON_WIDTH // 1.2, config.BUTTON_HEIGHT, "Back", font='CaveatBrush-Regular.ttf', button_color=config.COLOR_BEIGE)

        if self.is_host:
            resolved_ip = self.get_local_ip()
            self.host_ip = resolved_ip if resolved_ip else "127.0.0.1"
            # Bind to all interfaces so LAN broadcast discovery can reach the host.
            try:
                self.network_manager.socket.bind(("", config.SERVER_PORT))
            except OSError as e:
                self.host_setup_failed = True
                self.host_setup_error = (
                    f"Could not start lobby on port {config.SERVER_PORT}. "
                    "Another game instance may already be running."
                )
                print(f'[LOBBY ERROR] {self.host_setup_error} ({e})')

            if not resolved_ip:
                print('[LOBBY WARNING] Could not resolve a LAN IP, falling back to localhost (127.0.0.1).')

            host_addr = (self.host_ip, config.SERVER_PORT)
            print(f'[LOBBY CREATED] Host IP: {self.host_ip}, Lobby Name: {self.lobby_name}')
            self.players_list[player_name] = PlayerData(player_name, host_addr, is_host=True, is_ready=True)
            
            self.start_button = Button(
                config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
                config.SCREEN_HEIGHT - 120,
                config.BUTTON_WIDTH + 10,
                config.BUTTON_HEIGHT + 10,
                'Start Game',
                font='CaveatBrush-Regular.ttf',
                button_color=config.COLOR_BEIGE,
            )
            
            self.start_button.set_visible(False)
            self.start_button.set_enabled(False)
        else:
            self.ready_button = Button(
                config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
                config.SCREEN_HEIGHT - 120,
                config.BUTTON_WIDTH + 10,
                config.BUTTON_HEIGHT + 10,
                'Ready',
                font='CaveatBrush-Regular.ttf',
                button_color=config.COLOR_BEIGE,
            )
            
            self.ready_button.set_visible(True)
            self.ready_button.set_enabled(True)

        self.my_player = self.players_list.get(self.player_name,None)
        if self.my_player is None:
            raise Exception('my_player is None in MultiplayerLobby')

        # --- Skin Selection Assets ---
        self.load_skin_assets()
        self.tinted_idle_images: Dict[int, Tuple[pygame.Surface, ...]] = {}
        self._load_tinted_images()
        self.my_player.final_color = self.available_colors[self.my_player.color_index]
        self.my_player.final_hat = AVAILABLE_HATS_KEYS[self.my_player.hat_index]

    # ---------------- SKIN ASSETS ----------------
    def load_skin_assets(self):
        self.available_colors = config.AVAILABLE_COLORS
        # Load idle frames for player preview
        self.idle_frames = []
        for i in range(3):
            frame = pygame.image.load(
                os.path.join(self.game.photos_dir, "player_animations", f"p_1_idle_{i}.png")
            ).convert_alpha()
            w, h = frame.get_size()
            frame = pygame.transform.scale(frame, (w * 4, h * 4))
            self.idle_frames.append(frame)
        
        # Load hat images
        self.hat_images = {}
        for hat in config.HATS:
            name = hat["name"]
            file = hat["file"]
            
            if file is None:
                self.hat_images[name] = 'None'
                continue
                
            path = os.path.join(self.game.photos_dir, "../assets/player_hats", file)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                # Scale for preview
                img = pygame.transform.smoothscale(img, (50, 50))
                self.hat_images[name] = img
            else:
                self.hat_images[name] = 'None'
        
    def _load_tinted_images(self, color_index: Optional[int] = None) -> None:
        # Cache tinted frames for a color to avoid recreating them on every render.
        if not self.players_list:
            return
        for player in self.players_list.values():
            active_color_index = color_index if color_index is not None else player.color_index
            if active_color_index in self.tinted_idle_images:
                continue
            tinted_images = []
            for idle_frame in self.idle_frames:
                color = self.available_colors[active_color_index]
                tinted_images.append(self.tint_image(idle_frame, color))
            self.tinted_idle_images[active_color_index] = tuple(tinted_images)

    def tint_image(self, image, color) -> pygame.Surface:
        tinted = image.copy()
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((*color, 255))
        tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        return tinted

    def update_idle_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_idle_update >= 1000 // self.idle_fps:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_update = now

    def _set_player_color(self, step: int) -> None:
        if not self.my_player:
            return

        taken_colors = {player.color_index for name, player in self.players_list.items() if name != self.player_name}
        new_color_index = self.my_player.color_index

        for _ in range(len(self.available_colors)):
            new_color_index = (new_color_index + step) % len(self.available_colors)
            if new_color_index not in taken_colors:
                self.my_player.color_index = new_color_index
                self.my_player.final_color = self.available_colors[new_color_index]
                self._load_tinted_images(new_color_index)
                self.broadcast_skin_update()
                return

    def _set_player_hat(self, step: int) -> None:
        if not self.my_player:
            return

        self.my_player.hat_index = (self.my_player.hat_index + step) % len(AVAILABLE_HATS_KEYS)
        self.my_player.final_hat = AVAILABLE_HATS_KEYS[self.my_player.hat_index]
        self.broadcast_skin_update()

    def _broadcast_packet_to_peers(self, packet_type: str, data: dict[str, Any], scope: str = LOBBY_SCOPE) -> None:
        if not self.my_player:
            return

        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            self.network_manager.send_packet(player.addr, packet_type, data, scope)

    def _send_packet_to_host(self, packet_type: str, data: dict[str, Any], scope: str = LOBBY_SCOPE) -> None:
        for player in self.players_list.values():
            if player.is_host:
                self.network_manager.send_packet(player.addr, packet_type, data, scope)
                return

    def _player_panel_position(self, index: int) -> Tuple[int, int]:
        panel_x = 80 if index == 0 else config.SCREEN_WIDTH - 280
        return panel_x, 120

    def _draw_instructions(self, screen) -> None:
        if not self.players_list:
            return

        inst_y = config.SCREEN_HEIGHT - 160
        inst_lines = ["Arrow Keys / WASD: Change Color", "Up/Down or W/S: Change Hat"]

        for i, line in enumerate(inst_lines):
            inst_surf = self.info_font.render(line, True, (80, 60, 40))
            inst_rect = inst_surf.get_rect(center=(config.SCREEN_WIDTH // 2, inst_y + i * 22))
            screen.blit(inst_surf, inst_rect)

    def _draw_buttons(self, screen) -> None:
        if self.is_host:
            all_ready = all(player.is_ready for player in self.players_list.values())
            can_start = all_ready and len(self.players_list) >= 2
            self.start_button.set_visible(can_start)
            self.start_button.set_enabled(can_start)
            self.start_button.draw(screen)
            return

        self.ready_button.draw(screen)

    # ---------------- NETWORK ----------------
    @staticmethod
    def get_local_ip() -> Optional[str]:
        try:
            # Create a dummy socket (doesn't send data)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google's DNS
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return None

    def _handle_failed_host_setup(self) -> bool:
        if not self.host_setup_failed:
            return False

        print(f'[LOBBY EXIT] {self.host_setup_error} Returning to MainMenu.')
        self.host_setup_failed = False
        self.exit_state()
        self.state_manager.change_state('MainMenu')
        return True
            
    def convert_player_list_to_dict(self, player_list: Dict[str, PlayerData]) -> Dict[str, dict]:
        return {player_name: asdict(player_data) for player_name, player_data in player_list.items()}

    def convert_player_list_to_Player(self, player_list: Dict[str, dict]) -> Dict[str, PlayerData]:
        player_list_converted: Dict[str, PlayerData] = {}
        for player_name, player_data in player_list.items():
            data = dict(player_data)
            data['addr'] = tuple(data['addr'])
            player_list_converted[player_name] = PlayerData(**data)
        return player_list_converted
    
    # ---------------- INPUTS ----------------
    def handle_events(self, event):
        if not self.my_player:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.rect.collidepoint(event.pos):
                packet_data = {'player_name': self.my_player.name}
                if self.my_player.is_host:
                    peer = self._get_peer_player()
                    if not peer:
                        self.network_manager.close_socket()
                        self.exit_state()
                        self.state_manager.change_state('MainMenu')
                        return
                    self.leave_target_addr = peer.addr
                    self.leave_seq = self.network_manager.send_packet(peer.addr, LEAVE_PACKET_TYPE, packet_data, LOBBY_SCOPE)
                else:
                    host_player = next((player for player in self.players_list.values() if player.is_host), None)
                    if not host_player:
                        self._pop_to_input_popup()
                        return
                    self.leave_target_addr = host_player.addr
                    self.leave_seq = self.network_manager.send_packet(host_player.addr, LEAVE_PACKET_TYPE, packet_data, LOBBY_SCOPE)
                return

            if self.is_host and self.start_button.rect.collidepoint(event.pos):
                self.begin_state_change(MAP_SELECTOR_SCOPE)
                return

            if (not self.is_host) and self.ready_button.rect.collidepoint(event.pos):
                self.my_player.is_ready = not self.my_player.is_ready
                packet_data = {'player_name': self.my_player.name}
                self._send_packet_to_host(READY_PACKET_TYPE, packet_data)
                return

        # Skin selection controls
        if event.type == pygame.KEYDOWN and self.player_name in self.players_list:
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                self._set_player_color(-1)
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                self._set_player_color(1)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self._set_player_hat(-1)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self._set_player_hat(1)

    # ---------------- Network ----------------
    def handle_network_packets(self):
        while True:
            poll_data = self.network_manager.poll()
            if not poll_data:
                break
            self.handle_packet(poll_data)

    def handle_packet(self, poll_data: Tuple[Packet, Addr]) -> None:
        packet, addr = poll_data
        packet_scope = packet.get('scope')
        packet_type = packet.get('type')
        packet_data = packet.get('data')

        if packet_scope == LOBBY_DISCOVERY_SCOPE:
            if packet_type == 'DISCOVER_HOSTS':
                self._handle_discover_hosts_packet(addr)
            return

        if packet_scope != LOBBY_SCOPE:
            if packet_scope in {MAP_SELECTOR_SCOPE, TEST_FIELD_SCOPE}:
                return
            return

        if not packet_type or not packet_data:
            raise Exception(f'Invalid packet (data or type missing): packet:{packet} from {addr}')
        
        if packet_type == JOIN_PACKET_TYPE:
            self._handle_join_packet(packet_data, addr)
        elif packet_type == LEAVE_PACKET_TYPE:
            self._handle_leave_packet(packet_data, addr)
        elif packet_type == PLAYER_LIST_PACKET_TYPE:
            self._handle_player_list_packet(packet_data, addr)
        elif packet_type == STATE_CHANGE_PACKET_TYPE:
            self._handle_state_change_packet(packet_data, addr)
        elif packet_type == SKIN_PACKET_TYPE:
            self._handle_skin_update_packet(packet_data, addr)
        elif packet_type == READY_PACKET_TYPE:
            self._handle_ready_toggle_packet(packet_data, addr)

    def _handle_discover_hosts_packet(self, addr: Addr) -> None:
        if not self.is_host:
            return
        data = {
            'host_name': self.player_name,
            'lobby_name': self.lobby_name,
            'current_players': len(self.players_list),
            'max_players': self.max_players,
        }
        self.network_manager.send_packet(addr, HOST_OFFER_PACKET_TYPE, data, LOBBY_DISCOVERY_SCOPE)

    def _handle_skin_update_packet(self, packet_data, addr):
        player_name = packet_data.get('player_name')
        if player_name not in self.players_list:
            print(f'[SKIN_UPDATE ERROR] Unknown player {player_name} from {addr}')
            return
        player = self.players_list[player_name]
        player.color_index = packet_data.get('color_index', 0)
        player.hat_index = packet_data.get('hat_index', 0)
        player.final_color = self.available_colors[player.color_index]
        player.final_hat = AVAILABLE_HATS_KEYS[player.hat_index]
        print(f'[SKIN_UPDATE] {player_name} updated skin from {addr}')

    def _handle_state_change_packet(self, packet_data, addr):
        if not self.my_player:
            return
        state = packet_data.get('state')
        print(f'[STATE_CHANGE] state: {state} from {addr}')
        self.exit_state()
        self.state_manager.change_state(MAP_SELECTOR_SCOPE, self.players_list, self.network_manager, self.player_name)

    def _handle_player_list_packet(self, packet_data, addr) -> None:
        player_list = packet_data.get('player_list')
        self.players_list = self.convert_player_list_to_Player(player_list)
        print(f'[PLAYER_LIST UPDATE] player_list: {self.players_list}')

    def _handle_leave_packet(self, packet_data, addr) -> None:
        player_name = packet_data.get('player_name')
        print(f'{player_name} left from {addr}')
        if player_name in self.players_list:
            del self.players_list[player_name]

        self._pop_to_input_popup()

    def _pop_to_lobby_selector(self) -> None:
        while self.game.state_stack and self.game.state_stack[-1].__class__.__name__ != 'MultiplayerSelector':
            self.game.state_stack[-1].exit_state()

        
    def _broadcast_player_list(self) -> None:
        if self.my_player is None:
            return
        data = {'player_list': self.convert_player_list_to_dict(self.players_list)}
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            print(f'Sending PLAYER_LIST to {player.addr}')
            self.network_manager.send_packet(player.addr, PLAYER_LIST_PACKET_TYPE, data, LOBBY_SCOPE)

    def _handle_join_packet(self, packet_data, addr) -> None:
        player_name = packet_data.get('player_name', 'UNKNOWN')
            
        if (len(self.players_list) >= self.max_players):
            print(f'{player_name} tried to join from {addr} but the lobby is full!')
            return
        
        for name in self.players_list:
            if (name == player_name):
                print(f'{player_name} tried to join from {addr} player with the same name already joined!')
                data = {'msg' : f'Player with username {player_name} is already in the lobby!'}
                self.network_manager.send_packet(addr, SAME_DATA_PACKET_TYPE, data, LOBBY_SCOPE)
                return
        for player in self.players_list.values():
            if (addr == (player.addr)):
                print(f'Address: {addr} is already in player_list')
                return
        
        # Create new player with unique color
        new_player = PlayerData(player_name, (addr), is_host=False)
        
        # Assign first available color
        taken_colors = [p.color_index for p in self.players_list.values()]
        for color_idx in range(len(self.available_colors)):
            if color_idx not in taken_colors:
                new_player.color_index = color_idx
                break
        
        self.players_list[player_name] = new_player
        print(f"{player_name} joined from {addr}")

        self._broadcast_player_list()

    def _handle_ready_toggle_packet(self, packet_data, addr) -> None:
        player_name = packet_data.get('player_name')
        if player_name not in self.players_list:
            print(f'[READY_TOGGLE ERROR] Unknown player {player_name} from {addr}')
            return
        player = self.players_list[player_name]
        player.is_ready = not player.is_ready
        print(f'[READY_TOGGLE] {player_name} is_ready: {player.is_ready} from {addr}')

    def broadcast_skin_update(self) -> None:
        if not self.my_player:
            return
        data = {
            'player_name': self.my_player.name,
            'color_index': self.my_player.color_index,
            'hat_index': self.my_player.hat_index
        }
        self._broadcast_packet_to_peers(SKIN_PACKET_TYPE, data)

    def broadcast_state_change(self, new_state: str) -> Dict[Addr, int]:
        if not self.my_player:
            return {}
        data = {'state' : new_state}
        seq_by_addr: Dict[Addr, int] = {}
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue
            seq = self.network_manager.send_packet(player.addr, STATE_CHANGE_PACKET_TYPE, data, LOBBY_SCOPE)
            seq_by_addr[player.addr] = seq
        return seq_by_addr

    def begin_state_change(self, new_state: str) -> None:
        if not self.my_player or not self.my_player.is_host:
            return
        if self.pending_state_change:
            return

        self.pending_state_change = new_state
        self.state_change_seq_by_addr = self.broadcast_state_change(new_state)

        # No peers to wait for.
        if not self.state_change_seq_by_addr:
            self._complete_pending_state_change()

    def _complete_pending_state_change(self) -> None:
        if not self.pending_state_change:
            return

        new_state = self.pending_state_change
        self.pending_state_change = None
        self.state_change_seq_by_addr.clear()
        self.exit_state()
        self.state_manager.change_state(new_state, self.players_list, self.network_manager, self.player_name)

    def check_state_change_acks(self) -> None:
        if not self.pending_state_change:
            return

        all_acked = all(
            self.network_manager.get_completed_seq(addr, seq=seq)
            for addr, seq in self.state_change_seq_by_addr.items()
        )
        if all_acked:
            self._complete_pending_state_change()

    def check_leave_seq(self) -> None:
        if self.leave_seq and self.leave_target_addr and self.network_manager.get_completed_seq(self.leave_target_addr, seq=self.leave_seq):
            print(f'[LEFT LOBBY] {self.my_player.name} has left the lobby.')
            self.network_manager.close_socket()
            self.exit_state()
            self.state_manager.change_state('MainMenu')
    # ---------------- Update ----------------
    def update(self) -> None:
        if self._handle_failed_host_setup():
            return
        self.check_leave_seq()
        self.check_state_change_acks()
        self.update_idle_animation()
        self.handle_network_packets()
        self.network_manager.update()
    # ---------------- Render ---------------
    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))

        # Title
        self.game.draw_text(screen, self.lobby_name, config.COLOR_BLACK, config.SCREEN_WIDTH // 2, 30)

        # Draw player skin selectors
        player_list = list(self.players_list.values())
        
        for idx, player in enumerate(player_list):
            if idx >= 2:  # Max 2 players
                break
            panel_x, panel_y = self._player_panel_position(idx)
            self.draw_player_panel(screen, player, panel_x, panel_y)

        self._draw_instructions(screen)
        self._draw_buttons(screen)

        self.back_button.draw(screen)

    def draw_player_panel(self, screen, player: PlayerData, x, y):
        """Draw individual player's skin selection panel"""
        
        # Panel background
        panel_surf = pygame.Surface((PANEL_WIDTH, PANEL_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (15, 20, 30, 200), panel_surf.get_rect(), border_radius=15)
        pygame.draw.rect(panel_surf, (*config.MENU_OUTLINE, 200), panel_surf.get_rect(), width=2, border_radius=15)
        screen.blit(panel_surf, (x, y))
        
        # Player name
        name_color = config.COLOR_WHITE
        name_text = player.name if len(player.name) <= 12 else player.name[:12] + "..."
        name_surf = self.skin_font.render(name_text, True, name_color)
        name_rect = name_surf.get_rect(center=(x + PANEL_WIDTH // 2, y + 130))
        screen.blit(name_surf, name_rect)
        
        # Player preview with color and hat
        preview_y = y + 60
        if self.tinted_idle_images.get(player.color_index) is None:
            self._load_tinted_images(player.color_index)
        tinted_frames = self.tinted_idle_images.get(player.color_index)

        if tinted_frames:
            frame = tinted_frames[self.idle_index]  
        else:   
            frame = self.idle_frames[self.idle_index]
    
        # Tint player sprite
        preview_rect = frame.get_rect(center=(x + PANEL_WIDTH // 2, preview_y))
        screen.blit(frame, preview_rect)
        
        # Draw hat on player
        hat_def = AVAILABLE_HATS_KEYS[player.hat_index]
        if hat_def != "None":
            hat_img = self.hat_images.get(hat_def)
            if hat_img:
                # Adjust hat position
                hat_x = preview_rect.centerx - hat_img.get_width() // 2
                hat_y = preview_rect.top - 10
                screen.blit(hat_img, (hat_x, hat_y))
                
        color = self.available_colors[player.color_index]
        color_name = COLOR_NAMES.get(color, "Unknown")
        color_surf = self.info_font.render(f"Color: {color_name}", True, (255, 255, 255))
        color_rect = color_surf.get_rect(center=(x + PANEL_WIDTH // 2, y + 160))
        screen.blit(color_surf, color_rect)

        # Hat name
        hat_name_surf = self.info_font.render(f"Hat: {hat_def}", True, (255, 255, 255))
        hat_name_rect = hat_name_surf.get_rect(center=(x + PANEL_WIDTH // 2, y + 185))
        screen.blit(hat_name_surf, hat_name_rect)

        # Ready indicator
        if not self.my_player:
            return
        
        ready_color  = config.COLOR_LIGHT_GREEN if player.is_ready else config.COLOR_RED
        if player.name == self.my_player.name:
            ready_surf = self.small_font.render("(You)", True, ready_color)
        else:
            ready_surf = self.small_font.render("Ready", True, ready_color)
        ready_rect = ready_surf.get_rect(center=(x + PANEL_WIDTH // 2, y + 215))
        screen.blit(ready_surf, ready_rect)