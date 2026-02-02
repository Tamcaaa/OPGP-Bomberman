import json
import os
import socket
import pygame
import config
from typing import List, Tuple, Any, Dict, Union
from dataclasses import dataclass,asdict,field
from states.general.state import State
from custom_classes.button import Button
from managers.music_manager import MusicManager
from managers.state_manager import StateManager
from managers.network_manager import NetworkManager


Addr = Tuple[str,int]
Packet = Dict[str,Any]

# Color name
COLOR_NAMES = {
    config.WHITE_PLAYER: "White", config.BLACK_PLAYER: "Black",
    config.RED_PLAYER: "Red", config.BLUE_PLAYER: "Blue",
    config.DARK_GREEN_PLAYER: "Green", config.LIGHT_GREEN_PLAYER: "Light Green",
    config.YELLOW_PLAYER: "Yellow", config.PINK_PLAYER: "Pink",
    config.ORANGE_PLAYER: "Orange", config.PURPLE_PLAYER: "Purple",
    config.BROWN_PLAYER: "Brown", config.CYAN_PLAYER: "Cyan"
}

@dataclass
class Player:
    name : str
    addr : Tuple[str,int]
    is_host: bool
    is_ready: bool = False
    selection_index: int = 0
    vote_index: int | None = None
    color_index: int = 0  
    hat_index: int = 0 

