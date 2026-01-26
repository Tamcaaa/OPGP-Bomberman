import json
import time
import socket
from typing import Dict,Tuple,Any,Optional,List,Set,ItemsView


Addr = Tuple[str,int]
Packet = Dict[str,Any]

class NetworkManager:
    def __init__(self,socket: socket.socket, *, resend_timeout:float = 0.2,resend_tries: int = 3) -> None:
        self.socket = socket
        self.socket.setblocking(False)

        # Seq for so we can track if packets got delivered twice
        self._seq = 0
        self._pending: Dict[int, Tuple[Addr,Packet,float,int]] = {}
        self._processed_seq: Dict[Addr,set[int]] = {}  # seq -> (addr,packet,last_time_sent)

        self.resend_tries = resend_tries
        self.resend_timeout  = resend_timeout

    # ---------------- Sending ----------------
    def send_packet(self, addr: Addr, packet_type:str,data: Optional[dict] = None,scope: str = 'Game') -> int:
        self._seq += 1
        packet = {
            'scope' : scope,
            'type' : packet_type,
            'seq' : self._seq,
            'data': data
        }
        self._send_raw_packet(addr,packet)
        resend_try = 0
        self._pending[self._seq] = (addr,packet,time.time(),resend_try)
        return self._seq
    
    def broadcast_packet(self,addrs: Tuple[Addr], packet_type: str, data: Optional[dict] = None, scope: str = 'Game') -> Tuple[int]:
        seq_list = []
        for addr in addrs:
            self._seq += 1
            seq_list += [self._seq]
            packet = {
                'scope' : scope,
                'type' : packet_type,
                'seq' : self._seq,
                'data' : data
            }
            self._send_raw_packet(addr,packet)
            resend_try = 0
            self._pending[self._seq] = (addr,packet,time.time(),resend_try)
        return tuple(seq_list)
    
    def _send_raw_packet(self,addr: Addr,packet: Packet) -> None:
        raw_packet = json.dumps(packet).encode('utf-8')
        self.socket.sendto(raw_packet,addr)
    # ---------------- Receiving ----------------
    def poll(self) -> None | Tuple[Packet,Addr]:
        '''
        Call every frame/tick.
        - Reads all available UDP packets
        - Handles ACKs, duplicates
        '''
        try:
            raw, addr = self.socket.recvfrom(65535)
        except BaseException:
            return # no more packets
        
        try:
            packet = json.loads(raw.decode('utf-8'))
        except Exception:
            print(f'[WARN] Invalid packet: {raw} from {addr}')
            return # ignore invalid packets
        
        packet_type = packet.get('type')
        seq = packet.get('seq')

        # Incoming ACK
        if packet_type == 'ACK' and isinstance(seq,int):
            self._pending.pop(seq,None)
            self._processed_seq[addr].add(seq)
            print(f'[SEQ COMPLETED] seq: {seq}')
            return

        if isinstance(seq,int):
            seen = self._processed_seq.setdefault(addr,set())
            if seq in seen:
                # Duplicate: still ACK, but don't process twice
                self._send_ack(addr,seq)
                return
            seen.add(seq)
            print(f'[SEQ PENDING] seq: {seq}')
            self._send_ack(addr,seq)
            return (packet,addr)
        
    def _send_ack(self,addr:Addr,seq:int) -> None: 
        ack_packet = {'type': 'ACK','seq': seq}
        self._send_raw_packet(addr,ack_packet)
    
    def update(self) -> None:
        '''Call every frame to resend un_ACKed packets'''
        now = time.time()
        for seq,(addr, packet, last_time_sent, resend_try) in list(self._pending.items()):
            if now - last_time_sent >= self.resend_timeout and resend_try <= self.resend_tries:
                self._send_raw_packet(addr,packet)
                resend_try += 1
                self._pending[seq] = (addr,packet,now,resend_try)
            elif resend_try > self.resend_tries:
                self._pending.pop(seq)
                print(f'[SEQ DROPPED] seq: {seq}')
    def close_connection(self) -> None:
        self.socket.close()
    # ---------------- Getters and Setters ----------------
    def get_processed_seq(self,addr: Optional[Addr] = None,*, seq: Optional[int] = None) -> ItemsView[Addr,Set[int]] | set[int] | bool | None:
        if addr is None and seq is None:
            return self._processed_seq.items()
        if addr and seq is None:
            return self._processed_seq.get(addr, set())
        if addr and seq:
            return True if seq in self._processed_seq.get(addr, set()) else False
        return None
    
    # ---------------- Packet Checker ----------------
    def _check_packet(self,packet:Packet,addr: Addr) -> bool:
        packet_scope = packet.get('scope')
        packet_type = packet.get('type')
        packet_seq = packet.get('seq')
        packet_data = packet.get('data')

        if not packet_scope:
            print(f'[PACKET ERROR] scope is missing or empty! packet: {packet} from {addr}')
            return False
        if not packet_type:
            print(f'[PACKET ERROR] type is missing or empty! packet: {packet} from {addr}')
            return False
        if packet_seq:
            print(f'[PACKET ERROR] seq is missing or empty! packet: {packet} from {addr}')
            return False
        if packet_data is None:
            print(f'[PACKET ERROR] data is missing or empty! packet: {packet} from {addr}')
            return False
        
        if packet_scope == 'MultiplayerLobby':
            return self._check_multiplayerLobby_packet(packet_type,packet_data,addr)
        return False
    
    def _check_multiplayerLobby_packet(self,packet_type,packet_data,addr) -> bool:    
        if packet_type == 'JOIN':
            if not packet_data.get('player_name'):
                print(f'[JOIN_PACKET ERROR] missing or empty player_name from {addr}')
                return False
            return True
        elif packet_type == 'LEAVE':
            if not packet_data.get('player_name'):
                print(f'[LEAVE_PACKET ERROR] missing or empty player_name from {addr}')
                return False
            return True
        elif packet_type == 'PLAYER_LIST':
            if not packet_data.get('player_list'):
                print(f'[PLAYER_LIST ERROR] missing or empty player_list from {addr}')
                return False
            return True
        elif packet_type == 'STATE_CHANGE':
            if not packet_data.get('state'):
                print(f'[STATE_CHANGE ERROR] missing or empty state from {addr}')
                return False
            return True
        elif packet_type == 'SKIN_UPDATE':
            color_index = packet_data.get('color_index')
            hat_index = packet_data.get('hat_index')
            if not packet_data.get('player_name'):
                print(f'[SKIN_UPDATE ERROR] missing or empty player_name from {addr}')
                return False
            if not color_index:
                print(f'[SKIN_UPDATE ERROR] missing or empty color_index from {addr}')
                return False
            if not isinstance(color_index,int):
                print(f'[SKIN_UPDATE ERROR] invalid color_index from {addr}')
                return False
            if not hat_index:
                print(f'[SKIN_UPDATE ERROR] missing or empty hat_index from {addr}')
                return False
            if not isinstance(hat_index,int):
                print(f'[SKIN_UPDATE ERROR] invalid hat_index from {addr}')
                return False
            return True
        return False