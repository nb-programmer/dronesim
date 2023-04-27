
from panda3d.core import (
    LColor,
    ColorBlendAttrib
)
COLOR_BLEND_INVERT = ColorBlendAttrib.make(
    ColorBlendAttrib.M_subtract,
    ColorBlendAttrib.O_constant_color, ColorBlendAttrib.O_one,
    LColor(0.5,0.5,0.5,0)
)