class MultiplayerLobby(State):
    def __init__(self, game, player_name,network_manager:NetworkManager, players_list = {},*, is_host=False):
        super().__init__(game)
        pygame.display.set_caption("BomberMan: Multiplayer Lobby")
        self.bg_image = pygame.image.load(os.path.join(game.photos_dir, "bg.png"))

        self.music_manager = MusicManager()
        self.state_manager = StateManager(game)
        self.network_manager = network_manager

        # data from input
        self.player_name = player_name
        self.is_host = is_host

        self.leave_seq = None
        
        self.players_list: Dict[str,Player] = self.convert_player_list_to_Player(players_list) if players_list else {}

        self.max_players = 2
        
        # Animation
        self.last_idle_update = pygame.time.get_ticks()
        self.idle_index = 0
        self.idle_fps = 4

        # Buttons
        self.back_button = Button(
            20, 20,
            config.BUTTON_WIDTH // 1.2,
            config.BUTTON_HEIGHT,
            "Back",
            font='CaveatBrush-Regular.ttf',
            button_color = config.COLOR_BEIGE)

        if self.is_host:
            self.host_ip = self.get_local_ip()
            self.network_manager.socket.bind((self.host_ip, config.SERVER_PORT))
            addr = (self.host_ip, config.SERVER_PORT)
            self.players_list[player_name] = Player(player_name,addr,is_host=True,is_ready=True)  # Need to add the host to the list

            self.start_button = Button(
            config.SCREEN_WIDTH // 2 - config.BUTTON_WIDTH // 2,
            config.SCREEN_HEIGHT - 120,
            config.BUTTON_WIDTH + 10,
            config.BUTTON_HEIGHT + 10,
            'Start Game',
            font='CaveatBrush-Regular.ttf',
            button_color = config.COLOR_BEIGE)
            
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
            button_color = config.COLOR_BEIGE)
            
            self.ready_button.set_visible(True)
            self.ready_button.set_enabled(True)

        self.my_player = self.players_list.get(self.player_name,None)
        if self.my_player is None:
            raise Exception('my_player is None in MultiplayerLobby')

        # --- Skin Selection Assets ---
        self.load_skin_assets()
        self.tinted_idle_images: Dict[int,Tuple[pygame.Surface]] = {} # {color_index: Tuple[tinted_images]}
        self._load_tinted_images()

    # ---------------- SKIN ASSETS ----------------
    def load_skin_assets(self):
        """Load color list, hat images, and idle animations for preview"""
        # Available colors
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
                self.hat_images[name] = None
                continue
                
            path = os.path.join(self.game.photos_dir, "../assets/player_hats", file)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                # Scale for preview
                img = pygame.transform.smoothscale(img, (50, 50))
                self.hat_images[name] = img
            else:
                self.hat_images[name] = None
        
        # Font for skin selector
        self.skin_font = pygame.font.Font("CaveatBrush-Regular.ttf", 20)
    
    def _load_tinted_images(self,color_index: int|None = None) -> None:
        # Load tinted images for spefic color index (We safe it for later use for example if player is spamming the color wheel)
        if not self.players_list:
            return
        for player in self.players_list.values():
            tinted_images = []
            color_index = color_index if color_index else player.color_index
            for idle_frame in self.idle_frames:
                color = self.available_colors[color_index]
                tinted_images.append(self.tint_image(idle_frame,color))
            self.tinted_idle_images.setdefault(color_index,tuple(tinted_images))

    def tint_image(self, image, color) -> pygame.Surface:
        '''Apply color tint to player sprite'''
        tinted = image.copy()
        tint = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        tint.fill((*color, 255))
        tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        return tinted

    def update_idle_animation(self):
        '''Update idle animation frame'''
        now = pygame.time.get_ticks()
        if now - self.last_idle_update >= 1000 // self.idle_fps:
            self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
            self.last_idle_update = now

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
            
    def convert_player_list_to_dict(self,player_list:Dict[str,Player])-> Dict[str,dict]:
        player_list_converted: Dict[str,dict] = {}
        for player_name,player_data in player_list.items():
            player_list_converted[player_name] = asdict(player_data)
        return player_list_converted
    
    def convert_player_list_to_Player(self,player_list:Dict[str,dict]) -> Dict[str,Player]:
        player_list_converted: Dict[str,Player] = {}
        for player_name,player_data in player_list.items():
            player_data['addr'] = tuple(player_data['addr'])
            player_list_converted[player_name] = Player(**player_data)
        return player_list_converted
    
    # ---------------- INPUTS ----------------
    def handle_events(self, event):
        if not self.my_player:
            return
        elif self.back_button.is_clicked():
            packet_type = 'LEAVE'
            pakcet_data = {'player_name' : self.my_player.name}
            scope = 'MultiplayerLobby'
            self.leave_seq = self.network_manager.send_packet(self.my_player.addr,packet_type,pakcet_data,scope)
        elif self.is_host and self.start_button.is_clicked():
            self.broadcast_state_change("MultiplayerMapSelector")
            self.exit_state()
            self.state_manager.change_state("MultiplayerMapSelector", self.players_list,self.network_manager,self.player_name)
        elif (not self.is_host) and self.ready_button.is_clicked():
            self.my_player.is_ready = not self.my_player.is_ready
            packet = {
                'type' : 'READY_TOGGLE',
                'data' : {'player_name': self.my_player.name},
                'scope' : 'MultiplayerLobby'
            }
            for player in self.players_list.values():
                if player.is_host:
                    self.network_manager.send_packet(player.addr,packet['type'],packet['data'],packet['scope'])
        # Skin selection controls
        if event.type == pygame.KEYDOWN and self.player_name in self.players_list:
            my_player = self.players_list[self.player_name]
            other_player_colors = [p.color_index for name, p in self.players_list.items() if name != self.player_name]
            
            # Color selection (Arrow Keys or WASD)
            if event.key in [pygame.K_LEFT, pygame.K_a]:
                my_player.color_index = (my_player.color_index - 1) % len(self.available_colors)
                # Skip if same as other player
                while my_player.color_index in other_player_colors:
                    my_player.color_index = (my_player.color_index - 1) % len(self.available_colors)
                self._load_tinted_images()
                print(self.tinted_idle_images)
                self.broadcast_skin_update()
                
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                my_player.color_index = (my_player.color_index + 1) % len(self.available_colors)
                # Skip if same as other player
                while my_player.color_index in other_player_colors:
                    my_player.color_index = (my_player.color_index + 1) % len(self.available_colors)
                self._load_tinted_images()
                print(self.tinted_idle_images)
                self.broadcast_skin_update()
            
            # Hat selection (Up/Down or WS)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                my_player.hat_index = (my_player.hat_index - 1) % len(config.HATS)
                self.broadcast_skin_update()
                
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                my_player.hat_index = (my_player.hat_index + 1) % len(config.HATS)
                self.broadcast_skin_update()

    # ---------------- Network ----------------
    def handle_network_packets(self):
        poll_data = self.network_manager.poll()
        if poll_data:
            self.handle_packet(poll_data)

    def handle_packet(self,poll_data:Tuple[Packet, Addr]) -> None:
        packet,addr = poll_data

        if not packet.get('scope') == 'MultiplayerLobby':
            print(f'[SCOPE_ERROR] from MultiplayerLobby; packet:{packet} from {addr}')
            return
        packet_type = packet.get('type')
        packet_data = packet.get('data')
        packet_seq = packet.get('seq')

        if not packet_type or not packet_data:
            raise Exception(f'Invalid packet (data or type missing): packet:{packet} from {addr}')
        
        if packet_type == 'JOIN':
            self._handle_join_packet(packet_data,addr)
        elif packet_type == 'LEAVE':
            self._handle_leave_packet(packet_data,addr)
        elif packet_type == 'PLAYER_LIST':
            self._handle_player_list_packet(packet_data,addr)
        elif packet_type == 'STATE_CHANGE':
            self._handle_state_change_packet(packet_data,addr)
        elif packet_type == 'SKIN_UPDATE':
            self._handle_skin_update_packet(packet_data,addr)
        elif packet_type == 'READY_TOGGLE':
            self._handle_ready_toggle_packet(packet_data,addr)
    
    def _handle_skin_update_packet(self,packet_data,addr):
        player_name = packet_data.get('player_name')
        if not (player_name in self.players_list):
            print(f'[SKIN_UPDATE ERROR] Unknown player {player_name} from {addr}')
            return
        self.players_list[player_name].color_index = packet_data.get('color_index', 0)
        self.players_list[player_name].hat_index = packet_data.get('hat_index', 0)
        print(f'[SKIN_UPDATE] {player_name} updated skin from {addr}')

    def _handle_state_change_packet(self,packet_data,addr):
        state = packet_data.get('state')
        print(f'[STATE_CHANGE] state: {state} from {addr}')
        self.exit_state()
        self.state_manager.change_state('MultiplayerMapSelector',self.players_list,self.network_manager,self.player_name)

    def _handle_player_list_packet(self,packet_data,addr) -> None:
        player_list = packet_data.get('player_list')
        self.players_list = self.convert_player_list_to_Player(player_list)
        print(f'[PLAYER_LIST UPDATE] player_list: {self.players_list}') 

    def _handle_leave_packet(self,packet_data,addr) -> None:
        player_name = packet_data.get('player_name')
        print(f'{player_name} left from {addr}')
        del self.players_list[player_name]
        self._broadcast_player_list()
        
    def _broadcast_player_list(self) -> None:
        if self.my_player is None:
            return
        
        packet_type = 'PLAYER_LIST'
        data = {'player_list': self.convert_player_list_to_dict(self.players_list)}
        scope = 'MultiplayerLobby'
        for player in self.players_list.values():
            if player.addr == self.my_player.addr:
                continue 
            print(f'Sending PLAYER_LIST to {player.addr}')
            self.network_manager.send_packet(player.addr,packet_type,data,scope)

    def _handle_join_packet(self,packet_data,addr) -> None:
        player_name = packet_data.get('player_name','UNKNOWN')
            
        if (len(self.players_list) >= self.max_players):
            print(f'{player_name} tried to join from {addr} but the lobby is full!')
            return
        
        for name in self.players_list:
            if (name == player_name):
                print(f'{player_name} tried to join from {addr} player with the same name already joined!')
                data = {'msg' : f'Player with username {player_name} is already in the lobby!'}
                packet_type = 'SAME_DATA'
                scope = 'MultiplayerLobby'
                self.network_manager.send_packet(addr,packet_type,data,scope)
                return       
        for player in self.players_list.values():
            if (addr == (player.addr)):
                print(f'Address: {addr} is already in player_list')
                return
        
        # Create new player with unique color
        new_player = Player(player_name, (addr), is_host=False)
        
        # Assign first available color
        taken_colors = [p.color_index for p in self.players_list.values()]
        for color_idx in range(len(self.available_colors)):
            if color_idx not in taken_colors:
                new_player.color_index = color_idx
                break
        
        self.players_list[player_name] = new_player
        print(f"{player_name} joined from {addr}")

        self._broadcast_player_list()

    def _handle_ready_toggle_packet(self,packet_data,addr) -> None:
        player_name = packet_data.get('player_name')
        if not (player_name in self.players_list):
            print(f'[READY_TOGGLE ERROR] Unknown player {player_name} from {addr}')
            return
        player = self.players_list[player_name]
        player.is_ready = not (player.is_ready)
        print(f'[READY_TOGGLE] {player_name} is_ready: {player.is_ready} from {addr}')
    def broadcast_skin_update(self) -> None:
        if not self.my_player:
            return
        packet_type = 'SKIN_UPDATE'
        data = {
            'player_name': self.my_player.name,
            'color_index': self.my_player.color_index,
            'hat_index': self.my_player.hat_index
        }
        scope = 'MultiplayerLobby'
        for player in self.players_list.values():
            if not (player == self.my_player):
                self.network_manager.send_packet(player.addr,packet_type,data,scope)

    def broadcast_state_change(self,new_state:str) -> None:
        packet_type = 'STATE_CHANGE'
        data = {'state' : new_state}
        scope = 'MultiplayerLobby'
        for player in self.players_list.values():
            self.network_manager.send_packet(player.addr,packet_type,data,scope)

    def check_leave_seq(self) -> None:
        '''Check if leave packet got Ack'ed'''
        if self.leave_seq and self.my_player and self.network_manager.get_completed_seq(self.my_player.addr,seq=self.leave_seq):
            print(f'[LEFT LOBBY] {self.my_player.name} has left the lobby.')
            self.network_manager.close_socket()
            self.exit_state()
            self.state_manager.change_state('MainMenu')
    # ---------------- Update ----------------
    def update(self) -> None:
        self.check_leave_seq()
        self.update_idle_animation()
        self.handle_network_packets()
        self.network_manager.update()
    # ---------------- Render ---------------
    def render(self, screen):
        screen.blit(self.bg_image, (0, 0))

        # Title
        self.game.draw_text(screen, 'Multiplayer Lobby', config.COLOR_BLACK, config.SCREEN_WIDTH // 2, 30)

        # IP Label (if host)
        if self.is_host:
            host = self.players_list.get(self.player_name)
            ip_text = f'Share this IP: {self.host_ip if host else "UNKNOWN"}'
            ip_surface = pygame.font.Font(None, 24).render(ip_text, True, config.TEXT_COLOR)
            ip_rect = ip_surface.get_rect(center=(config.SCREEN_WIDTH // 2, 60))
            screen.blit(ip_surface, ip_rect)

        # Draw player skin selectors
        player_list = list(self.players_list.values())
        
        for idx, player in enumerate(player_list):
            if idx >= 2:  # Max 2 players
                break
            
            # Position for each player panel
            if idx == 0:
                panel_x = 80
            else:
                panel_x = config.SCREEN_WIDTH - 280
            
            panel_y = 120
            self.draw_player_panel(screen, player, panel_x, panel_y)
        
        # Instructions
        if len(player_list) > 0:
            inst_y = config.SCREEN_HEIGHT - 160
            inst_font = pygame.font.Font("CaveatBrush-Regular.ttf", 18)
            
            inst_lines = [
                "Arrow Keys / WASD: Change Color",
                "Up/Down or W/S: Change Hat"
            ]
            
            for i, line in enumerate(inst_lines):
                inst_surf = inst_font.render(line, True, (80, 60, 40))
                inst_rect = inst_surf.get_rect(center=(config.SCREEN_WIDTH // 2, inst_y + i * 22))
                screen.blit(inst_surf, inst_rect)

        # Draw Buttons
        if self.is_host:
            # Check if all players are ready
            if all(player.is_ready for player in self.players_list.values()):
                self.start_button.set_visible(len(self.players_list) >= 2)
                self.start_button.set_enabled(len(self.players_list) >= 2)
                self.start_button.draw(screen)
            else:
                self.start_button.set_visible(False)
                self.start_button.set_enabled(True)
        else:
            self.ready_button.draw(screen)

        self.back_button.draw(screen)

    def draw_player_panel(self, screen, player: Player, x, y):
        """Draw individual player's skin selection panel"""
        panel_width = 200
        panel_height = 280
        
        # Panel background
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (15, 20, 30, 200), panel_surf.get_rect(), border_radius=15)
        pygame.draw.rect(panel_surf, (*config.MENU_OUTLINE, 200), panel_surf.get_rect(), width=2, border_radius=15)
        screen.blit(panel_surf, (x, y))
        
        # Player name
        name_color = config.COLOR_WHITE
        name_text = player.name if len(player.name) <= 12 else player.name[:12] + "..."
        name_surf = self.skin_font.render(name_text, True, name_color)
        name_rect = name_surf.get_rect(center=(x + panel_width // 2, y + 130))
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
        preview_rect = frame.get_rect(center=(x + panel_width // 2, preview_y))
        screen.blit(frame, preview_rect)
        
        # Draw hat on player
        hat_def = config.HATS[player.hat_index]
        if hat_def["name"] != "None":
            hat_img = self.hat_images.get(hat_def["name"])
            if hat_img:
                # Adjust hat position
                hat_x = preview_rect.centerx - hat_img.get_width() // 2
                hat_y = preview_rect.top - 10
                screen.blit(hat_img, (hat_x, hat_y))
                
        color = self.available_colors[player.color_index]
        color_name = COLOR_NAMES.get(color, "Unknown")
        color_surf = pygame.font.Font("CaveatBrush-Regular.ttf", 18).render(f"Color: {color_name}", True, (255, 255, 255))
        color_rect = color_surf.get_rect(center=(x + panel_width // 2, y + 160))
        screen.blit(color_surf, color_rect)
        
        # Hat name
        hat_name_surf = pygame.font.Font("CaveatBrush-Regular.ttf", 18).render(f"Hat: {hat_def['name']}", True, (255, 255, 255))
        hat_name_rect = hat_name_surf.get_rect(center=(x + panel_width // 2, y + 185))
        screen.blit(hat_name_surf, hat_name_rect)


        # Ready indicator
        if not self.my_player:
            return
        
        ready_color  = config.COLOR_LIGHT_GREEN if player.is_ready else config.COLOR_RED
        if player.name == self.my_player.name:
            ready_surf = pygame.font.Font("CaveatBrush-Regular.ttf", 16).render("(You)", True, ready_color)
        else:
            ready_surf = pygame.font.Font("CaveatBrush-Regular.ttf", 16).render("Ready", True, ready_color)
        ready_rect = ready_surf.get_rect(center=(x + panel_width // 2, y + 215))
        screen.blit(ready_surf, ready_rect)