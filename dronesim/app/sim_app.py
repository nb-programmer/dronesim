
from panda3d.core import (
    loadPrcFileData,
    VirtualFileSystem,
    VirtualFileMountSystem,
    Filename,
    getModelPath,
    ButtonHandle,
    KeyboardButton,
    DirectionalLight,
    Spotlight,
    LPoint3f, LVecBase3f, LPoint4f,
    NodePath, TextNode, SamplerState,
    LTexCoord,
    PStatClient
)

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.task.Task import Task

from dronesim._base import PACKAGE_BASE
from dronesim.interface import IDroneControllable, DroneAction
from dronesim.utils import IterEnumMixin, square_aspect2d_frame

from .hud import HUDFieldMixin, HUDFrame, Crosshair
from .environment import Panda3DEnvironment
from .camera_control import FreeCam, FPCamera, TPCamera
from .asset_manager import JSONLoader

from dronesim.actor import VehicleModel

import os
import glm
import enum
import logging
from dataclasses import dataclass

from dronesim.types import InputState, PandaFilePath, StepRC
from typing import Optional, Union, Callable, List, Any

# Default config data for the app. You can set your own by using
# loadPrcFileData or a config file before creating the Application.
DEFAULT_CONFIG_VARS = """
vfs-case-sensitive 0

window-title Drone Simulator
win-size 1280 720

textures-power-2 up
texture-minfilter mipmap
texture-anisotropic-degree 8
"""
loadPrcFileData("", DEFAULT_CONFIG_VARS)

# Instruct the Virtual File System to mount the real 'assets/' folder to the virtual directory '/assets/'
ASSETS_VFS = VirtualFileSystem.get_global_ptr()
ASSETS_VFS.mount(
    VirtualFileMountSystem(Filename.from_os_specific(
        os.path.join(PACKAGE_BASE, 'assets/')
    )),
    '/assets/',
    VirtualFileSystem.MFReadOnly
)

# Add virtual assets directory to load models and scenes from to the loader's search path
getModelPath().prepend_directory('/assets')

# Colors used for some HUD elements as foreground (text color) and background
HUD_COLORS = dict(
    fg=(1, 1, 1, 1),
    bg=(0, 0, 0, 0.2)
)

LOG = logging.getLogger(__name__)


def objectHUDFormatter(o):
    '''Simple JSON string formatter for various data types'''
    if isinstance(o, enum.Enum):
        # Get name of the enum value
        return o.name
    if isinstance(o, float):
        # Simple float
        return str(round(o, 2))
    if isinstance(o, glm.vec3) or isinstance(o, LPoint3f):
        # 3-D vector representing a point in 3-D space
        return '[xyz] %.6f %.6f %.6f' % tuple(o)
    if isinstance(o, glm.vec4) or isinstance(o, LPoint4f):
        # 4-D vector representing a point in 4-D space
        return '[xyzw] %.2f %.2f %.2f %.2f' % tuple(o)
    if isinstance(o, LVecBase3f):
        # A base vector, denotes angle from origin
        return '[hpr] %.2f %.2f %.2f' % tuple(o)
    # Convert to string for others
    return str(o)


class CameraMode(IterEnumMixin, enum.Enum):
    '''Cyclic iterable enum to get active camera'''

    # All cameras listed here will be cycled through by the user

    free = FreeCam()
    firstPerson = FPCamera()
    thirdPerson = TPCamera()

    def __call__(self, app, *args, **kwargs):
        self.value.assert_mode(app, *args, **kwargs)

    def update(self, dt: float, **kwargs):
        self.value.update(dt, **kwargs)

    def update_scroll(self, dir: float):
        self.value.update_scroll(dir)

    @property
    def state(self):
        return self.value.state()


class ControllingCharacter(IterEnumMixin, enum.Enum):
    '''Whether the user controls the camera or the Vehicle'''
    camera = enum.auto()
    player = enum.auto()


