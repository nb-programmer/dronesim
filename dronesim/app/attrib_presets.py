
from panda3d.core import (
    LColor,
    ColorBlendAttrib
)
COLOR_BLEND_INVERT = ColorBlendAttrib.make(
    ColorBlendAttrib.M_subtract,
    ColorBlendAttrib.O_constant_color, ColorBlendAttrib.O_one,
    LColor(0.5,0.5,0.5,0)
)

# COLOR_BLEND_INVERT = ColorBlendAttrib.make(
#     rgb_mode=ColorBlendAttrib.M_max,
#     rgb_a=ColorBlendAttrib.OOne,
#     rgb_b=ColorBlendAttrib.O_one_minus_incoming_color,

#     alpha_mode = ColorBlendAttrib.M_max,
#     alpha_a=ColorBlendAttrib.OOne,
#     alpha_b=ColorBlendAttrib.O_one_minus_incoming_alpha
# )
