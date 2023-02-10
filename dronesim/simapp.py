
from panda3d.core import (
    loadPrcFileData,
    VirtualFileSystem,
    VirtualFileMountSystem,
    Filename,
    getModelPath,
    ButtonHandle,
    KeyboardButton,
    Light,
    AmbientLight,
    LPoint3f, LVecBase3f, LPoint4f,
    NodePath, TextNode, SamplerState,
    TransparencyAttrib
)

from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.task.Task import Task

from . import PACKAGE_BASE
from .interface.control import IDroneControllable
from .utils import IterEnumMixin, HUDMixin
from .types import Vec4Tuple, DroneAction

from .cameracontrol import FreeCam, FPCamera, TPCamera
from .actor.uav import UAVDroneModel

import os
import glm
import enum
import typing
import logging
from dataclasses import dataclass

#Default config data
DEFAULT_CONFIG_VARS = """
win-size 1280 720
vfs-case-sensitive 0
window-title Drone Simulator
texture-minfilter mipmap
texture-anisotropic-degree 16
"""
loadPrcFileData("", DEFAULT_CONFIG_VARS)

#Instruct the Virtual File System to mount the real 'assets/' folder to the virtual directory '/assets/'
ASSETS = VirtualFileSystem.getGlobalPtr()
ASSETS.mount(
    VirtualFileMountSystem(Filename.from_os_specific(
        os.path.join(PACKAGE_BASE, 'assets/')
    )),
    '/assets/',
    VirtualFileSystem.MFReadOnly
)

#Add virtual assets directory to load models and scenes from to the Loader's search path
getModelPath().appendDirectory('/assets')

#Colors used for some HUD elements as foreground (text color) and background
HUD_COLORS = dict(
    fg=(1,1,1,1),
    bg=(0,0,0,0.2)
)

LOG = logging.getLogger(__name__)

def objectHUDFormatter(o):
    '''Simple JSON string formatter for various data types'''
    if isinstance(o, enum.Enum):
        return o.name
    if isinstance(o, float):
        return str(round(o, 2))
    if isinstance(o, glm.vec3) or isinstance(o, LPoint3f):
        return '[xyz] %.6f %.6f %.6f' % tuple(o)
    if isinstance(o, glm.vec4) or isinstance(o, LPoint4f):
        return '[xyzw] %.2f %.2f %.2f %.2f' % tuple(o)
    if isinstance(o, LVecBase3f):
        return '[hpr] %.2f %.2f %.2f' % tuple(o)
    return str(o)


class CameraMode(IterEnumMixin, enum.Enum):
    '''Cyclic iterable enum to get active camera'''

    #All cameras listed here will be cycled through by the user

    free = FreeCam()
    firstPerson = FPCamera()
    thirdPerson = TPCamera()

    def __call__(self, app, *args, **kwargs):
        self.value.assert_mode(app, *args, **kwargs)
    def update(self, dt : float, **kwargs):
        self.value.update(dt, **kwargs)
    def update_scroll(self, dir : float):
        self.value.update_scroll(dir)

    @property
    def state(self):
        return self.value.state()

class ControllingCharacter(IterEnumMixin, enum.Enum):
    '''Whether the user controls the camera or the UAV'''
    camera = enum.auto()
    player = enum.auto()


@dataclass(init=False)
class CameraController(HUDMixin):
    camMode : CameraMode = CameraMode.free
    mouseCapture : bool = True
    control : ControllingCharacter = ControllingCharacter.camera

    def __init__(self, *, app=None, **kwargs):
        self.app = app
        #Activate current (default) mode
        self()

    # Mostly just passthrough methods

    def __call__(self):
        self.camMode(
            self.app,
            mouseLocked=self.mouseCapture
        )

    def update(self, dt, **kwargs):
        self.camMode.update(
            dt = dt,
            **kwargs
        )

    def update_scroll(self, dir : float):
        self.camMode.update_scroll(dir)

