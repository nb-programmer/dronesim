
from panda3d.core import (
    loadPrcFileData,
    VirtualFileSystem,
    VirtualFileMountSystem,
    Filename,
    getModelPath,
    ButtonHandle,
    KeyboardButton,
    Light,
    DirectionalLight,
    Spotlight,
    AmbientLight,
    LPoint3f, LVecBase3f, LPoint4f,
    NodePath, PandaNode, TextNode, SamplerState,
    TransparencyAttrib,
    PStatClient
)

from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import DirectFrame
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.task.Task import Task

from . import PACKAGE_BASE
from .interface import IDroneControllable, DroneAction
from .utils import IterEnumMixin, HUDMixin
from .types import InputState, StepRC

from .cameracontrol import FreeCam, FPCamera, TPCamera
from .actor.uav import UAVDroneModel

import simplepbr

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
ASSETS_VFS = VirtualFileSystem.getGlobalPtr()
ASSETS_VFS.mount(
    VirtualFileMountSystem(Filename.from_os_specific(
        os.path.join(PACKAGE_BASE, 'assets/')
    )),
    '/assets/',
    VirtualFileSystem.MFReadOnly
)

#Add virtual assets directory to load models and scenes from to the loader's search path
getModelPath().prepend_directory('/assets')

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
            attach_lights : typing.List[typing.Union[Light, NodePath]] = [],
            enable_dull_ambient_light : bool = True,
            **kwargs
        ):
        super().__init__(**kwargs)
        self.disableMouse() # Disable default mouse control

        self.pbr_pipeline = simplepbr.Pipeline(
            enable_shadows=False,
            enable_fog=False
        )

        self._all_uavs : typing.List[UAVDroneModel] = list(uav_players)
        self.attach_lights = attach_lights

        #Add ambient lighting (minimum scene light)
        if enable_dull_ambient_light:
            ambient = AmbientLight('ambient_dull_light')
            ambient.setColor((.1, .1, .1, 1))
            self.attach_lights.append(ambient)

        #Scene graph (holds all scene models)
        self.scene_holder : NodePath = self.render.attachNewNode("environment_scene_holder")
        self.reset_scene()

        #Reparent all UAVs to the render node
        for uav in uav_players:
            uav.instance_to(self.render)

        #Load given scene
        if scene_model is not None:
            self.load_attach_scene(scene_model)

        self.camera.setPos(0, -10, 10)
        self.camLens.setNear(0.1)

        #State
        self.camState = CameraController(app=self)
        self.debuggerState = dict()
        self.HUDState = dict()
        self.input_state = InputState(
            movement_vec=None,
            is_jump_pressed=False,
            is_crouch_pressed=False,
            is_dash=False
        )

        #Buffer viewer keybind
        self.accept("v", self.bufferViewer.toggleEnable)
        self.accept("V", self.bufferViewer.toggleEnable)

        #Keybinds for various operations
        self.accept("escape", self.eToggleMouseCapture)
        self.accept("wheel_up", self.eMouseWheelScroll, [1])
        self.accept("wheel_down", self.eMouseWheelScroll, [-1])
        self.accept("f1", self.eToggleHUDView)
        self.accept("f3", self.eToggleDebugView)
        self.accept("shift-f3", self.eConnectPStats)
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
        self._updateInputState()
        self._updatePlayerMovementCommand()
        self._updateUAVObjects()
        self._updateCamera()
        self._updateHUD()
        return task.cont

    def reset_scene(self):
        self.render.clear_light()
        for light_node in self.attach_lights:
            if isinstance(light_node, Light):
                light = self.render.attachNewNode(light_node)
            elif isinstance(light_node, NodePath):
                light = light_node
                light.reparentTo(self.render)

            if isinstance(light.node(), (DirectionalLight, Spotlight)):
                light.node().setScene(self.render)
                light.node().setShadowCaster(True, 512, 512)
            self.render.setLight(light)

    def load_attach_scene(self,
            scene_path : typing.Union[str, os.PathLike, Filename, NodePath],
            position : LVecBase3f = (0,0,0),
            rotation : LVecBase3f = (0,0,0)) -> NodePath:
        if isinstance(scene_path, (str, os.PathLike, Filename)):
            #Load scene from given path
            scene_model = self.loader.loadModel(scene_path)
        elif isinstance(scene_path, NodePath):
            scene_model = scene_path
        elif isinstance(scene_path, PandaNode):
            scene_model = NodePath(scene_path)
        else:
            raise TypeError("Argument `scene_path` is not a valid type.")
        self.attach_scene(scene_model)
        scene_model.setPos(position)
        scene_model.setHpr(rotation)
        return scene_model

    def attach_scene(self, scene_model : NodePath):
        scene_model.instance_to(self.scene_holder)
        self._setup_scene_lighting(scene_model)

    def _setup_scene_lighting(self, scene_model : NodePath):
        '''
        Move lights from scene to render node
        so that all objects are affected by it
        '''
        for light in scene_model.find_all_matches('**/+Light'):
            light.parent.wrt_reparent_to(self.render)
            light.node().set_shadow_caster(True, 512, 512)
            self.render.set_light(light)

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

    def eConnectPStats(self):
        '''Start connection with Pandas' PStats server'''
        if not PStatClient.isConnected():
            PStatClient.connect()
        else:
            PStatClient.disconnect()

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

    def _updateInputState(self):
        self.input_state['movement_vec'] = self._getMovementControlState()
        if self.input_state['movement_vec'].vely > 0.25:
            if self.is_button_down(KeyboardButton.control()):
                self.input_state['is_dash'] = True
        else:
            self.input_state['is_dash'] = False

        self.input_state['is_jump_pressed'] = self.is_button_down(KeyboardButton.space())
        self.input_state['is_crouch_pressed'] = self.is_button_down(KeyboardButton.shift())

    def _updateUAVObjects(self):
        for uav in self._all_uavs:
            uav.update()

    def _updateCamera(self):
        control = self.input_state if self.camState.control == ControllingCharacter.camera else None
        self.camState.update(globalClock.dt, input_state=control)

    def _updatePlayerMovementCommand(self):
        player = self.activeUAVController
        mv_vec = self.input_state['movement_vec']
        if mv_vec is not None and player and self.camState.control == ControllingCharacter.player:
            player.rc_control(mv_vec)

    def _updateHUD(self):
        self.HUD_basic_info.setText(self.formatDictToHUD(self.camState.hud(), serializer=objectHUDFormatter))

        uav = self.activeUAVController
        uav_debug_data = uav.get_debug_data() if uav else {}

        self.debuggerState.update({
            'fps': globalClock.getAverageFrameRate(),
            'input': self.input_state,
            'active_uav': uav_debug_data,
            'camera': self.camState.camMode.state
        })
        self.HUD_debug_info.setText(
            self.formatDictToHUD(self.debuggerState, serializer=objectHUDFormatter)
        )

    def print_scene_graph(self):
        '''Print hierarchy of the `scene` graph'''
        self.scene_holder.ls()

    def print_render_graph(self):
        '''Print hierarchy of the entire render graph'''
        self.render.ls()

    def is_button_down(self, btn : ButtonHandle) -> bool:
        '''Returns whether a button/key is pressed'''
        return self.mouseWatcherNode.isButtonDown(btn)

    def _getMovementControlState(self) -> StepRC:
        btnFw = KeyboardButton.ascii_key('w')
        btnBw = KeyboardButton.ascii_key('s')
        btnL = KeyboardButton.ascii_key('a')
        btnR = KeyboardButton.ascii_key('d')

        btnLArrow = KeyboardButton.left()
        btnRArrow = KeyboardButton.right()
        btnUArrow = KeyboardButton.up()
        btnDArrow = KeyboardButton.down()

        state_lr = (self.is_button_down(btnR) - self.is_button_down(btnL))
        state_fwbw = (self.is_button_down(btnFw) - self.is_button_down(btnBw))
        state_yawlr = (self.is_button_down(btnRArrow) - self.is_button_down(btnLArrow))
        state_altud = (self.is_button_down(btnUArrow) - self.is_button_down(btnDArrow))

        return StepRC(state_lr, state_fwbw, state_altud, state_yawlr)

    @staticmethod
    def formatDictToHUD(d : dict, serializer : typing.Callable[[typing.Any], str] = str, level=0):
        return '\n'.join(
            '%s%s:\n%s' % (' '*level, k, SimulatorApplication.formatDictToHUD(v, serializer, level+1))
            if isinstance(v, dict)
            else (' '*level+k+': '+serializer(v))
            for k,v in d.items()
        )
