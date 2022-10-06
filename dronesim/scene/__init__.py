
import pygame

#Object-oriented GL library
from ..render import pygl, Dimension
from ..render.camera import Camera

from OpenGL import GL as gl
from OpenGL import GLU as glu

import numpy as np

class RenderableScene(pygame.Surface):
    def __init__(self, *args, size : Dimension = (320, 240), **kwargs):
        super().__init__(*args, size, **kwargs)
        self.camera = Camera()

        self.fbuftex = pygl.GLTexture(self)
        self.fbuf = pygl.GLFramebuffer(self.fbuftex)
        self._fbdata = None
        self.renderInit()
    def renderInit(self): pass
    def renderScene(self, viewport : Dimension, *args, **kwargs): pass
    def render(self, viewport : Dimension, *args, **kwargs):
        self.renderScene(viewport, *args, **kwargs)
    def isReady(self):
        return self._fbdata is not None
    def renderToFrameBuffer(self, pixel_format : gl.GLuint = gl.GL_BGR, to_array : bool = False, *args, **kwargs):
        with self.fbuf:
            self.renderScene(self.get_size(), *args, **kwargs)
            self._fbdata = gl.glReadPixels(0, 0, *self.get_size(), pixel_format, gl.GL_UNSIGNED_BYTE)
            if to_array and self.isReady():
                return self.readFBArray()
    def blitToFramebuffer(self, fb_id : gl.GLuint = 0, viewport : Dimension = None):
        if not viewport:
            viewport = self.get_size()
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, self.fbuf)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, fb_id)
        gl.glBlitFramebuffer(
            0, 0, *self.get_size(),
            0, 0, *viewport,
            gl.GL_COLOR_BUFFER_BIT,
            gl.GL_LINEAR
        )
    def readFBArray(self):
        if self._fbdata is None:
            return
        return np.frombuffer(self._fbdata, dtype=np.uint8).reshape((*self.get_size()[-1::-1], 3))

    def readRawBuffer(self):
        return self._fbdata
