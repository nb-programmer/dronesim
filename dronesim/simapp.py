
from panda3d.core import (
    loadPrcFileData,
    getModelPath,
    Filename,
    WindowProperties,
    ButtonHandle,
    KeyboardButton,
    AmbientLight,
    LPoint3f, LVecBase3f, LPoint4f,
    NodePath, TextNode
)

import simplepbr

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task

from . import PACKAGE_BASE
from .simulator import DroneSimulator
from .interface.control import IDroneControllable
from .utils import IterEnumMixin, HUDMixin, rad2deg

import os
import glm
import enum
import typing
import random
import logging
from dataclasses import dataclass

#Default config data
DEFAULT_CONFIG_VARS = """
win-size 1280 720
window-title Drone Simulator
texture-minfilter mipmap
texture-anisotropic-degree 16
"""
loadPrcFileData("", DEFAULT_CONFIG_VARS)

#Add package directory to load assets
getModelPath().appendDirectory(Filename.from_os_specific(PACKAGE_BASE))

HUD_COLORS = dict(
    fg=(1,1,1,1),
    bg=(0,0,0,0.2)
)

LOG = logging.getLogger(__name__)

def objectHUDFormatter(o):
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

class CameraControlBase:
    def assertMode(self, app : ShowBase, mouseLocked : bool = None):
        self._app = app
        #Ignore an update so that mouse centering doesn't shift the view
        self._skip_update = 1

        if mouseLocked is None:
            if not hasattr(self, 'mouseLocked'):
                self.mouseLocked = False
        else:
            self.mouseLocked = mouseLocked

        #Update mouse lock mode
        if self.mouseLocked:
            self._mouseModeRelative()
        else:
            self._mouseModeUnlocked()
            
    def update(self, dt : float = None, **kwargs):
        '''Default camera update handler'''
        if self.mouseLocked:
            #Lock mouse to center if it is being captured
            self._grabMouseLockRelative()
    
    def state(self):
        return {
            'pos': self._app.camera.getPos(),
            'facing': self._app.camera.getHpr()
        }

    def _grabMouseLockRelative(self):
        '''
        Returns relative motion of mouse by locking it in the center of the window.
        Returns X and Y relative movement.
        '''
        win = self._app.win
        md = win.getPointer(0)
        x = md.getX()
        y = md.getY()
        cx, cy = win.getXSize()//2, win.getYSize()//2
        heading, pitch = 0, 0
        if win.movePointer(0, cx, cy):
            heading = (x - cx) / cx
            pitch = (y - cy) / cy
        if self._skip_update > 0:
            self._skip_update -= 1
            return (0, 0)
        return (heading, pitch)
    def _mouseModeRelative(self):
        props = WindowProperties()
        props.setCursorHidden(True)
        props.setMouseMode(WindowProperties.M_relative)
        self._app.win.requestProperties(props)
    def _mouseModeUnlocked(self):
        props = WindowProperties()
        props.setCursorHidden(False)
        props.setMouseMode(WindowProperties.M_absolute)
        self._app.win.requestProperties(props)
    def _getMovementControlState(self):
        #Returns if button is pressed
        isDown : typing.Callable[[ButtonHandle], bool] = self._app.mouseWatcherNode.isButtonDown

        btnFw = KeyboardButton.ascii_key('w')
        btnBw = KeyboardButton.ascii_key('s')
        btnL = KeyboardButton.ascii_key('a')
        btnR = KeyboardButton.ascii_key('d')
        state_fwbw = (isDown(btnFw) - isDown(btnBw))
        state_lr = (isDown(btnR) - isDown(btnL))

        return (state_fwbw, state_lr, 0.0, 0.0)

class FreeCam(CameraControlBase):
    def update(self,
               dt : float,
               flySpeed : float = 30.0,
               lookSensitivity : float = 2000.0,
               **kwargs):
        '''
        Implement Free camera (spectator view) movement
        '''
        hprVec = self._app.camera.getHpr()
        xyzVec = self._app.camera.getPos()

        #Get user movement control
        mvVec = self._getMovementControlState()
        
        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            #Mouse relative pitch and yaw
            hprVec[0] -= mx * lookSensitivity * dt
            hprVec[1] -= my * lookSensitivity * dt
            
        self._app.camera.setHpr(hprVec)

        #Get updated camera matrix
        camRotVecFB = self._app.camera.getMat().getRow3(1)
        camRotVecLR = self._app.camera.getMat().getRow3(0)
        camRotVecFB.normalize()
        camRotVecLR.normalize()

        #New camera position based on user control and camera facing direction
        flyVec = camRotVecFB * mvVec[0] * flySpeed * dt + camRotVecLR * mvVec[1] * flySpeed * dt
        self._app.camera.setPos(xyzVec + flyVec)

