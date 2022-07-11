
from OpenGL import GL as gl
from OpenGL import GLU as glu

from typing import Tuple

class Camera:
    def __init__(self):
        self.unit_to_px_factor = 50
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.xlook = 0.0
        self.ylook = 0.0
        self.zlook = 0.0
        self.tilt = 0.0
    def lookAt(self, where):
        pass
    def performWorldTransform(self, viewport : Tuple[int, int]):
        gl.glViewport(0, 0, *viewport)
        glu.gluPerspective(45, (viewport[0] / viewport[1]), 0.01, 5000.0)
        #TODO: glu.gluLookAt()
        gl.glRotatef(self.tilt, 0.0, 0.0, -1.0)
        gl.glTranslatef(-self.x * self.unit_to_px_factor, -self.y * self.unit_to_px_factor, -self.z * self.unit_to_px_factor)
