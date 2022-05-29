
import socket
import threading

from dronesim.protocol import SimRPC
from dronesim.utils import callevery

#TODO: Refine the protocol more: packetize better, add various attributes such as from the Tello drone, remote address set

class SimulatedDroneHandler:
    def __init__(self):
        self._commandHandler = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect(('127.0.0.1', 9989))
        self.rsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rsock.setblocking(0)
        self.rsock.bind(('127.0.0.1', 9988))
        self._rcvTh = threading.Thread(target=self._recv, daemon=True)
        self._rcvTh.start()

    def setCommandHandler(self, fn):
        self._commandHandler = fn

    def _recv(self):
        while self._rcvTh.is_alive():
            try:
                data = self.rsock.recv(4096)
                rpc = SimRPC.deserialize(data)
                if self._commandHandler:
                    self._commandHandler(rpc)
            except (BlockingIOError, ConnectionResetError):
                pass

    def send(self, rpc : SimRPC):
        self.sock.send(rpc.serialize())
    

class SimulatedDroneControl:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect(('127.0.0.1', 9988))
        self.rsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rsock.bind(('127.0.0.1', 9989))
        self.rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rsock.setblocking(0)
        self._rcvTh = threading.Thread(target=self._recv, daemon=True)
        self._rcvTh.start()
        self._state = {}
        self._vid_url = ""
    def _recv(self):
        while self._rcvTh.is_alive():
            try:
                data = self.rsock.recv(4096)
                rpc = SimRPC.deserialize(data)
                self.updateState(rpc)
            except (BlockingIOError, ConnectionResetError):
                pass
    def send(self, rpc : SimRPC):
        self.sock.send(rpc.serialize())
    def connect(self, *args, **kwargs):
        self._getVideoURL()
    def takeoff(self):
        self.send(SimRPC(command = 'takeoff'))
    def land(self):
        self.send(SimRPC(command = 'land'))
    @callevery(0.01)
    def send_rc_control(self, left_right_velocity: int, forward_backward_velocity: int, up_down_velocity: int, yaw_velocity: int):
        self.send(SimRPC(command = 'rc', param = (left_right_velocity/100, forward_backward_velocity/100, up_down_velocity/100, yaw_velocity/100)))
    def updateState(self, cmd):
        if cmd['command'] == 'state':
            self._state = cmd['param']
        elif cmd['command'] == 'videourl':
            self._vid_url = cmd['param']
    @callevery(0.5)
    def _getVideoURL(self):
        self.send(SimRPC(command = 'vurl'))
    def streamon(self):
        self._getVideoURL()
    def streamoff(self):
        pass

    def get_current_state(self):
        return self._state

    @property
    def is_flying(self):
        return self._state.get('fl', False)
    @property
    def stream_on(self):
        return self._state.get('st', False)
    def get_battery(self):
        return self._state.get('b', 0)
    def get_udp_video_address(self):
        return self._vid_url
    def move_left(self, x : int):
        pass
    def move_right(self, x : int):
        pass
    def move_up(self, x : int):
        pass
    def move_down(self, x : int):
        pass
    def rotate_clockwise(self, x : int):
        pass
    def rotate_counterclockwise(self, x : int):
        pass
