import json
import time
import socket
from typing import Dict,Tuple,Any,Optional


Addr = Tuple[str,int]
Packet = Dict[str,Any]

class NetworkManager():
    def __init__(self,socket: socket.socket, *, resend_timeout:float = 0.2) -> None:
        self.socket = socket
        self.socket.setblocking(False)

        # Seq for so we can track if packets got delivered twice
        self._seq = 0
        self._pending: Dict[int, Tuple[Addr,Packet,float]] = {}
        self._processed_seq: Dict[Addr,set[int]] = {}  # seq -> (addr,packet,last_time_sent)

        self.resend_timeout  = resend_timeout

    # ---------------- Sending ----------------
    def send_packet(self, addr: Addr, msg_type:str,data: Optional[dict] = None,scope: str = 'Game') -> int:
        self._seq += 1
        packet = {
            'scope' : scope,
            'type' : msg_type,
            'seq' : self._seq,
            'data': data
        }
        self._send_raw_packet(addr,packet)
        self._pending[self._seq] = (addr,packet,time.time())
        return self._seq

    def _send_raw_packet(self,addr: Addr,packet: Packet) -> None:
        raw_packet = json.dumps(packet).encode('utf-8')
        self.socket.sendto(raw_packet,addr)
    # ---------------- Receiving ----------------
    def poll(self) -> None:
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
            return

        if isinstance(seq,int):
            seen = self._processed_seq.setdefault(addr,set())
            if seq in seen:
                # Duplicate: still ACK, but don't process twice
                self._send_ack(addr,seq)
                return
            seen.add(seq)
            self._send_ack(addr,seq)
        
    def _send_ack(self,addr:Addr,seq:int) -> None: 
        ack_packet = {'type': 'ACK','seq': seq}
        self._send_raw_packet(addr,ack_packet)
    
    def update(self) -> None:
        '''Call every frame to resend un_ACKed packets'''
        now = time.time()
        for seq,(addr, packet, last_time_sent) in list(self._pending.items()):
            if now - last_time_sent >= self.resend_timeout:
                self._send_raw_packet(addr,packet)
                self._pending[seq] = (addr,packet,now)

