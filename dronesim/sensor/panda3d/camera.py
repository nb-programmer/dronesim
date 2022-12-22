
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

class Panda3DCameraSensor(NodePath, SensorBase):
    CAMERA_TYPE_RGB = GraphicsOutput.RTPColor
    CAMERA_TYPE_DEPTH = GraphicsOutput.RTPDepth

    def __init__(self, node_name : str, size : tuple = (512, 512), camera_type = CAMERA_TYPE_RGB):
        super().__init__(Camera(node_name, PerspectiveLens()))
        self.tex = Texture()
        self.texfbuf = None
        self.fbufsize = size
        self.camera_type = camera_type
    def update(self):
        '''Force render scene and return the image as a 'BGR' numpy array'''
        return
    def getViewportSize(self) -> tuple:
        return self.fbufsize
    def attachToEnv(self, scene : NodePath, gengine : GraphicsEngine, host_go : GraphicsOutput):
        #TODO: Check if this is even required
        self.node().setScene(scene)
        self.reparentTo(scene)
        
        #To render to the framebuffer, create a texture buffer
        _prop = FrameBufferProperties()
        #We need RGB and Depth
        _prop.setRgbColor(1)
        _prop.setDepthBits(1)

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

        self.texfbuf.addRenderTexture(self.tex, GraphicsOutput.RTMCopyRam, self.camera_type)

        #Create a DisplayRegion to be within the whole texture (left, right, bottom, top)
        dr = self.texfbuf.makeDisplayRegion(0,1,0,1)
        #Make camera render to this texture
        dr.setCamera(self)