@dataclass(init=False)
class CameraController(HUDFieldMixin):
    camMode: CameraMode = CameraMode.free
    mouseCapture: bool = True
    control: ControllingCharacter = ControllingCharacter.camera

    def __init__(self, *, app=None, **kwargs):
        self.app = app
        # Activate current (default) mode
        self()

    # Mostly just passthrough methods

    def __call__(self):
        self.camMode(
            self.app,
            mouseLocked=self.mouseCapture
        )

    def update(self, dt, **kwargs):
        self.camMode.update(
            dt=dt,
            **kwargs
        )

    def update_scroll(self, dir: float):
        self.camMode.update_scroll(dir)


class SimulatorApplication(ShowBase):
    '''
    Simulator app to render and control the drone within the environment.
    It handles creating the simulator window, handle the environment, camera control,
    handling entities and user input.
    '''

    DEFAULT_ASSETS = "/assets/assets.json"

    def __init__(
        self,
        env: Panda3DEnvironment,
        *entities: Union[Actor, VehicleModel],
        assets_file: PandaFilePath = DEFAULT_ASSETS,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.disable_mouse()  # Disable default mouse control (NOTE: Misleading name!)
        self.external_shader_pipelines = []
        self._assets_load_file = assets_file

        # Object that will handle events by hooking handlers to them.
        # A separate object is created (rather than using `self`) so that default
        # hooks of `ShowBase` don't get overridden.
        # See: https://discourse.panda3d.org/t/issue-when-using-base-accept-window-event-and-also-setting-window-size-outside-of-window-event/28959/2
        self._event_hook = DirectObject()

        # Holds all entities (and vehicles) to be updated
        self._entities: List[Actor] = []

        # Entity graph (holds all scene models)
        self.entity_holder: NodePath = self.render.attach_new_node(
            "entity_holder")
        # Scene graph (holds all scene models)
        self.scene_holder: NodePath = self.render.attach_new_node(
            "environment_holder")

        # Add all entities passed to the application
        self.add_entity(*entities)

        # Attach environment
        env.reparent_to(self.scene_holder)

        self.reset_lights()

        self.camera.set_pos(0, -10, 10)
        self.camLens.set_near(0.1)

        # State
        self.camState = CameraController(app=self)
        self.debuggerState = dict()
        self.HUDState = dict()
        self.input_state: InputState = dict(
            movement_vec=None,
            is_jump_pressed=False,
            is_crouch_pressed=False,
            is_dash=False
        )

        # Vehicle action keybinds
        self.accept("i", self.eHandleVehicleCommandSend, [DroneAction.TAKEOFF])
        self.accept("k", self.eHandleVehicleCommandSend, [DroneAction.LAND])

        # Tasks
        self.updateEngineTask = self.taskMgr.add(
            self.update_engine, "updateEngine")

        # HUD elements
        self._init_ui()

    def add_entity(self, *entity: Actor):
        self._entities.extend(entity)

        # Reparent all entities to the entity holder node
        for e in entity:
            e.reparent_to(self.entity_holder)

    @property
    def vehicles(self) -> List[VehicleModel]:
        '''Filters all attached entities for VehicleModel objects.'''
        return list(filter(lambda x: isinstance(x, VehicleModel), self._entities))

    @property
    def activeVehicleNode(self) -> Optional[VehicleModel]:
        '''Returns the active (selected) vehicle object, if any.'''
        v_list = self.vehicles
        if len(v_list) > 0:
            # TODO: Add a way for user to select one of these using dropdown and keybind
            return v_list[0]

    @property
    def activeVehicleController(self) -> Optional[IDroneControllable]:
        '''Returns the controller instance of the active (selected) vehicle object, if any.'''
        vehicle = self.activeVehicleNode
        if vehicle:
            return vehicle.controller

    def update_engine(self, task: Task):
        '''Update all objects in the application'''
        self._updateInputState()
        self._updatePlayerMovementCommand()
        self._updateEntities()
        self._updateCamera()
        self._update_hud()
        return task.cont

    def reset_lights(self):
        '''Causes a search throughout the whole environment graph for `Light` entities and
        move them to the main render node, so that they affect the entire scene (and entities).'''

        self.render.clear_light()
        for light in self.scene_holder.find_all_matches('**/+Light'):
            light.parent.wrt_reparent_to(self.render)
            self.render.set_light(light)

            # Light types that can cast shadows
            if isinstance(light.node(), (DirectionalLight, Spotlight)):
                # Make the light render this render path for the shadow map
                light.node().set_scene(self.render)
                light.node().set_shadow_caster(True, 512, 512)

    def attach_shader_pipeline(self, pipeline_obj):
        pass
        '''self.pbr_pipeline = simplepbr.Pipeline(
            enable_shadows=False,
            enable_fog=False
        )'''

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
        '''Start connection with Pandas' PStats server, or disconnects from it'''
        self._toggle_pstats_connection()

    def eToggleControlMode(self):
        self.camState.control = next(self.camState.control)
        LOG.info("Changed control to '%s'" % self.camState.control)
        self.camState()

    def eToggleFullscreen(self):
        # FIXME native resolution and back
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

    def eWindowEvent(self, window):
        if window.properties.has_foreground() and not window.properties.foreground:
            if self.camState.mouseCapture:
                LOG.info("Window lost focus, disabling mouse capture")
                self.camState.mouseCapture = False
                self.camState()

    def eHandleVehicleStateDump(self):
        '''Dump the current state object of the active Vehicle to stdout'''
        print(self.activeVehicleController.get_current_state(), flush=True)

    def eHandleVehicleCommandSend(self, cmd: DroneAction, **params):
        '''Send the given command (with parameters) to the active Vehicle controller'''
        player = self.activeVehicleController
        if player:
            player.direct_action(cmd, **params)

    def _updateInputState(self):
        self.input_state['movement_vec'] = self._getMovementControlState()
        if self.input_state['movement_vec'].vely > 0.25:
            if self.is_button_down(KeyboardButton.control()):
                self.input_state['is_dash'] = True
        else:
            self.input_state['is_dash'] = False

        self.input_state['is_jump_pressed'] = self.is_button_down(
            KeyboardButton.space())
        self.input_state['is_crouch_pressed'] = self.is_button_down(
            KeyboardButton.shift())

    def _updateEntities(self):
        for entity in self._entities:
            entity.update()

    def _updateCamera(self):
        control = self.input_state if self.camState.control == ControllingCharacter.camera else None
        self.camState.update(globalClock.dt, input_state=control)

    def _updatePlayerMovementCommand(self):
        player = self.activeVehicleController
        mv_vec = self.input_state['movement_vec']
        if mv_vec is not None and player and self.camState.control == ControllingCharacter.player:
            player.rc_control(mv_vec)

    def print_scene_graph(self):
        '''Print hierarchy of the `scene` graph'''
        self.scene_holder.ls()

    def print_render_graph(self):
        '''Print hierarchy of the entire render graph'''
        self.render.ls()

    def is_button_down(self, btn: ButtonHandle) -> bool:
        '''Returns whether a button/key is pressed'''
        return self.mouseWatcherNode.isButtonDown(btn)

    def _toggle_pstats_connection(self):
        if not PStatClient.isConnected():
            LOG.info("Attempting connection with PStats server...")
            PStatClient.connect()
        else:
            LOG.info("Disconnecting from PStats server")
            PStatClient.disconnect()

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
        state_yawlr = (self.is_button_down(btnRArrow) -
                       self.is_button_down(btnLArrow))
        state_altud = (self.is_button_down(btnUArrow) -
                       self.is_button_down(btnDArrow))

        return StepRC(state_lr, state_fwbw, state_altud, state_yawlr)

    # App/UI related

    def _init_assets(self):
        assets = JSONLoader.load(
            self.loader, self._assets_load_file, ASSETS_VFS)
        # TODO

    def _init_keybinds(self):
        # Buffer viewer keybind
        self._event_hook.accept("v", self.bufferViewer.toggleEnable)
        self._event_hook.accept("V", self.bufferViewer.toggleEnable)

        # Keybinds for various operations
        self._event_hook.accept("escape", self.eToggleMouseCapture)
        self._event_hook.accept("wheel_up", self.eMouseWheelScroll, [1])
        self._event_hook.accept("wheel_down", self.eMouseWheelScroll, [-1])
        self._event_hook.accept("shift-wheel_up", self.eMouseWheelScroll, [0.25])
        self._event_hook.accept("shift-wheel_down", self.eMouseWheelScroll, [-0.25])
        self._event_hook.accept("f1", self.eToggleHUDView)
        self._event_hook.accept("f3", self.eToggleDebugView)
        self._event_hook.accept("shift-f3", self.eConnectPStats)
        self._event_hook.accept("f5", self.eToggleCameraMode)
        self._event_hook.accept("f6", self.eToggleControlMode)
        self._event_hook.accept("f11", self.eToggleFullscreen)
        self._event_hook.accept("\\", self.eHandleVehicleStateDump)

        self._event_hook.accept("window-event", self.eWindowEvent)

    def _init_hud(self):
        # TODO: Make a HUD class and put stuff in there and control it using methods
        HUD_PADDING = 0.08
        self.HUD_holder = HUDFrame(
            parent=self.aspect2d,
            frameSize=(self.a2dLeft, self.a2dRight,
                       self.a2dBottom, self.a2dTop),
            frameColor=(1, 1, 1, 0)
        )

        self.HUD_basic_info = OnscreenText(
            parent=self.HUD_holder,
            scale=0.06,
            align=TextNode.ARight,
            pos=(self.a2dRight - HUD_PADDING /
                 self.a2dRight/2, self.a2dTop - HUD_PADDING),
            mayChange=True,
            **HUD_COLORS
        )

        self.HUD_debug_info = OnscreenText(
            parent=self.HUD_holder,
            scale=0.06,
            align=TextNode.ALeft,
            pos=(self.a2dLeft - HUD_PADDING/self.a2dLeft /
                 2, self.a2dTop - HUD_PADDING),
            mayChange=True,
            **HUD_COLORS
        )
        # Hide debug view by default
        self.HUD_debug_info.hide()

        # Crosshair
        crosshair_tex = self.loader.loadTexture(
            Filename("/assets/textures/ui_1.png"),
            minfilter=SamplerState.FT_nearest,
            magfilter=SamplerState.FT_nearest
        )
        self.HUD_crosshair = Crosshair(
            "player_crosshair",
            crosshair_tex,
            frame=square_aspect2d_frame(0.015),
            tex_uv_range=(LTexCoord(4/128,-4/128),LTexCoord(12/128,-12/128))
        )
        self.HUD_crosshair.reparent_to(self.HUD_holder)

    def _update_hud(self):
        if not self.HUD_holder.isHidden():
            self.HUD_basic_info.setText(self.formatDictToHUD(
                self.camState.hud(), serializer=objectHUDFormatter))

            if not self.HUD_debug_info.isHidden():
                vehicle = self.activeVehicleController
                vehicle_debug_data = vehicle.get_debug_data() if vehicle else {}

                self.debuggerState.update({
                    'fps': globalClock.getAverageFrameRate(),
                    'input': self.input_state,
                    'active_vehicle': vehicle_debug_data,
                    'camera': self.camState.camMode.state
                })
                self.HUD_debug_info.setText(
                    self.formatDictToHUD(
                        self.debuggerState, serializer=objectHUDFormatter)
                )

    def _init_ui(self):
        self._init_keybinds()
        self._init_assets()
        self._init_hud()

    @classmethod
    def formatDictToHUD(cls, d: dict, serializer: Callable[[Any], str] = str, level=0) -> str:
        return '\n'.join(
            '%s%s:\n%s' % (
                ' '*level, k, cls.formatDictToHUD(v, serializer, level+1))
            if isinstance(v, dict)
            else (' '*level+k+': '+serializer(v))
            for k, v in d.items()
        )
