import json
import time
import socket
from typing import Dict, Tuple, Any, Optional, Set, ItemsView


Addr = Tuple[str, int]
Packet = Dict[str, Any]


class NetworkManager:
    # True => reliable (ACK + resend), False => unreliable (send once).
    PACKET_RELIABILITY: Dict[str, bool] = {
        # Discovery / lobby browse (best-effort only)
        'DISCOVER_HOSTS': False,
        'HOST_OFFER': False,

        # High-frequency gameplay updates
        'PLAYER_UPDATE': False,

        # Lobby flow
        'JOIN': True,
        'LEAVE': True,
        'READY_TOGGLE': True,
        'PLAYER_LIST': True,
        'SKIN_UPDATE': True,
        'STATE_CHANGE': True,
        'SAME_DATA': True,

        # Map selector flow
        'MAP_SELECTION': True,
        'MOVE_SELECTION': False,      # Frequent cursor updates can be dropped.
        'CONFIRM_SELECTION': True,
        'CANCEL_SELECTION': True,
        'FINAL_MAP_SELECTION': True,

        # Match events
        'BOMB_UPDATE': True,
        'POWERUP_UPDATE': True,
    }

    def __init__(
        self,
        socket: socket.socket,
        *,
        resend_timeout: float = 0.5,
        resend_tries: int = 5,
    ) -> None:
        self.socket = socket
        self.socket.setblocking(False)

        # Outgoing sequence number.
        self._seq = 0
        self._pending: Dict[int, Tuple[Addr, Packet, float, int]] = {}
        self._processed_seq: Dict[Addr, set[int]] = {}
        self._completed_seq: Dict[Addr, set[int]] = {}

        self.resend_tries = resend_tries
        self.resend_timeout = resend_timeout
        self.last_cleanup = time.time()
        self.cleanup_interval = 30

    def close_socket(self) -> None:
        self.close_connection()

    # ---------------- Sending ----------------
    @classmethod
    def is_reliable_packet_type(cls, packet_type: str) -> bool:
        return cls.PACKET_RELIABILITY.get(packet_type, True)

    @classmethod
    def set_packet_reliability(cls, packet_type: str, reliable: bool) -> None:
        cls.PACKET_RELIABILITY[packet_type] = reliable

    @classmethod
    def get_packet_reliability(cls, packet_type: str) -> bool:
        return cls.is_reliable_packet_type(packet_type)

    def send_packet(
        self,
        addr: Addr,
        packet_type: str,
        data: Optional[dict] = None,
        scope: str = 'Game',
        *,
        reliable: Optional[bool] = None,
    ) -> int:
        if reliable is None:
            reliable = self.is_reliable_packet_type(packet_type)

        self._seq += 1
        packet = {
            'scope': scope,
            'type': packet_type,
            'seq': self._seq,
            'data': data
        }

        self._send_raw_packet(addr, packet)
        if not reliable:
            return self._seq

        self._pending[self._seq] = (addr, packet, time.time(), 0)
        return self._seq

    def send_reliable(self, addr: Addr, packet_type: str, data: Optional[dict] = None, scope: str = 'Game') -> int:
        return self.send_packet(addr, packet_type, data, scope, reliable=True)

    def send_unreliable(self, addr: Addr, packet_type: str, data: Optional[dict] = None, scope: str = 'Game') -> int:
        return self.send_packet(addr, packet_type, data, scope, reliable=False)

    def broadcast_packet(
        self,
        addrs: Tuple[Addr],
        packet_type: str,
        data: Optional[dict] = None,
        scope: str = 'Game',
        *,
        reliable: Optional[bool] = None,
    ) -> Tuple[int]:
        if reliable is None:
            reliable = self.is_reliable_packet_type(packet_type)

        seq_list: list[int] = []
        for addr in addrs:
            seq = self.send_packet(addr, packet_type, data, scope, reliable=reliable)
            seq_list.append(seq)
        return tuple(seq_list)

    def broadcast_reliable(self, addrs: Tuple[Addr], packet_type: str, data: Optional[dict] = None, scope: str = 'Game') -> Tuple[int]:
        return self.broadcast_packet(addrs, packet_type, data, scope, reliable=True)

    def broadcast_unreliable(self, addrs: Tuple[Addr], packet_type: str, data: Optional[dict] = None, scope: str = 'Game') -> Tuple[int]:
        return self.broadcast_packet(addrs, packet_type, data, scope, reliable=False)

    def _send_raw_packet(self, addr: Addr, packet: Packet) -> None:
        raw_packet = json.dumps(packet).encode('utf-8')
        self.socket.sendto(raw_packet, addr)

    # ---------------- Receiving ----------------
    def poll(self) -> None | Tuple[Packet, Addr]:
        try:
            raw, addr = self.socket.recvfrom(65535)
        except (BlockingIOError, InterruptedError, OSError):
            return

        try:
            packet = json.loads(raw.decode('utf-8'))
        except Exception:
            print(f'[WARN] Invalid packet: {raw} from {addr}')
            return

        packet_type = packet.get('type')
        seq = packet.get('seq')

        # Incoming ACK
        if packet_type == 'ACK' and isinstance(seq, int):
            self._pending.pop(seq, None)
            self._completed_seq.setdefault(addr, set()).add(seq)
            return

        if isinstance(seq, int):
            is_reliable = self.is_reliable_packet_type(packet_type)
            if not is_reliable:
                return (packet, addr)

            seen = self._processed_seq.setdefault(addr, set())
            if seq in seen:
                self._send_ack(addr, seq)
                return
            seen.add(seq)
            self._send_ack(addr, seq)
            return (packet, addr)

        return (packet, addr)

    def _send_ack(self, addr: Addr, seq: int) -> None:
        self._send_raw_packet(addr, {'type': 'ACK', 'seq': seq})

    def update(self) -> None:
        """Resend un-ACKed packets and periodically trim sequence caches."""
        now = time.time()
        for seq, (addr, packet, last_time_sent, resend_try) in list(self._pending.items()):
            if now - last_time_sent >= self.resend_timeout and resend_try <= self.resend_tries:
                self._send_raw_packet(addr, packet)
                resend_try += 1
                self._pending[seq] = (addr, packet, now, resend_try)
            elif resend_try > self.resend_tries:
                self._pending.pop(seq)

        # Periodically clean up old sequence records
        if now - self.last_cleanup >= self.cleanup_interval:
            self._cleanup_sequences()
            self.last_cleanup = now

    def _cleanup_sequences(self) -> None:
        # Keep only last 20 (highest) sequences per address.
        for addr, seqs in list(self._processed_seq.items()):
            if not seqs:
                del self._processed_seq[addr]
                continue
            self._processed_seq[addr] = set(sorted(seqs)[-20:])

        for addr, seqs in list(self._completed_seq.items()):
            if not seqs:
                del self._completed_seq[addr]
                continue
            self._completed_seq[addr] = set(sorted(seqs)[-20:])

    def close_connection(self) -> None:
        self.socket.close()

    # ---------------- Getters and Setters ----------------
    def get_completed_seq(
        self,
        addr: Optional[Addr] = None,
        *,
        seq: Optional[int] = None,
    ) -> ItemsView[Addr, Set[int]] | set[int] | bool | None:
        """Check if outgoing packets got ACKed"""
        if addr is None and seq is None:
            return self._completed_seq.items()
        if addr and seq is None:
            return self._completed_seq.get(addr, set())
        if addr and seq:
            return seq in self._completed_seq.get(addr, set())
        return None
