
import pygame
import pygame.locals

from OpenGL import GL as gl
from ..render import pygl

from OpenGL.GL import shaders as glsl
from . import RenderableScene, Dimension

from dronesim import PACKAGE_BASE

import os
import numpy as np

ASSET_PATH = os.path.join(PACKAGE_BASE, 'assets')
SHADER_PATH = os.path.join(PACKAGE_BASE, 'shaders')

class FlatPathMapScene(RenderableScene):
    def renderInit(self):
        #Default background color
        gl.glClearColor(.1, .1, .1, 1)

        #Textures need to be enabled to be rendered
        gl.glEnable(gl.GL_TEXTURE_2D)

        #Enable Backface culling
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)

        #Compile shaders and create shader program
        self._initShaders()

        self.tex_floor = pygl.GLTexture(pygame.image.load(os.path.join(ASSET_PATH, 'ceramic-tiles-texture-5.jpg')))
        self.tex_path = pygl.GLTexture(pygame.image.load(os.path.join(ASSET_PATH, 'loop.png')))

    def _initShaders(self):
        _shaders = []
        with open(os.path.join(SHADER_PATH, 'vertex.vert'), 'rb') as f: _shaders.append(glsl.compileShader(f.read(), gl.GL_VERTEX_SHADER))
        with open(os.path.join(SHADER_PATH, 'fragment.frag'), 'rb') as f: _shaders.append(glsl.compileShader(f.read(), gl.GL_FRAGMENT_SHADER))
        self.shader = glsl.compileProgram(*_shaders)
        self._mvp_uniform = pygl.GLUniform("MVP", self.shader)

    def renderScene(self, viewport : Dimension, state=None):
        '''
        Renders POV of drone's bottom camera in the current framebuffer
        '''

        if state is None: return
        observation, reward, done, info = state

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()

        # Move camera with the drone
        (_dx, _dy, _dz), (_dax, _day, _daz) = info['state']['pos'], info['state']['angle']
        self.camera.x = _dx
        self.camera.y = _dy
        self.camera.z = _dz + 0.06  # Camera slightly higher than drone's feet
        self.camera.tilt = np.rad2deg(_daz)

        # We are moving the world relative to the camera
        self.camera.performWorldTransform(viewport)


        #with self.shader:
        
        self.RenderFloor()
        self.RenderPath()

    def RenderFloor(self):
        tex_s = 10
        self.tex_floor()
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(1,1,1)
        gl.glTexCoord2f(0,0)
        gl.glVertex3fv((-1000,-1000,0))
        gl.glTexCoord2f(tex_s,0)
        gl.glVertex3fv((1000,-1000,0))
        gl.glTexCoord2f(tex_s,tex_s)
        gl.glVertex3fv((1000,1000,0))
        gl.glTexCoord2f(0,tex_s)
        gl.glVertex3fv((-1000,1000,0))
        gl.glEnd()

    def RenderPath(self):
        self.tex_path()
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(1,1,1)
        gl.glTexCoord2f(0,0)
        gl.glVertex3fv((-100,-100,0))
        gl.glTexCoord2f(1,0)
        gl.glVertex3fv((100,-100,0))
        gl.glTexCoord2f(1,1)
        gl.glVertex3fv((100,100,0))
        gl.glTexCoord2f(0,1)
        gl.glVertex3fv((-100,100,0))
        gl.glEnd()