class SimulatorApplication(ShowBase):
    '''
    Simulator app to render and control the UAV environment.
    It handles creating the simulator window, loading the scene, camera control,
    handling actors and user input.
    '''

    #Default scene to load (from virtual assets directory that is mounted. Can be anywhere, really)
    DEFAULT_SCENE = Filename("scenes/simple_loop.glb")

    def __init__(
            self,
            *uav_players : UAVDroneModel,
            scene_model : typing.Optional[typing.Union[str, os.PathLike, Filename, NodePath]] = DEFAULT_SCENE,
            default_lights : typing.List[Light] = [],
            **kwargs
        ):
        super().__init__(**kwargs)
        self.disableMouse() # Disable default mouse control
        self.render.setShaderAuto()

        #TODO: Test import, if fail, fallback to auto shader. Once done, make panda3d-simplepbr optional.
        import simplepbr
        simplepbr.init(enable_shadows=False)

        self._all_uavs : typing.List[UAVDroneModel] = list(uav_players)

        self.default_lights = default_lights

        #Add ambient lighting (minimum scene light)
        ambient = AmbientLight('ambient_dull_light')
        ambient.setColor((.1, .1, .1, 1))
        self.default_lights.append(ambient)

        #Scene graph (holds all scene models)
        self.scene_holder : NodePath = self.render.attachNewNode("environment_scene_holder")
        self.reset_scene()

        #Reparent all UAVs to the render node
        for uav in uav_players:
            uav.reparentTo(self.render)

        #Load given scene
        if scene_model is not None:
            self.load_attach_scene(scene_model)

        #State
        self.camState = CameraController(app=self)
        self.camera.setPos(0, -10, 10)
        self.camLens.setNear(0.1)
        self.debuggerState = dict()
        self.HUDState = dict()
        self._movementState : Vec4Tuple = None

        #Buffer viewer keybind
        self.accept("v", self.bufferViewer.toggleEnable)
        self.accept("V", self.bufferViewer.toggleEnable)

        #Keybinds for various operations
        self.accept("escape", self.eToggleMouseCapture)
        self.accept("wheel_up", self.eMouseWheelScroll, [1])
        self.accept("wheel_down", self.eMouseWheelScroll, [-1])
        self.accept("f1", self.eToggleHUDView)
        self.accept("f3", self.eToggleDebugView)
        self.accept("f5", self.eToggleCameraMode)
        self.accept("f6", self.eToggleControlMode)
        self.accept("f11", self.eToggleFullscreen)
        self.accept("\\", self.eHandleUAVStateDump)

        #UAV action keybinds
        self.accept("i", self.eHandleUAVCommandSend, [DroneAction.TAKEOFF])
        self.accept("k", self.eHandleUAVCommandSend, [DroneAction.LAND])

        #Tasks
        self.updateEngineTask = self.taskMgr.add(self.update_engine, "updateEngine")

        #HUD elements
        #TODO: Make a HUD class and put stuff in there and control it using methods
        HUD_PADDING = 0.08
        self.HUD_holder = DirectFrame(
            frameSize = (self.a2dLeft, self.a2dRight, self.a2dBottom, self.a2dTop),
            frameColor = (0, 0, 0, 0)
        )

        self.HUD_basic_info = OnscreenText(
            parent = self.HUD_holder,
            scale = 0.06,
            align = TextNode.ARight,
            pos = (self.a2dRight - HUD_PADDING/self.a2dRight/2, self.a2dTop - HUD_PADDING),
            mayChange = True,
            **HUD_COLORS
        )

        self.HUD_debug_info = OnscreenText(
            parent = self.HUD_holder,
            scale = 0.06,
            align = TextNode.ALeft,
            pos = (self.a2dLeft - HUD_PADDING/self.a2dLeft/2, self.a2dTop - HUD_PADDING),
            mayChange = True,
            **HUD_COLORS
        )
        #Hide debug view by default
        self.HUD_debug_info.hide()

        #Crosshair
        crosshair_tex = self.loader.loadTexture(
            Filename("textures/crosshair.png"),
            minfilter = SamplerState.FTNearest,
            magfilter = SamplerState.FTNearest
        )
        self.HUD_crosshair = OnscreenImage(
            parent = self.HUD_holder,
            image = crosshair_tex,
            pos = (0,0,0),
            scale = (0.12, 1, 0.12)
        )
        self.HUD_crosshair.setTransparency(TransparencyAttrib.MAlpha)
        self.HUD_crosshair.setColor((1,1,1,0.33))

    @property
    def activeUAVNode(self) -> typing.Optional[UAVDroneModel]:
        if len(self._all_uavs) > 0:
            return self._all_uavs[0]

    @property
    def activeUAVController(self) -> typing.Optional[IDroneControllable]:
        uav = self.activeUAVNode
        if uav:
            return uav.controller

    def update_engine(self, task : Task):
        '''Update all objects in the application'''
        self._movementState = self._getMovementControlState()
        self._updatePlayerMovementCommand()
        self._updateUAVObjects()
        self._updateCamera()
        self._updateHUD()
        return task.cont

    def reset_scene(self):
        self.render.clear_light()
        for light_node in self.default_lights:
            light = self.render.attachNewNode(light_node)
            self.render.setLight(light)

    def load_attach_scene(self, scene_path : typing.Union[str, os.PathLike, Filename, NodePath], position : LVecBase3f = (0,0,0), rotation : LVecBase3f = (0,0,0)):
        if isinstance(scene_path, NodePath):
            scene_model = scene_path
        else:
            scene_model = self.loader.loadModel(scene_path)
        self.attach_scene(scene_model)
        scene_model.setPos(position)
        scene_model.setHpr(rotation)

    def attach_scene(self, scene_model : NodePath):
        scene_model.reparentTo(self.scene_holder)
        self._setup_scene_lighting(scene_model)

    def _setup_scene_lighting(self, scene_model : NodePath):
        '''
        Move lights from scene to render node
        so that all objects are affected by it
        '''
        for light in scene_model.find_all_matches('**/+Light'):
            light.parent.wrt_reparent_to(self.render)
            self.render.setLight(light)

    def eToggleCameraMode(self):
        '''Keybind event handler to switch Camera Mode'''
        self.camState.camMode = next(self.camState.camMode)
        LOG.info("Changed cam to %s" % self.camState.camMode.name)
        self.camState()

    def eToggleMouseCapture(self):
        '''Keybind event handler to enable/disable Mouse capture'''
        self.camState.mouseCapture = not self.camState.mouseCapture
        LOG.info("Changed mouse capture to %s" % self.camState.mouseCapture)
        self.camState()

    def eMouseWheelScroll(self, dir):
        '''Mouse scroll wheel event handler to change camera property (fly speed, orbit size)'''
        self.camState.update_scroll(dir)

    def eToggleHUDView(self):
        '''Keybind event handler to show/hide the HUD'''
        if self.HUD_holder.isHidden():
            self.HUD_holder.show()
        else:
            self.HUD_holder.hide()

    def eToggleDebugView(self):
        '''Keybind event handler to show/hide debug view'''
        if self.HUD_debug_info.isHidden():
            self.HUD_debug_info.show()
        else:
            self.HUD_debug_info.hide()

    def eToggleControlMode(self):
        self.camState.control = next(self.camState.control)
        LOG.info("Changed control to '%s'" % self.camState.control)
        self.camState()

    def eToggleFullscreen(self):
        #FIXME native resolution and back
        '''
        new_wp = WindowProperties()
        old_wp = base.win.getProperties()

        #If already fullscreen, make windowed, else set to fullscreen
        if old_wp.getFullscreen():
            new_wp.setFullscreen(False)
        else:
            new_wp.setFullscreen(True)

        new_wp.setSize(1920,1080)
        base.win.requestProperties(new_wp)
        '''

    def eHandleUAVStateDump(self):
        '''Dump the current state object to stdout'''
        print(self.activeUAVController.get_current_state(), flush=True)

    def eHandleUAVCommandSend(self, cmd : DroneAction, **params):
        '''Send the given command (with parameters) to the active UAV controller'''
        player = self.activeUAVController
        if player:
            player.direct_action(cmd, **params)

    def _updateUAVObjects(self):
        for uav in self._all_uavs:
            uav.update()

    def _updateCamera(self):
        control = self._movementState if self.camState.control == ControllingCharacter.camera else None
        self.camState.update(globalClock.dt, mvVec=control)

    def _updatePlayerMovementCommand(self):
        player = self.activeUAVController
        if self._movementState is not None and player and self.camState.control == ControllingCharacter.player:
            player.rc_control(self._movementState)

    def _getMovementControlState(self) -> Vec4Tuple:
        #Returns whether a button/key is pressed
        isDown : typing.Callable[[ButtonHandle], bool] = self.mouseWatcherNode.isButtonDown

        btnFw = KeyboardButton.ascii_key('w')
        btnBw = KeyboardButton.ascii_key('s')
        btnL = KeyboardButton.ascii_key('a')
        btnR = KeyboardButton.ascii_key('d')

        btnLArrow = KeyboardButton.left()
        btnRArrow = KeyboardButton.right()
        btnUArrow = KeyboardButton.up()
        btnDArrow = KeyboardButton.down()

        state_lr = (isDown(btnR) - isDown(btnL))
        state_fwbw = (isDown(btnFw) - isDown(btnBw))
        state_yawlr = (isDown(btnRArrow) - isDown(btnLArrow))
        state_altud = (isDown(btnUArrow) - isDown(btnDArrow))

        #Order is the same as the arguments of 'StepRC' type
        return (state_lr, state_fwbw, state_altud, state_yawlr)

    def _updateHUD(self):
        self.HUD_basic_info.setText(self.formatDictToHUD(self.camState.hud(), serializer=objectHUDFormatter))

        uav = self.activeUAVController
        uav_debug_data = uav.get_debug_data() if uav else {}

        self.debuggerState.update({
            'fps': globalClock.getAverageFrameRate(),
            'uav': uav_debug_data,
            'camera': self.camState.camMode.state
        })
        self.HUD_debug_info.setText(
            self.formatDictToHUD(self.debuggerState, serializer=objectHUDFormatter)
        )

    @staticmethod
    def formatDictToHUD(d : dict, serializer : typing.Callable[[typing.Any], str] = str, level=0):
        return '\n'.join(
            '%s%s:\n%s' % (' '*level, k, SimulatorApplication.formatDictToHUD(v, serializer, level+1))
            if isinstance(v, dict)
            else (' '*level+k+': '+serializer(v))
            for k,v in d.items()
        )