class CameraMode(IterEnumMixin, enum.Enum):
    free = FreeCam()
    firstPerson = CameraControlBase()
    thirdPerson = CameraControlBase()
    
    def __call__(self, app, *args, **kwargs):
        self.value.assertMode(app, *args, **kwargs)
    def update(self, dt : float, **kwargs):
        self.value.update(dt, **kwargs)

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
    flySpeed : float = 15.0
    control : ControllingCharacter = ControllingCharacter.camera

    #HUD field visibility
    def __shouldshow__(self, field : str):
        if field == 'flySpeed' or field == 'control':
            return self.camMode == CameraMode.free
        return True

    def __init__(self, *, app=None, **kwargs):
        self.app = app
        #Activate current (default) mode
        self()

    def __call__(self):
        self.camMode(
            self.app,
            mouseLocked=self.mouseCapture
        )

    def update(self, dt):
        self.camMode.update(
            dt = dt,
            flySpeed = self.flySpeed
        )

class UAVDroneModel(Actor):
    '''
    Model class for a UAV Drone (quad, hex)-copter with separate Shell and propeller models.
    The model object can be synced to a state object via a IDroneControllable interface object.

    :param IDroneControllable update_source: Optional drone interface to update position/rotation with every update() call.
    If not specified, you can pass the state in the update(state).

    :param dict propellers indicates the set of bones to use in the model to attach propellers.
    the key is the name of the bone, and value is the model asset file name or NodePath object.
    The number of propellers would indicate the type of drone it is.

    :param dict propeller_spin indicates direction of spin for the given propeller bones, where value of
    '1' is clockwise, and '-1' is anti-clockwise. Direction is set to clockwise to any bones with unspecified direction.
    
    
    Default propeller layout is the 'Quad X' frame arrangement
    
    '''
    def __init__(self,
                 update_source : IDroneControllable = None,
                 shell_model : typing.Union[NodePath, os.PathLike] = None,
                 propellers : typing.Dict[str, typing.Union[NodePath, os.PathLike]] = None,
                 propeller_spin : typing.Dict[str, float] = None):
        self._update_source = update_source
        if shell_model is None:
            shell_model = "assets/models/quad-shell.glb"
        
        #Default propeller models
        if propellers is None:
            prop_model_cw = "assets/models/propeller.glb"
            prop_model_ccw = prop_model_cw #Temporary

            propellers = {
                "PropellerJoint1": prop_model_ccw,
                "PropellerJoint2": prop_model_ccw,
                "PropellerJoint3": prop_model_cw,
                "PropellerJoint4": prop_model_cw
            }
            if propeller_spin is None:
                propeller_spin = {
                    "PropellerJoint1": -1,
                    "PropellerJoint2": -1,
                    "PropellerJoint3": 1,
                    "PropellerJoint4": 1
                }
        
        if propeller_spin is None:
            propeller_spin = dict()
            
        propeller_spin.update({k: 1 for k in propellers.keys() if k not in propeller_spin})

        #Prefix so that it doesn't clash with original bone node
        propeller_parts = {'p_%s'%k:v for k,v in propellers.items()}
        
        self.joints = {'propellers': {}}

        super().__init__({
            'modelRoot': shell_model,
            **propeller_parts
        }, anims={'modelRoot': {}}) #To use the multipart w/o LOD loader (this is the way to do it)
        
        for bone in propellers.keys():
            #Make node accessible
            self.exposeJoint(None, 'modelRoot', bone)
            self.attach('p_%s'%bone, "modelRoot", bone)
            control_node = self.controlJoint(None, 'modelRoot', bone)

            self.joints['propellers'][bone] = {
                'bone': control_node,
                'spinDir': propeller_spin[bone]
            }
            #Random rotation
            control_node.setH(random.randint(0,360))
    
    def update(self, state : dict = None):
        if state is None and self._update_source is not None:
            state = self._update_source.get_current_state()
        if state is not None:
            transformState = state.get('state')
            if transformState is not None:
                self.setPos(*transformState['pos'])
                rotx, roty, rotz = transformState['angle']
                self.setHpr(rad2deg(rotz), rad2deg(roty), rad2deg(rotx)) #TODO: Need more transformations for pitch and roll
                thrust = transformState['thrust']
                prop_vel = thrust.z * 1e5

                for bone in self.joints['propellers'].values():
                    #Rotate with respect to spin direction and thrust
                    bone['bone'].setH(bone['bone'].getH() + prop_vel*bone['spinDir'])

        super().update()
        
