
from .scene import RenderableScene

import threading
import subprocess
import ffmpeg

from typing import Tuple

class SimulatedDroneViewStreamer(threading.Thread):
    def __init__(self, renderer : RenderableScene, stream_url : str = 'udp://127.0.0.1:2000', fps : float = 30):
        super().__init__()
        self._fps : float = fps
        self._renderer = renderer
        self._output_stream_path = stream_url
        self._res : Tuple[int, int] = self._renderer.get_size()
        self._stop : threading.Event = threading.Event()
        self.ffgraph = (ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='%dx%d' % self._res)
            .output(self._output_stream_path, listen=1, pix_fmt='yuv422p', format='mpegts')
            .overwrite_output())
        self.ffprocess : subprocess.Popen = None

    #Just so that I can use typing ^_^
    def _setProcess(self, proc : subprocess.Popen):
        self.ffprocess = proc

    def stop(self):
        self._stop.set()
        if self.ffprocess:
            self.ffprocess.terminate()
            self.ffprocess.wait()
            if not self.ffprocess.stdin.closed:
                self.ffprocess.stdin.close()

    def run(self):
        #Start the FFMpeg process, gobble stderr to hide output
        self._setProcess(self.ffgraph.run_async(pipe_stdin=True, quiet=True))
        while not self._stop.wait(timeout = (1 / self._fps)):
            if self._renderer.isReady():
                _frame = self._renderer.readRawBuffer()
                if _frame is not None:
                    #Can't handle with locks as write() is blocking when process isn't consuming stdin
                    #which results in a deadlock if a lock is used. So we just ignore the broken pipe
                    try:
                        if not self.ffprocess.stdin.closed:
                            self.ffprocess.stdin.write(_frame)
                            self.ffprocess.stdin.flush()
                    except (BrokenPipeError, OSError):
                        pass

    @property
    def stream_path(self):
        return self._output_stream_path
