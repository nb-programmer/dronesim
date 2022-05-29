
from OpenGL import GL as gl
import numpy as np
import pygame

from typing import Iterable

class GLBuffer:
    def __init__(self):
        self._buff_id = gl.GLuint()
        self._buff_data = (gl.GLfloat*0)()
        gl.glGenBuffers(1, self._buff_id)
    def __call__(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._buff_id)
        return self
    def loadDataFloat(self, buffer_data : Iterable, operation : int = gl.GL_STATIC_DRAW):
        self()._buff_data = (gl.GLfloat * len(buffer_data))(*buffer_data)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, len(self._buff_data) * 4, self._buff_data, operation)
        return self
    def __len__(self):
        return len(self._buff_data)

class GLVertexArray(gl.GLuint):
    def __init__(self):
        gl.GLuint.__init__(self, gl.glGenVertexArrays(1))
        self()
    def __call__(self):
        gl.glBindVertexArray(self)

class GLUniform(gl.GLuint):
    def __init__(self, uniform_name, program_id):
        gl.GLuint.__init__(self, gl.glGetUniformLocation(program_id, uniform_name))
    def set2f(self, value):
        pass

class GLModel:
    def __init__(self):
        #Model's transformation matrix (world-space)
        self.model_matrix = np.identity(4)

    def _calculate_mvp(self, view_matrix : np.ndarray, projection_matrix : np.ndarray):
        #Multiply in reverse order, to convert to camera-space
        return projection_matrix @ view_matrix @ self.model_matrix

    def render(self, view_matrix : np.ndarray, projection_matrix : np.ndarray, shader_mvp : gl.GLuint):
        mvp = self._calculate_mvp(view_matrix, projection_matrix)
        self._renderModel(mvp)

    def _renderModel(self): pass

class GLMesh(GLModel):
    def __init__(self, mesh_data : GLBuffer):
        super().__init__()
        self._mesh = mesh_data
    def _renderModel(self):
        #Vertices at location 0
        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 4 * len(self._mesh))
        gl.glDrawArrays(gl.GL_STATIC_DRAW, 0, 3)

class GLTexture(gl.GLuint):
    def __init__(self, pygame_texture : pygame.Surface = None):
        gl.GLuint.__init__(self, gl.glGenTextures(1))
        self()
        if pygame_texture:
            img_data = pygame.surfarray.array3d(pygame_texture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, pygame_texture.get_width(), pygame_texture.get_height(), 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, img_data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR_MIPMAP_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)

    def __call__(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self)

class GLFramebuffer(gl.GLuint):
    def __init__(self, load_texture : GLTexture = None):
        gl.GLuint.__init__(self, gl.glGenFramebuffers(1))
        if load_texture:
            with self:
                gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, load_texture, 0)

    def __enter__(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self)
    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
