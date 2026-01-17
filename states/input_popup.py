import pygame
import config
import json
import socket
from states.state import State
from managers.state_manager import StateManager
from custom_classes.button import Button



class InputPopup(State):
    def __init__(self, game):
        State.__init__(self, game)
        pygame.display.set_caption("BomberMan: Multiplayer")
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.active_box = None

        self.state_manager = StateManager(game)

        # Input boxes
        self.username_rect = pygame.Rect(config.SCREEN_WIDTH // 4, config.SCREEN_HEIGHT // 3, config.SCREEN_WIDTH // 2, 40)
        self.address_rect = pygame.Rect(config.SCREEN_WIDTH // 4, config.SCREEN_HEIGHT // 3 + 80, config.SCREEN_WIDTH // 2, 40)

        self.username_text = 'Test'
        self.address_text = '192.168.1.11'

        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')

        self.username_color = self.color_inactive
        self.address_color = self.color_inactive

        self.result = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.01)
        
        # Buttons
        button_y = config.SCREEN_HEIGHT // 3 + 150
        self.join_button = Button(config.SCREEN_WIDTH // 2 - 110, button_y, 100, 40, "Join",
                                  self.submit,
                                  font='CaveatBrush-Regular.ttf',
                                  button_color=config.COLOR_BEIGE)
        self.back_button = Button(config.SCREEN_WIDTH // 2 + 10, button_y, 100, 40, "Back",
                                  self.go_back,
                                  font='CaveatBrush-Regular.ttf',
                                  button_color=config.COLOR_BEIGE)

    def submit(self):
        player_name = self.username_text.strip()
        ip = self.address_text.strip()
        if player_name and ip:
            self.send_join_request(player_name,ip)
    def send_join_request(self,player_name,ip_to_join):
        max_attempts = 5
        attempt = 0
        while attempt < max_attempts:
            packet = {
                "type": "JOIN",
                'data': {"name": player_name},
            }
            packet = json.dumps(packet).encode('utf-8')
            self.socket.sendto(packet, (ip_to_join, 9999))
            self.port = self.socket.getsockname()[1] # getsockname --> (ip,port)
            try:
                response, _ = self.socket.recvfrom(1024)
                response_packet = json.loads(response.decode('utf-8'))
                if response_packet.get('type') == 'PLAYER_LIST':
                    data = response_packet.get('data')
                    self.exit_state()
                    self.state_manager.change_state('MultiplayerLobby',player_name,self.socket,data.get('player_list'))
                    print("Joined successfully!")
                    break
                elif response_packet.get('type') == 'SAME_NAME':
                    data = response_packet.get('data')
                    print(data.get('msg'))
            except (socket.timeout, json.JSONDecodeError):
                # No response
                attempt += 1
                print(f"Join attempt {attempt} failed, retrying...")
    def go_back(self):
        self.exit_state()

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.username_rect.collidepoint(event.pos):
                self.active_box = 'username'
                self.username_color = self.color_active
                self.address_color = self.color_inactive
            elif self.address_rect.collidepoint(event.pos):
                self.active_box = 'address'
                self.address_color = self.color_active
                self.username_color = self.color_inactive
            else:
                self.active_box = None
                self.username_color = self.color_inactive
                self.address_color = self.color_inactive

        if event.type == pygame.KEYDOWN and self.active_box:
            if event.key == pygame.K_RETURN:
                self.submit()
            elif event.key == pygame.K_BACKSPACE:
                if self.active_box == 'username':
                    self.username_text = self.username_text[:-1]
                else:
                    self.address_text = self.address_text[:-1]
            else:
                if self.active_box == 'username':
                    self.username_text += event.unicode
                else:
                    self.address_text += event.unicode

        # Check button clicks
        if self.join_button.is_clicked():
            self.join_button.action()
        if self.back_button.is_clicked():
            self.back_button.action()

    def render(self, screen):
        popup_height = 260
        popup_rect = pygame.Rect(config.SCREEN_WIDTH // 4 - 10, config.SCREEN_HEIGHT // 3 - 20, config.SCREEN_WIDTH // 2 + 20, popup_height)
        pygame.draw.rect(screen, (50, 50, 50), popup_rect, border_radius=8)

        # Labels
        username_label = self.font.render("Username:", True, config.TEXT_COLOR)
        address_label = self.font.render("Host Address:", True, config.TEXT_COLOR)
        screen.blit(username_label, (self.username_rect.x, self.username_rect.y - 25))
        screen.blit(address_label, (self.address_rect.x, self.address_rect.y - 25))

        # Input boxes
        pygame.draw.rect(screen, self.username_color, self.username_rect, 2, border_radius=5)
        pygame.draw.rect(screen, self.address_color, self.address_rect, 2, border_radius=5)

        username_surface = self.font.render(self.username_text, True, config.TEXT_COLOR)
        address_surface = self.font.render(self.address_text, True, config.TEXT_COLOR)
        screen.blit(username_surface, (self.username_rect.x + 5, self.username_rect.y + 8))
        screen.blit(address_surface, (self.address_rect.x + 5, self.address_rect.y + 8))

        # Draw buttons
        self.join_button.draw(screen)
        self.back_button.draw(screen)