import json
import os
import time

import pygame

import config
import socket

from states.state import State
from managers.music_manager import MusicManager
from managers.state_manager import StateManager


class MultiplayerLobby(State):
    def __init__(self, game, is_host=False, player_name="Server Host", host_ip="127.0.0.1"):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Multiplayer Lobby")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))

        self.AUTH = "PLEASEWORK"

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.01)

        self.acknowledged_players = set()
        self.state_change_sent = False

        self.player_name = player_name
        self.is_host = is_host
        self.players = []
        if self.is_host:
            self.players = [("Server Host", ('127.0.0.1', 1111))]

        self.host_ip = host_ip
        self.port = 9999

        if self.is_host:
            self.host_ip = self.get_local_ip()
            self.socket.bind((self.host_ip, self.port))
            self.local_port = 1111
        else:
            self.local_port = None

        # Buttons
        self.start_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT - 120,
            config.BUTTON_WIDTH,
            config.BUTTON_HEIGHT,
            "Start Game"
        )
        self.back_button = Button(
            20, 20,
            config.BUTTON_WIDTH // 1.5,
            config.BUTTON_HEIGHT // 1.5,
            "Back"
        )

        self.request_cooldown = 1
        self.last_request_time = 0

        print(f"your local ip {self.get_local_ip()}")

    @staticmethod
    def get_local_ip():
        try:
            # Create a dummy socket (doesn't send data)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google's DNS
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            return f"Could not determine local IP: {e}"

    def listen_for_joins(self):
        try:
            packet, addr = self.socket.recvfrom(1024)
            packet = json.loads(packet.decode('utf-8'))
            if not packet.get('AUTH',"UNKNOWN") == self.AUTH:
                return
            if packet['type'] == 'JOIN':
                for player in self.players:
                    address = player[1]
                    if addr == address:
                        print("Player Already Connected")
                        return
                username = packet['data'].get('name', "UNKNOWN")
                print(f"{username} joined from {addr}")
                self.players.append((username, addr))

                # Send updated player list
                player_list_packet = {
                    'type': 'PLAYER_LIST',
                    'data': {'player_list': self.players}
                }
                for _, address in self.players[1:]:
                    self.socket.sendto(json.dumps(player_list_packet).encode('utf-8'), address)
            elif packet['type'] == 'LEAVE':
                self.players = [p for p in self.players if p[1] != addr]
                for _, address in self.players:
                    if address[1] == 1111:
                        return
                    player_list_packet = {
                        'type': 'PLAYER_LIST',
                        'data': {'player_list': self.players}
                    }
                    self.socket.sendto(json.dumps(player_list_packet).encode('utf-8'), address)
        except socket.timeout:
            pass

    def send_join_request(self):
        current_time = time.time()
        if current_time - self.last_request_time >= self.request_cooldown:
            packet = {
                "AUTH": self.AUTH,
                "type": "JOIN",
                'data': {"name": self.player_name},
            }
            message = json.dumps(packet).encode('utf-8')
            self.last_request_time = current_time
            if self.local_port is None:
                # Send a JOIN packet to the host
                self.socket.sendto(message, (self.host_ip, self.port))
                self.local_port = self.socket.getsockname()[1]
            else:
                for player in self.players:
                    port = player[1][1]
                    if self.local_port == port:
                        break
                else:
                    print("Trying to connect")
                    self.socket.sendto(message, (self.host_ip, self.port))

    def update_player_list(self):
        try:
            packet, addr = self.socket.recvfrom(1024)
            packet = json.loads(packet.decode('utf-8'))
            print(packet)
            if packet['type'] == "PLAYER_LIST":
                self.players = []
                for p in packet['data']['player_list']:
                    username, addr = p
                    self.players.append((username, addr))
        except socket.timeout:
            pass
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received from: {e}")

    def handle_events(self, event):
        if self.back_button.is_clicked():
            leave_packet = {
                'AUTH': self.AUTH,
                'type': 'LEAVE'
            }
            self.socket.sendto(json.dumps(leave_packet).encode('utf-8'), (self.host_ip, self.port))
            self.exit_state()
            self.socket.close()

        elif self.start_button.is_clicked():
            self.broadcast_state_change("MultiplayerMapSelector")
            self.exit_state()
            self.state_manager.change_state("MultiplayerMapSelector", self)

    def update(self):
        self.handle_network_packets()
        if self.is_host:
            self.listen_for_joins()
        else:
            self.send_join_request()
        self.update_player_list()

    def handle_network_packets(self):
        if self.is_host:
            try:
                packet, address = self.socket.recvfrom(1024)
                packet = json.loads(packet.decode('utf-8'))
                if not packet.get('AUTH','UNKNOWN') == self.AUTH:
                    return
                if packet['type'] == "ACK_STATE_CHANGE":
                    self.acknowledged_players.add(address)
            except socket.timeout:
                pass
        else:
            try:
                packet, address = self.socket.recvfrom(1024)
                packet = json.loads(packet.decode('utf-8'))
                if packet['type'] == 'STATE_CHANGE':
                    if packet['data'].get('state', 'UNKNOWN') == 'MultiplayerMapSelector':
                        # Send ACK to host
                        ack_packet = {
                            'AUTH': self.AUTH,
                            'type': 'ACK_STATE_CHANGE'
                        }
                        self.socket.sendto(json.dumps(ack_packet).encode('utf-8'), (self.host_ip, self.port))
                        self.state_manager.change_state("MultiplayerMapSelector", self)
            except socket.timeout:
                pass

    def broadcast_state_change(self, new_state):
        state_change_packet = {
            'type': 'STATE_CHANGE',
            'data': {'state': new_state}
        }
        message = json.dumps(state_change_packet).encode('utf-8')
        self.state_change_sent = True
        self.acknowledged_players = set()

        # Try to send up to 5 times, every 0.5 seconds
        for _ in range(5):
            for username, address in self.players:
                if address[1] == 1111:  # skip host
                    continue
                if address not in self.acknowledged_players:
                    self.socket.sendto(message, address)

            time.sleep(0.5)

            if len(self.acknowledged_players) == len(self.players) - 1:
                print("All clients acknowledged state change.")
                break
        else:
            print("Not all clients acknowledged the state change.")

    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))

        # Title
        self.game.draw_text(screen, "Multiplayer Lobby", config.COLOR_BLACK, config.SCREEN_WIDTH // 2, 60)

        # IP Label
        ip_text = f"Share this IP with friends: {self.host_ip}"
        ip_surface = pygame.font.Font(None, config.FONT_SIZE).render(ip_text, True, config.TEXT_COLOR)
        ip_rect = ip_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 100))
        screen.blit(ip_surface, ip_rect)

        # Draw player list
        y_start = 150
        for index, player in enumerate(self.players):
            player_name = player[0]
            if self.player_name == "Server Host" and player_name == "Server Host":
                player_name = 'Server Host (You)'
            elif self.player_name == player_name:
                player_name = f'{self.player_name} (You)'
            else:
                player_name = player_name

            text_surface = pygame.font.Font(None, config.FONT_SIZE).render(f'{index + 1}. {player_name}', True,
                                                                           config.TEXT_COLOR)
            text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, y_start + index * 40))
            screen.blit(text_surface, text_rect)

        # Draw buttons
        if self.is_host:
            self.start_button.draw(screen)
        self.back_button.draw(screen)


class Button:
    def __init__(self, x, y, width, height, text, action=None):
        """Initialize button with position, size, and text."""
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.action = action

    def draw(self, screen):
        """Draw the button on screen."""
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, config.BUTTON_HOVER_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)
        else:
            pygame.draw.rect(screen, config.BUTTON_COLOR, self.rect, border_radius=config.BUTTON_RADIUS)

        # Render the text on the button
        text_surface = self.font.render(self.text, True, config.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self):
        """Check if the button is clicked."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
