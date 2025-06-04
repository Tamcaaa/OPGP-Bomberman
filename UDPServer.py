import socket
import threading
import time


class UDPServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.clients = {}
        self.running = True
        self.player_count = 0
        self.game_state = {}

        print(f"UDP Server started on {host}:{port}")

        # Spustenie vlákna pre prijímanie správ
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        # Spustenie vlákna pre aktualizáciu stavu hry
        self.update_thread = threading.Thread(target=self.update_game_state)
        self.update_thread.daemon = True
        self.update_thread.start()

    def receive_messages(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode()

                if addr not in self.clients:
                    self.handle_new_connection(addr, message)
                else:
                    self.handle_client_message(addr, message)
            except Exception as e:
                print(f"Error receiving message: {e}")

    def handle_new_connection(self, addr, message):
        if self.player_count < 2:
            player_id = self.player_count + 1
            self.clients[addr] = player_id
            self.player_count += 1

            # Inicializácia herného stavu pre hráča
            self.game_state[player_id] = {
                'x': 0,
                'y': 0,
                'health': 3,
                'bombs': []
            }

            # Odoslanie potvrdenia a ID hráča
            response = f"CONNECTED|{player_id}"
            self.sock.sendto(response.encode(), addr)
            print(f"Player {player_id} connected from {addr}")

            # Ak sú pripojení dvaja hráči, oznámime štart hry
            if self.player_count == 2:
                self.broadcast("START")
        else:
            response = "FULL|Server is full"
            self.sock.sendto(response.encode(), addr)

    def handle_client_message(self, addr, message):
        player_id = self.clients[addr]
        parts = message.split('|')

        if parts[0] == 'POSITION':
            try:
                x, y = map(int, parts[1:])
                self.game_state[player_id]['x'] = x
                self.game_state[player_id]['y'] = y
            except:
                print(f"Invalid position update from player {player_id}")

        elif parts[0] == 'PLACE_BOMB':
            bomb_data = parts[1]
            self.game_state[player_id]['bombs'].append(bomb_data)
            self.broadcast(f"BOMB|{player_id}|{bomb_data}")

        elif parts[0] == 'EXPLOSION':
            bomb_id = parts[1]

            for player in self.game_state.values():
                if bomb_id in player['bombs']:
                    player['bombs'].remove(bomb_id)
            self.broadcast(f"EXPLOSION|{bomb_id}")

    def update_game_state(self):
        while self.running:
            if self.player_count > 0:
                state_str = self.serialize_game_state()
                self.broadcast(f"STATE|{state_str}")
            time.sleep(0.05)  # 20 aktualizácií za sekundu

    def serialize_game_state(self):
        return str(self.game_state)

    def broadcast(self, message):
        for addr in self.clients:
            try:
                self.sock.sendto(message.encode(), addr)
            except Exception as e:
                print(f"Error broadcasting to {addr}: {e}")

    def stop(self):
        self.running = False
        self.sock.close()
        print("Server stopped")


if __name__ == "__main__":
    server = UDPServer()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()