import pygame
import config
import socket
import time
from states.general.state import State
from managers.state_manager import StateManager
from custom_classes.button import Button
from managers.network_manager import NetworkManager


class InputPopup(State):
    def __init__(self, game, network_manager: NetworkManager, mode='join'):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: Multiplayer")
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.active_box = None
        self.mode = mode if mode in ('join', 'host') else 'join'
        self.is_host_mode = self.mode == 'host'

        self.network_manager = network_manager
        self.state_manager = StateManager(game)

        self.username_text = 'Test'
        self.lobby_name_text = ''
        self.discovered_hosts = {}
        self.selected_host_addr = None
        self.discovery_interval = 2.0
        self.discovery_timeout = 5.0
        self.last_discovery_sent = 0.0
        self.status_text = ''

        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.username_color = self.color_inactive
        self.lobby_name_color = self.color_inactive

        self.result = None
        self.list_row_height = 34
        self.status_time = 0
        self.status_duration = 6.0

        self._build_layout()
        self.request_lobby_discovery(force=True)

    def _build_layout(self):
        popup_width = config.SCREEN_WIDTH // 2 + 20
        popup_height = 290 if self.is_host_mode else 520
        popup_x = config.SCREEN_WIDTH // 4 - 10
        popup_y = config.SCREEN_HEIGHT // 3 - 50
        popup_y += 40 if self.is_host_mode else -30

        self.popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)

        input_width = config.SCREEN_WIDTH // 2
        input_x = (config.SCREEN_WIDTH - input_width) // 2
        input_top = popup_y + 55

        if self.is_host_mode:
            input_height = 32
            row_gap = 62
            self.username_rect = pygame.Rect(input_x, input_top, input_width, input_height)
            self.lobby_name_rect = pygame.Rect(input_x, input_top + row_gap, input_width, input_height)
            button_y = self.lobby_name_rect.bottom + 58
        else:
            input_height = 40
            self.username_rect = pygame.Rect(input_x, input_top, input_width, input_height)
            self.games_list_rect = pygame.Rect(input_x, input_top + 80, input_width, 170)
            button_y = popup_y + 380

        primary_label = "Host" if self.is_host_mode else "Join"
        self.join_button = Button(config.SCREEN_WIDTH // 2 - 110, button_y, 100, 40, primary_label,
                                  self.submit, font='CaveatBrush-Regular.ttf', button_color=config.COLOR_BEIGE)
        self.back_button = Button(config.SCREEN_WIDTH // 2 + 10, button_y, 100, 40, "Back",
                                  self.go_back, font='CaveatBrush-Regular.ttf', button_color=config.COLOR_BEIGE)

    def _set_status(self, message: str):
        self.status_text = message
        self.status_time = time.time()

    def submit(self):
        player_name = self.username_text.strip()

        if not player_name:
            self._set_status('Username is required.')
            return

        if self.is_host_mode:
            lobby_name = self.lobby_name_text.strip()
            if not lobby_name:
                self._set_status('Lobby name is required.')
                return

            existing_names = {
                host_data.get('lobby_name', '').strip().casefold()
                for host_data in self.discovered_hosts.values()
                if host_data.get('lobby_name')
            }
            if lobby_name.casefold() in existing_names:
                self._set_status('Lobby name already exists. Choose another one.')
                return

            host_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            host_network_manager = NetworkManager(host_socket)

            self.exit_state()
            self.state_manager.change_state('MultiplayerLobby', player_name, host_network_manager,
                                           is_host=True, lobby_name=lobby_name)
            return

        if self.selected_host_addr:
            self.send_join_request(player_name, self.selected_host_addr)
            self._set_status(f'Trying to join {self.selected_host_addr[0]}...')
        else:
            self._set_status('Select a discovered lobby.')

    def send_join_request(self, player_name, join_addr):
        self.network_manager.send_packet(join_addr, 'JOIN', {'player_name': player_name}, 'MultiplayerLobby')

    def request_lobby_discovery(self, force=False):
        now = time.time()
        if not force and now - self.last_discovery_sent < self.discovery_interval:
            return
        self.last_discovery_sent = now
        self.network_manager.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        packet_type = 'DISCOVER_HOSTS'
        data = {'player_name': self.username_text.strip() or 'Unknown Player'}
        scope = 'LobbyDiscovery'
        self.network_manager.send_packet(('255.255.255.255', config.SERVER_PORT), packet_type, data, scope)

    def _get_host_entries(self):
        entries = sorted(self.discovered_hosts.values(), key=lambda item: (item['lobby_name'], item['host_name']))
        return entries

    def _prune_discovered_hosts(self):
        now = time.time()
        stale = [
            addr_key
            for addr_key, host_data in self.discovered_hosts.items()
            if now - host_data['last_seen'] > self.discovery_timeout
        ]
        for addr_key in stale:
            del self.discovered_hosts[addr_key]
            if self.selected_host_addr == addr_key:
                self.selected_host_addr = None
        
        if not self.is_host_mode and not self.discovered_hosts and not self.status_text:
            self._set_status('No lobbies found. Searching...')

    def _select_host_at_position(self, pos):
        if not self.games_list_rect.collidepoint(pos):
            return
        entries = self._get_host_entries()
        relative_y = pos[1] - self.games_list_rect.y
        row = relative_y // self.list_row_height
        if 0 <= row < len(entries):
            selected = entries[row]
            self.selected_host_addr = selected['addr']

    def go_back(self):
        self.exit_state()

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mouse_click(event.pos)

        if event.type == pygame.KEYDOWN and self.active_box:
            if event.key == pygame.K_RETURN:
                self.submit()
            elif event.key == pygame.K_BACKSPACE:
                self._backspace_active_box()
            else:
                self._add_char_to_active_box(event.unicode)

        if self.join_button.is_clicked() and self.join_button.action:
            self.join_button.action()
        if self.back_button.is_clicked() and self.back_button.action:
            self.back_button.action()

    def _handle_mouse_click(self, pos):
        self._clear_active_box()

        if self.username_rect.collidepoint(pos):
            self.active_box = 'username'
            self.username_color = self.color_active
        elif self.is_host_mode and self.lobby_name_rect.collidepoint(pos):
            self.active_box = 'lobby_name'
            self.lobby_name_color = self.color_active
        elif not self.is_host_mode and self.games_list_rect.collidepoint(pos):
            self._select_host_at_position(pos)

    def _clear_active_box(self):
        self.active_box = None
        self.username_color = self.color_inactive
        self.lobby_name_color = self.color_inactive

    def _backspace_active_box(self):
        if self.active_box == 'username':
            self.username_text = self.username_text[:-1]
        elif self.active_box == 'lobby_name':
            self.lobby_name_text = self.lobby_name_text[:-1]

    def _add_char_to_active_box(self, char):
        if self.active_box == 'username':
            self.username_text += char
        elif self.active_box == 'lobby_name':
            self.lobby_name_text += char
            
    def handle_packet(self, packet_poll):
        packet, addr = packet_poll

        if not (packet.get('scope') in ['InputPopup', 'MultiplayerLobby', 'LobbyDiscovery']):
            return

        packet_type = packet.get('type')
        packet_data = packet.get('data')

        if not packet_type or not packet_data:
            raise Exception(f'Invalid packet (data or type missing): {packet} from {addr}')

        if packet_type == 'PLAYER_LIST':
            player_list = packet_data.get('player_list')
            if not player_list:
                return
            selected_lobby = self.discovered_hosts.get(self.selected_host_addr, {})
            lobby_name = selected_lobby.get('lobby_name', '')
            self.network_manager.register_peer(addr)
            self.exit_state()
            self.state_manager.change_state('MultiplayerLobby', self.username_text.strip(),
                                           self.network_manager, player_list, lobby_name=lobby_name)
            return

        if packet_type == 'HOST_OFFER':
            host_name = packet_data.get('host_name', 'Host')
            lobby_name = packet_data.get('lobby_name', f"{host_name}'s Lobby")
            current_players = packet_data.get('current_players', 0)
            max_players = packet_data.get('max_players', 0)

            host_addr = (addr[0], config.SERVER_PORT)
            self.discovered_hosts[host_addr] = {
                'addr': host_addr,
                'host_name': host_name,
                'lobby_name': lobby_name,
                'current_players': current_players,
                'max_players': max_players,
                'last_seen': time.time(),
            }
            if self.selected_host_addr is None:
                self.selected_host_addr = host_addr
            return

        if packet_type == 'SAME_DATA':
            self._set_status(packet_data.get('msg', 'Unable to join selected game.'))
            return        
    def update(self):
        while True:
            packet_poll = self.network_manager.poll()
            if not packet_poll:
                break
            self.handle_packet(packet_poll)

        if self.status_text and time.time() - self.status_time > self.status_duration:
            self.status_text = ''

        self.request_lobby_discovery()
        self._prune_discovered_hosts()
        self.network_manager.update()

    def _render_background(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), self.popup_rect, border_radius=8)

    def _render_labels(self, screen):
        username_label = self.font.render("Username:", True, config.TEXT_COLOR)
        screen.blit(username_label, (self.username_rect.x, self.username_rect.y - 25))

        if self.is_host_mode:
            lobby_name_label = self.font.render("Lobby Name:", True, config.TEXT_COLOR)
            screen.blit(lobby_name_label, (self.lobby_name_rect.x, self.lobby_name_rect.y - 25))
        else:
            address_label = self.font.render("Available Lobbies:", True, config.TEXT_COLOR)
            screen.blit(address_label, (self.games_list_rect.x, self.games_list_rect.y - 25))

    def _render_inputs(self, screen):
        pygame.draw.rect(screen, self.username_color, self.username_rect, 2, border_radius=5)
        username_surface = self.font.render(self.username_text, True, config.TEXT_COLOR)
        screen.blit(username_surface, (self.username_rect.x + 5, self.username_rect.y + 6))

        if self.is_host_mode:
            pygame.draw.rect(screen, self.lobby_name_color, self.lobby_name_rect, 2, border_radius=5)
            lobby_name_surface = self.font.render(self.lobby_name_text, True, config.TEXT_COLOR)
            screen.blit(lobby_name_surface, (self.lobby_name_rect.x + 5, self.lobby_name_rect.y + 6))
        else:
            pygame.draw.rect(screen, self.color_inactive, self.games_list_rect, 2, border_radius=5)

    def _render_lobby_list(self, screen):
        entries = self._get_host_entries()
        if not entries:
            return

        for idx, host_data in enumerate(entries):
            row_y = self.games_list_rect.y + idx * self.list_row_height
            if row_y + self.list_row_height > self.games_list_rect.bottom:
                break
            row_rect = pygame.Rect(self.games_list_rect.x + 2, row_y + 2, self.games_list_rect.width - 4, self.list_row_height - 4)
            bg_color = (80, 120, 160) if host_data['addr'] == self.selected_host_addr else (35, 35, 35)
            pygame.draw.rect(screen, bg_color, row_rect, border_radius=4)
            row_text = (
                f"{host_data['lobby_name']} | "
                f"{host_data['host_name']} ({host_data['current_players']}/{host_data['max_players']})"
            )
            row_surface = pygame.font.Font(None, 26).render(row_text, True, config.TEXT_COLOR)
            screen.blit(row_surface, (row_rect.x + 6, row_rect.y + 6))

    def _render_status(self, screen):
        if self.status_text:
            status_y = self.popup_rect.y + 10
            status_surface = pygame.font.Font(None, 22).render(self.status_text, True, (255, 200, 100))
            screen.blit(status_surface, (self.username_rect.x, status_y))

    def render(self, screen):
        self._render_background(screen)
        self._render_status(screen)
        self._render_labels(screen)
        self._render_inputs(screen)
        if not self.is_host_mode:
            self._render_lobby_list(screen)
        self.join_button.draw(screen)
        self.back_button.draw(screen)