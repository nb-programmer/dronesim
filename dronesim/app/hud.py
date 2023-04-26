
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

from .attrib_presets import COLOR_BLEND_INVERT


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
    # Coord system of frame is (left, right, bottom, top), and defines the bounds of the card
    # Texture UV:
    #   U = X-axis (0=left, 1=right)
    #   V = Y-axis but from the bottom (1=bottom, 0=top)
    # So (0,1),(1,0) is the whole texture oriented from top-left to bottom-right.

    TEXTURE_UV_RANGE_DEFAULT = (LTexCoord(0,1), LTexCoord(1,0))
    def __init__(self,
                 name: str,
                 tex: Texture,
                 frame: Optional[Tuple[float,float,float,float]] = None,
                 tex_uv_range: Tuple[LTexCoord,LTexCoord] = TEXTURE_UV_RANGE_DEFAULT):
        super().__init__(name)
        self._ch = CardMaker('cm_%s' % name)
        if frame is None:
            # Use the whole space (for aspect2d it will fill the window as a best-fit square)
            self._ch.setFrameFullscreenQuad()
        else:
            # Position and size from given bounds
            self._ch.set_frame(*frame)
        self._ch.set_uv_range(*tex_uv_range)
        self._ch_node = self.attach_new_node(self._ch.generate())
        self._ch_node.set_texture(tex)
        self._ch_node.set_transparency(TransparencyAttrib.M_alpha)
        self._ch_node.set_attrib(COLOR_BLEND_INVERT)
