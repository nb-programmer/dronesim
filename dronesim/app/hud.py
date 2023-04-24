
import dataclasses

from panda3d.core import (
    NodePath,
    CardMaker,
    Texture,
    TransparencyAttrib,
    LTexCoord
)
from direct.gui.DirectGui import DirectFrame, OnscreenImage
from typing import Optional, Tuple


# TODO: Cleanup required

class HUDFieldMixin:
    '''HUD field to nested dictionary with visibility flag for a dataclass'''

    def hud(self):
        return {k.name: getattr(self, k.name) for k in dataclasses.fields(self) if self.__shouldshow__(k.name)}

    def __shouldshow__(self, field: str): return True


class HUDFrame(DirectFrame):
    def __init__(self, parent: Optional[NodePath] = None, **kwargs):
        super().__init__(parent=parent, **kwargs)

class Crosshair(NodePath):
    # Coord system is (left, right, bottom, top), and defines the bounds of the card
    FRAME_RANGE_DEFAULT = (-1,1,-1,1) # Same as using setFrameFullscreenQuad() on the CardMaker
    TEXTURE_UV_RANGE_DEFAULT = (LTexCoord(0,0), LTexCoord(1,-1))
    def __init__(self,
                 name: str,
                 tex: Texture,
                 frame: Tuple[float,float,float,float] = FRAME_RANGE_DEFAULT,
                 tex_uv_range: Tuple[LTexCoord,LTexCoord] = TEXTURE_UV_RANGE_DEFAULT):
        super().__init__(name)
        self._ch = CardMaker('cm_%s' % name)
        self._ch.set_frame(*frame)
        self._ch.set_uv_range(*tex_uv_range)
        self._ch_node = self.attach_new_node(self._ch.generate())
        self._ch_node.set_texture(tex)
        self._ch_node.set_transparency(TransparencyAttrib.MAlpha)
