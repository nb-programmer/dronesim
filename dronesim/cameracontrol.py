from panda3d.core import (
    ClockObject,
    WindowProperties
)

from .utils import asarray, deg2rad, clamp, modulo, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from .types import Vec4Tuple
import typing

class CameraControlBase:
    def __init__(self, clock : ClockObject = None):
        if clock is None:
            clock = ClockObject()
        self._clock = clock
        self._lastTickTime = clock.real_time

    def assert_mode(self, app : ShowBase, mouseLocked : bool = None):
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

    def update_scroll(self, dir : float):
        pass

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

    @staticmethod
    def restrict_Hpr(hprVec, p_range : typing.Tuple[float, float] = (-90,90), r_range : typing.Tuple[float, float] = (-90,90)):
        h, p, r = hprVec
        h = modulo(h, 360)
        p, r = clamp((p, r), [p_range[0], r_range[0]], [p_range[1], r_range[1]])
        return asarray([h, p, r])

    def _getTickDiffTime(self):
        currTickTime = self._clock.real_time
        tickPeriod = currTickTime - self._lastTickTime
        self._lastTickTime = currTickTime
        return tickPeriod

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

class FreeCam(CameraControlBase):
    '''
    Implement Free camera (spectator view) movement
    '''
    def __init__(self, flySpeed : float = 15.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._flySpeed = flySpeed

    def state(self):
        return {
            **super().state(),
            'flySpeed': self._flySpeed
        }

    def update_scroll(self, dir : float):
        #Inspired by Blender view3d fly
        time_wheel = self._getTickDiffTime()
        time_wheel = 1 + (10 - (20 * min(time_wheel, 0.5)))
        self._flySpeed += dir * time_wheel * 0.25
        self._flySpeed = min(max(self._flySpeed, 2.0), 100.0)

    def update(self,
               dt : float,
               lookSensitivity : float = 2000.0,
               mvVec : Vec4Tuple = None,
               **kwargs):

        hprVec = self._app.camera.getHpr()
        xyzVec = self._app.camera.getPos()

        if mvVec is None:
            mvVec = (0,)*4

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            #Mouse relative pitch and yaw
            hprVec[0] -= mx * lookSensitivity * dt
            hprVec[1] -= my * lookSensitivity * dt

        hprVec = tuple(self.restrict_Hpr(hprVec))
        self._app.camera.setHpr(hprVec)

        #Get updated camera matrix
        camRotVecFB = self._app.camera.getMat().getRow3(1)
        camRotVecLR = self._app.camera.getMat().getRow3(0)
        camRotVecFB.normalize()
        camRotVecLR.normalize()

        #New camera position based on user control and camera facing direction.
        #This allows movement in any direction
        flyVec = camRotVecLR * mvVec[0] * self._flySpeed * dt + camRotVecFB * mvVec[1] * self._flySpeed * dt
        self._app.camera.setPos(xyzVec + flyVec)

class FPCamera(CameraControlBase):
    '''
    Implements a first-person view camera.

    It will kind of feel like riding a boat in Minecraft
    '''

    def assert_mode(self, app : ShowBase, *args, **kwargs):
        super().assert_mode(app, *args, **kwargs)
        self._followObj : Actor = app.activeUAVNode

    def update(self,
               dt : float,
               lookSensitivity : float = 2000.0,
               **kwargs):
        hprVec = self._app.camera.getHpr()

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            #Mouse relative pitch and yaw
            hprVec[0] -= mx * lookSensitivity * dt
            hprVec[1] -= my * lookSensitivity * dt

        hprVec = tuple(self.restrict_Hpr(hprVec))
        self._app.camera.setHpr(hprVec)
        self._app.camera.setPos(self._followObj.getPos())


class TPCamera(CameraControlBase):
    '''
    Implements a third-person view camera.
    '''

    def __init__(self, orbit_radius : float = 30.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orbit_radius = orbit_radius
        self._cam_hprVec = asarray([0,0,0], dtype=float)

    def state(self):
        return {
            **super().state(),
            'orbitRadius': self._orbit_radius
        }

    def update_scroll(self, dir : float):
        #Inspired by Blender view3d fly
        time_wheel = self._getTickDiffTime()
        time_wheel = 1 + (10 - (20 * min(time_wheel, 0.5)))
        self._orbit_radius += dir * time_wheel * 0.25
        self._orbit_radius = min(max(self._orbit_radius, 5.0), 50.0)

    def assert_mode(self, app : ShowBase, *args, **kwargs):
        super().assert_mode(app, *args, **kwargs)
        self._followObj : Actor = app.activeUAVNode

    def update(self,
               dt : float,
               lookSensitivity : float = 2000.0,
               **kwargs):

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            #Mouse relative pitch and yaw
            self._cam_hprVec[0] += mx * lookSensitivity * dt
            self._cam_hprVec[1] += my * lookSensitivity * dt

        #Limit pitch not exactly to +/-90 degree so that lookAt does not flip image when it is exactly 90
        self._cam_hprVec = self.restrict_Hpr(self._cam_hprVec, p_range=(-89.999,89.999))

        _target_pos = self._followObj.getPos()
        heading_rads = deg2rad(self._cam_hprVec[0])
        pitch_rads = deg2rad(self._cam_hprVec[1])
        pitch_cos = cos(pitch_rads)

        #Orbit control
        _cam_orbit_xyz = (
            _target_pos[0] + sin(heading_rads) * pitch_cos * self._orbit_radius,
            _target_pos[1] + cos(heading_rads) * pitch_cos * self._orbit_radius,
            _target_pos[2] + sin(pitch_rads) * self._orbit_radius
        )

        self._app.camera.setPos(_cam_orbit_xyz)
        self._app.camera.lookAt(self._followObj)
