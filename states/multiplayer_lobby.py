import json
import os
import socket
import pygame
import config
from typing import List, Tuple, Any, Dict, Union
from dataclasses import dataclass,asdict,field
from states.state import State
from custom_classes.button import Button
from managers.music_manager import MusicManager
from managers.state_manager import StateManager

@dataclass
class Player:
    name : str
    ip : str
    port : int
    is_host: bool
    selection_index: int = 0
    vote_index: int | None = None

class MultiplayerLobby(State):
    def __init__(self, game, player_name,socket_= None, players_list = {}, is_host=False):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Multiplayer Lobby")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)

        # UDP socket
        self.socket = socket_ if socket_ else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.01)

        self.acknowledged_players = set()
        self.state_change_confirmed = False

        # data from input
        self.player_name = player_name
        self.is_host = is_host
        
        self.players_list: Dict[str,Player] = self.convert_player_list_to_Player(players_list) if players_list else {}

        self.request_cooldown = 1
        self.last_request_time = 0

        self.max_players = 2

        # Buttons
        self.start_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT - 120,
            config.BUTTON_WIDTH + 10,
            config.BUTTON_HEIGHT + 10,
            'Start Game',
            font='CaveatBrush-Regular.ttf',
            button_color = config.COLOR_BEIGE)
        self.back_button = Button(
            20, 20,
            config.BUTTON_WIDTH // 1.2,
            config.BUTTON_HEIGHT,
            "Back",
            font='CaveatBrush-Regular.ttf',
            button_color = config.COLOR_BEIGE)

        if self.is_host:
            self.port = 9999
            self.host_ip = self.get_local_ip()
            self.socket.bind((self.host_ip, self.port))
            self.players_list[player_name] = Player(player_name,self.host_ip,self.port,is_host=True)  # Need to add the host to the list

    # ---------------- NETWORK ----------------
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

    def handle_network_packets(self):
        try:
            packet, (ip,port) = self.socket.recvfrom(1024)
            packet = json.loads(packet.decode('utf-8'))
            if packet.get('type') == "ACK_STATE_CHANGE":
                self.acknowledged_players.add((ip,port))
            elif packet.get('type') == 'JOIN':
                data = packet.get('data')
                player_name = data.get('name', "UNKNOWN")
                # Check if player is already connected
                if len(self.players_list) >= self.max_players:
                    print(f'{player_name} tried to join from {ip,port} but the lobby is full!')
                    return
                for name in self.players_list:
                    if name == player_name:
                        print(f'{player_name} tried to join from {ip,port} player with same name already joined!')
                        packet = {
                            'type' : 'SAME_NAME',
                            'data' : {'msg' : f'Player with username {player_name} is already in the lobby!'}
                        }
                        self.send_packet(packet)
                        return
                for player in self.players_list.values():
                    if (ip,port) == (player.ip,player.port):
                        print("Player already Connected")
                        return
                
                self.players_list[player_name] = Player(player_name,ip,port,is_host=False)

                print(f"{player_name} joined from {(ip,port)}")

                # Send updated player list
                # We need to change the dict so we can send it, because we cant send complex data as dataclass with JSON
                packet = {
                    'type': 'PLAYER_LIST',
                    'data': {'player_list': self.convert_player_list_to_dict(self.players_list)}
                }
                self.send_packet(packet)

            elif packet.get('type') == 'LEAVE':
                data = packet.get('data')
                del self.players_list[data.get('player_name')]
                packet = {
                    'type': 'PLAYER_LIST',
                    'data': {'player_list': self.convert_player_list_to_dict(self.players_list)}
                }
                print(f"{data.get('player_name')} left!")
                self.send_packet(packet)
            elif packet.get('type') == "PLAYER_LIST":
                print(self.players_list)
                data = packet.get('data')
                self.players_list = self.convert_player_list_to_Player(data.get('player_list'))
                print(self.players_list)
            elif packet.get('type') == 'STATE_CHANGE':
                data = packet.get('data')
                if  data.get('state', 'UNKNOWN') == 'MultiplayerMapSelector':
                    # Send ACK to host
                    ack_packet = {
                        'type': 'ACK_STATE_CHANGE'
                    }
                    self.send_packet(ack_packet)
                    self.exit_state()
                    self.state_manager.change_state("MultiplayerMapSelector", self.players_list,self.socket,self.player_name)
        except socket.timeout:
            pass
        except json.JSONDecodeError as e:
            print(f"Invalid JSON received from: {e}")

    def send_packet(self, packet : bytes | Dict):
        packet = json.dumps(packet).encode("utf-8")
        for player in self.players_list.values():
            if self.player_name != player.name:
                self.socket.sendto(packet, (player.ip,player.port))
    def convert_player_list_to_dict(self,player_list:Dict[str,Player])-> Dict[str,dict]:
        player_list_converted: Dict[str,dict] = {}
        for player_name,player_data in player_list.items():
            player_list_converted[player_name] = asdict(player_data)
        return player_list_converted
    
    def convert_player_list_to_Player(self,player_list:Dict[str,dict]) -> Dict[str,Player]:
        player_list_converted: Dict[str,Player] = {}
        for player_name,player_data in player_list.items():
            player_list_converted[player_name] = Player(**player_data)
        return player_list_converted
    # ---------------- INPUTS ----------------
    def handle_events(self, event):
        if self.back_button.is_clicked():
            packet = {
                'type': 'LEAVE',
                'data': {'player_name' : self.player_name}
            }
            self.send_packet(packet)
            self.exit_state()
            self.socket.close()
        elif self.start_button.is_clicked():
            self.broadcast_state_change("MultiplayerMapSelector")
            self.exit_state()
            self.state_manager.change_state("MultiplayerMapSelector", self.players_list,self.socket,self.player_name)

    def update(self):
        self.handle_network_packets()

    

    def broadcast_state_change(self, new_state):
        state_change_packet = {
            'type': 'STATE_CHANGE',
            'data': {'state': new_state}
        }
        self.acknowledged_players = set()

        self.send_packet(state_change_packet)
    # ---------------- Render ---------------
    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))

        # Title
        self.game.draw_text(screen, 'Multiplayer Lobby', config.COLOR_BLACK, config.SCREEN_WIDTH // 2, 60)

        # IP Label
        host = self.players_list.get('Server Host')
        ip_text = f'Share this IP with a friend: {host.ip if host else 'UNKNOWN'}'
        ip_surface = pygame.font.Font(None, config.FONT_SIZE).render(ip_text, True, config.TEXT_COLOR)
        ip_rect = ip_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 100))
        screen.blit(ip_surface, ip_rect)

        # Player count label
        player_count_text = f"Players: {len(self.players_list)}/2"
        player_count_surface = pygame.font.Font(None, config.FONT_SIZE).render(player_count_text, True, config.TEXT_COLOR)
        player_count_rect = player_count_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 125))
        screen.blit(player_count_surface, player_count_rect)

        # Draw player list
        y_start = 150
        for index, player_name in enumerate(self.players_list.keys()):
            if self.player_name == "Server Host" and player_name == "Server Host":
                player_name = 'Server Host (You)'
            elif self.player_name == player_name:
                player_name = f'{self.player_name} (You)'
            else:
                player_name = player_name

            text_surface = pygame.font.Font(None, config.FONT_SIZE).render(f'{index + 1}. {player_name}', True, config.TEXT_COLOR)
            text_rect = text_surface.get_rect(center=(config.SCREEN_WIDTH // 2, y_start + index * 40))
            screen.blit(text_surface, text_rect)

        # Draw buttons
        if self.is_host:
            self.start_button.draw(screen)
        self.back_button.draw(screen)