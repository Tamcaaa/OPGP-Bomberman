import json
import time
import socket
from typing import Dict,Tuple,Any,Optional,List,Set,ItemsView


Addr = Tuple[str,int]
Packet = Dict[str,Any]

class NetworkManager:
    def __init__(self,socket: socket.socket, *, resend_timeout:float = 0.5,resend_tries: int = 5) -> None:
        self.socket = socket
        self.socket.setblocking(False)

        # Seq for so we can track if packets got delivered twice
        self._seq = 0
        self._pending: Dict[int, Tuple[Addr,Packet,float,int]] = {}
        self._processed_seq: Dict[Addr,set[int]] = {}  # Track incoming packet seqs (duplicate detection)
        self._completed_seq: Dict[Addr,set[int]] = {}  # Track outgoing packets that got ACKed

        self.resend_tries = resend_tries
        self.resend_timeout  = resend_timeout

    def close_socket(self) -> None:
        self.socket.close()

    # ---------------- Sending ----------------
    def send_packet(self, addr: Addr, packet_type:str,data: Optional[dict] = None,scope: str = 'Game') -> int:
        self._seq += 1
        packet = {
            'scope' : scope,
            'type' : packet_type,
            'seq' : self._seq,
            'data': data
        }
        print(f'[SEQ SENT] seq: {self._seq} packet: {packet} to {addr}')
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
            self._completed_seq.setdefault(addr, set()).add(seq)
            print(f'[SEQ COMPLETED] seq: {seq} packet: {packet} from {addr}')
            return

        if isinstance(seq,int):
            seen = self._processed_seq.setdefault(addr,set())
            if seq in seen:
                # Duplicate: still ACK, but don't process twice
                self._send_ack(addr,seq)
                return
            seen.add(seq)
            print(f'[SEQ RECIEVED] seq: {seq} packet: {packet} from {addr}')
            self._send_ack(addr,seq)
            return (packet,addr)
        print(f'[WARN] Packet with no seq: {packet} from {addr}')
        
    def _send_ack(self,addr:Addr,seq:int) -> None: 
        ack_packet = {'type': 'ACK','seq': seq}
        self._send_raw_packet(addr,ack_packet)
    
    def update(self) -> None:
        '''Call every frame to resend un_ACKed packets'''
        now = time.time()
        for seq,(addr, packet, last_time_sent, resend_try) in list(self._pending.items()):
            if now - last_time_sent >= self.resend_timeout and resend_try <= self.resend_tries:
                print(f'[SEQ RESEND] seq: {seq} packet: {packet} to {addr} (try {resend_try + 1})')
                self._send_raw_packet(addr,packet)
                resend_try += 1
                self._pending[seq] = (addr,packet,now,resend_try)
            elif resend_try > self.resend_tries:
                self._pending.pop(seq)
                print(f'[SEQ DROPPED] seq: {seq}')
    def close_connection(self) -> None:
        self.socket.close()
    # ---------------- Getters and Setters ----------------
    def get_completed_seq(self,addr: Optional[Addr] = None,*, seq: Optional[int] = None) -> ItemsView[Addr,Set[int]] | set[int] | bool | None:
        """Check if outgoing packets got ACKed"""
        if addr is None and seq is None:
            return self._completed_seq.items()
        if addr and seq is None:
            return self._completed_seq.get(addr, set())
        if addr and seq:
            return True if seq in self._completed_seq.get(addr, set()) else False
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
        if not packet_seq:
            print(f'[PACKET ERROR] seq is missing or empty! packet: {packet} from {addr}')
            return False
        if not packet_data:
            print(f'[PACKET ERROR] data is missing or empty! packet: {packet} from {addr}')
            return False
        
        if packet_scope == 'MultiplayerLobby':
            return self._check_multiplayerLobby_packet(packet_type,packet_data,addr)
        return False
    
    def _check_multiplayerLobby_packet(self, packet_type: str, packet_data: Dict[str, Any], addr: Addr) -> bool:
        def require_present(field: str, *, allow_empty_str: bool = False) -> bool:
            value = packet_data.get(field)
            if value is None:
                print(f'[{packet_type}_PACKET ERROR] missing {field} from {addr}')
                return False
            if not allow_empty_str and isinstance(value, str) and not value.strip():
                print(f'[{packet_type}_PACKET ERROR] empty {field} from {addr}')
                return False
            return True

        if packet_type in {'JOIN', 'LEAVE', 'READY_TOGGLE'}:
            return require_present('player_name')

        if packet_type == 'PLAYER_LIST':
            return require_present('player_list')

        if packet_type == 'STATE_CHANGE':
            return require_present('state')

        if packet_type == 'SKIN_UPDATE':
            if not require_present('player_name'):
                return False
            color_index = packet_data.get('color_index')
            hat_index = packet_data.get('hat_index')
            if color_index is None:
                print(f'[SKIN_UPDATE ERROR] missing color_index from {addr}')
                return False
            if not isinstance(color_index, int):
                print(f'[SKIN_UPDATE ERROR] invalid color_index from {addr}')
                return False
            if hat_index is None:
                print(f'[SKIN_UPDATE ERROR] missing hat_index from {addr}')
                return False
            if not isinstance(hat_index, int):
                print(f'[SKIN_UPDATE ERROR] invalid hat_index from {addr}')
                return False
            return True

        print(f'[MultiplayerLobby ERROR] unknown packet type: {packet_type} from {addr}')
        return False