class SimulatorApplication(ShowBase):
    '''
    '''
    def __init__(self,
                 drone : IDroneControllable,
                 scene_path : os.PathLike = None,
                 use_simplepbr_renderer : bool = True,
                 drone_model : Actor = None,
                 **kwargs
        ):
        super().__init__(**kwargs)
        base.disableMouse() # Disable default mouse control

        self.drone : IDroneControllable = drone
        
        if use_simplepbr_renderer:
            simplepbr.init(enable_shadows=False)
        else:
            self.render.setShaderAuto()

        #Scene
        self.scene = self._loadScene(scene_path)

        #Drone object
        if drone_model is None:
            drone_model = UAVDroneModel()

        self.droneModel = drone_model
        self.droneModel.reparentTo(self.render)
        
        #Add ambient lighting (minimum scene light)
        ambient = self.render.attachNewNode(AmbientLight('ambientDullLight'))
        ambient.node().setColor((.1, .1, .1, 1))
        self.render.setLight(ambient)
        
        #State
        self.camState = CameraController(app=self)
        self.camera.setPos(0, -10, 10)
        self.camLens.setNear(0.1)
        self.droneState = None
        self.debuggerState = dict(visible=False, items={})
        self.HUDState = dict(visible=True)
        
        self.accept("v", self.bufferViewer.toggleEnable)
        self.accept("V", self.bufferViewer.toggleEnable)
        
        #Events
        self.accept("escape", self.eToggleMouseCapture)
        self.accept("wheel_up", self.eMouseWheelScroll, [1])
        self.accept("wheel_down", self.eMouseWheelScroll, [-1])
        self.accept("f3", self.eToggleDebugView)
        self.accept("f5", self.eToggleCameraMode)
        self.accept("f6", self.eToggleControlMode)
        self.accept("f11", self.eToggleFullscreen)
        
        #Tasks
        self.updateEngineTask = self.taskMgr.add(self.updateEngine, "updateEngine")
        
        #HUD elements
        self.camHUDText = OnscreenText(
            parent = self.a2dTopRight,
            scale = 0.06,
            align = TextNode.ARight,
            pos = (-0.03, -0.1),
            **HUD_COLORS
        )
        self.debugHUDText = OnscreenText(
            parent = self.a2dTopLeft,
            scale = 0.06,
            align = TextNode.ALeft,
            pos = (0.03, -0.1),
            **HUD_COLORS
        )
        
    def getUAVModelNode(self) -> Actor:
        return self.droneModel

    def updateEngine(self, task : Task):
        '''Update all objects in the app'''
        self._updateDroneObject()
        self._updateCamera()
        self._updateHUD()
        return task.cont

    def loadScene(self, scene_path : os.PathLike):
        self.scene = self._loadScene(scene_path)
        
    def _loadScene(self, scene_path : os.PathLike) -> NodePath:
        if scene_path is None:
            scene_path = "assets/scenes/simple_loop.glb"
        sceneModel = self.loader.loadModel(scene_path)
        sceneModel.setPos(0,0,0)
        sceneModel.reparentTo(self.render)
        
        #Move scene lighting to root (render) node
        #So that all objects are affected by it
        sceneModel.clear_light()
        for light in sceneModel.find_all_matches('**/+Light'):
            light.parent.wrt_reparent_to(self.render)
            self.render.setLight(light)

        return sceneModel
        
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
        '''Mouse scroll wheel event handler to change Fly speed'''
        #Adjust fly speed based on direction of scroll
        self.camState.flySpeed += dir * 0.25
        self.camState.flySpeed = min(max(self.camState.flySpeed, 5.0), 50.0)

    def eToggleDebugView(self):
        '''Keybind event handler to show/hide debug view'''
        self.debuggerState['visible'] = not self.debuggerState['visible']

    def eToggleControlMode(self):
        self.camState.control = next(self.camState.control)
        LOG.info("Changed control to '%s'" % self.camState.control)
        self.camState()

    def eToggleFullscreen(self): pass

    def _updateDroneObject(self):
        self.droneState = self.drone.get_current_state()
        self.droneModel.update(self.droneState)

    def _updateCamera(self):
        self.camState.update(globalClock.dt)

    def _updateHUD(self):
        if not self.HUDState['visible']:
            self.camHUDText.setText('')
            self.debugHUDText.setText('')
            return
        
        self.camHUDText.setText(self.formatDictToHUD(self.camState.hud(), serializer=objectHUDFormatter))
        
        self.debuggerState['items'].update({
            'fps': globalClock.getAverageFrameRate(),
            'drone': self.droneState,
            'camera': self.camState.camMode.state
        })
        dbgInfo, dbgVis = self.debuggerState['items'], self.debuggerState['visible']
        self.debugHUDText.setText(
            self.formatDictToHUD(dbgInfo, serializer=objectHUDFormatter)
            if dbgVis else ''
        )

    @staticmethod
    def formatDictToHUD(d : dict, serializer : typing.Callable[[typing.Any], str] = str, level=0):
        return '\n'.join(
            '%s%s:\n%s' % (' '*level, k, SimulatorApplication.formatDictToHUD(v, serializer, level+1))
            if isinstance(v, dict)
            else (' '*level+k+': '+serializer(v))
            for k,v in d.items()
        )

