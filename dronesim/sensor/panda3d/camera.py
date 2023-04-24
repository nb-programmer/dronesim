
from ..sensor import SensorBase
from panda3d.core import (
    NodePath,
    Camera,
    PerspectiveLens,
    Texture,
    GraphicsEngine,
    GraphicsOutput,
    GraphicsPipe,
    WindowProperties,
    FrameBufferProperties
)

import numpy as np


# Maps Panda3D's data type enum to numpy's data types for use in conversion
COMPONENTTYPE_DTYPE_MAP = {
    Texture.T_unsigned_byte: np.uint8,
    Texture.T_unsigned_short: np.short,
    Texture.T_float: np.float32,
    Texture.T_unsigned_int_24_8: np.int32
}


class Panda3DCameraSensor(NodePath, SensorBase):
    CAMERA_TYPE_RGB = GraphicsOutput.RTPColor
    CAMERA_TYPE_DEPTH = GraphicsOutput.RTPDepth

    def __init__(self, node_name: str, size: tuple = (512, 512), camera_type=CAMERA_TYPE_RGB):
        super().__init__(Camera(node_name, PerspectiveLens()))
        self.tex = Texture()
        self.__last_frame = np.zeros((1, 1, 3))
        self.texfbuf = None
        self.fbufsize = size
        self.camera_type = camera_type

    def update(self):
        '''Render into the framebuffer and return the captured image as a numpy array'''
        # self.render_and_get_framebuffer()
        return self.__last_frame

    def get_viewport_size(self) -> tuple:
        return self.fbufsize

    def render_and_get_framebuffer(self) -> np.ndarray:
        '''
        Read the current texture data as a numpy array similar to OpenCV's Mat image format.

        In order to get the latest frame, you can call `base.graphicsEngine.renderFrame()` before calling this
        so that the scene gets rendered. This must also be done if you have a headless instance with just the
        graphicsEngine else no image will form.
        '''
        # TODO: Add a parameter for blocking till buffer copy done

        # Make sure the rendered frame has reached into the buffer in system memory
        is_rendered = self.tex.mightHaveRamImage()
        if is_rendered:
            # Get texture data that was loaded into memory
            fbdata = self.tex.getRamImage()

            # What type of data will be stored in the buffer
            # This is needed in order to convert it back to a numpy buffer correctly
            dtype = COMPONENTTYPE_DTYPE_MAP.get(
                self.tex.component_type, np.uint8)

            fb_array = np.frombuffer(fbdata, dtype)
            channels = self.tex.getNumComponents()
            if channels == 1:
                # Single channel image does not need extra dimension
                fb_array = np.reshape(fb_array, (
                    self.tex.getYSize(),
                    self.tex.getXSize()
                ))
            else:
                fb_array = np.reshape(fb_array, (
                    self.tex.getYSize(),
                    self.tex.getXSize(),
                    self.tex.getNumComponents()
                ))

            # Update to latest frame. Textures are laid out as if on quadrant I of a cartesian plane
            # so we need to flip it to get it into pixel coordinates
            self.__last_frame = np.flipud(fb_array)
        return is_rendered, self.__last_frame

    def attach_to_env(self, scene: NodePath, gengine: GraphicsEngine, host_go: GraphicsOutput):
        # TODO: Check if this is even required
        self.node().set_scene(scene)

        # To render to the framebuffer, create a texture buffer
        _prop = FrameBufferProperties()
        # We need RGB and Depth
        _prop.setRgbColor(1)
        # _prop.setDepthBits(1)

        self.texfbuf = gengine.makeOutput(
            host_go.getPipe(),
            "fbtex_%s" % self.name,
            0,
            _prop,
            WindowProperties(size=self.fbufsize),
            GraphicsPipe.BFRefuseWindow,
            host_go.getGsg(),
            host_go
        )

        self.texfbuf.addRenderTexture(
            self.tex, GraphicsOutput.RTMCopyRam, self.camera_type)

        # Create a DisplayRegion to be within the whole texture (left, right, bottom, top)
        dr = self.texfbuf.makeDisplayRegion(0, 1, 0, 1)
        # Make camera render to this texture
        dr.setCamera(self)
