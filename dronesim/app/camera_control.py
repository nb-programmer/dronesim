
from panda3d.core import (
    ClockObject,
    WindowProperties
)

from dronesim.utils import asarray, deg2rad, clamp, modulo, sin, cos

from direct.actor.Actor import Actor
from dronesim.types import InputState, StepRC
from typing import Tuple


FLYSPEED_DEFAULT = 15.0
FLYSPEED_MIN = 2.0
FLYSPEED_MAX = 500.0


class CameraControlBase:
    '''
    Base class for camera control
    This class on its own does not do anything with the camera, but it implements some useful
    utility functions
    '''

    def __init__(self, clock: ClockObject = None):
        if clock is None:
            clock = ClockObject()
        self._clock = clock
        self._lastTickTime = clock.real_time

    def assert_mode(self, app: "SimulatorApplication", mouseLocked: bool = None):
        self._app = app
        # Ignore an update so that mouse centering doesn't shift the view
        self._skip_update = 1

        if mouseLocked is None:
            if not hasattr(self, 'mouseLocked'):
                self.mouseLocked = False
        else:
            self.mouseLocked = mouseLocked

        # Update mouse lock mode
        if self.mouseLocked:
            self._mouseModeRelative()
        else:
            self._mouseModeUnlocked()

    def update_scroll(self, dir: float):
        pass

    def update(self, dt: float = None, **kwargs):
        '''Default camera update handler'''
        if self.mouseLocked:
            # Lock mouse to center if it is being captured
            self._grabMouseLockRelative()

    def state(self):
        return {
            'pos': self._app.camera.get_pos(),
            'facing': self._app.camera.get_hpr()
        }

    @staticmethod
    def restrict_hpr(hprVec, p_range: Tuple[float, float] = (-90, 90), r_range: Tuple[float, float] = (-90, 90)):
        h, p, r = hprVec
        h = modulo(h, 360)
        p, r = clamp((p, r), [p_range[0], r_range[0]],
                     [p_range[1], r_range[1]])
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
        md = win.get_pointer(0)
        x = md.get_x()
        y = md.get_y()
        cx, cy = win.get_x_size()//2, win.get_y_size()//2
        heading, pitch = 0, 0
        if win.move_pointer(0, cx, cy):
            heading = (x - cx) / cx
            pitch = (y - cy) / cy
        if self._skip_update > 0:
            self._skip_update -= 1
            return (0, 0)
        return (heading, pitch)

    def _mouseModeRelative(self):
        props = WindowProperties()
        props.set_cursor_hidden(True)
        props.set_mouse_mode(WindowProperties.M_relative)
        self._app.win.request_properties(props)

    def _mouseModeUnlocked(self):
        props = WindowProperties()
        props.set_cursor_hidden(False)
        props.set_mouse_mode(WindowProperties.M_absolute)
        self._app.win.request_properties(props)


class FreeCam(CameraControlBase):
    '''
    Implement Free camera (spectator view) movement

    It controls like Blender fly mode or Counter Strike spectator mode
    '''

    def __init__(self, flySpeed: float = FLYSPEED_DEFAULT, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._flySpeed = flySpeed

    def state(self):
        return {
            **super().state(),
            'flySpeed': self._flySpeed
        }

    def update_scroll(self, dir: float):
        # Inspired by Blender view3d fly
        time_wheel = self._getTickDiffTime()
        time_wheel = 1 + (10 - (20 * min(time_wheel, 0.5)))
        self._flySpeed += dir * time_wheel * 0.25
        self._flySpeed = min(max(self._flySpeed, FLYSPEED_MIN), FLYSPEED_MAX)

    def update(self,
               dt: float,
               lookSensitivity: float = 2000.0,
               input_state: InputState = None,
               **kwargs):

        hprVec = self._app.camera.get_hpr()
        xyzVec = self._app.camera.get_pos()
        mvVec: StepRC = None

        if input_state is not None:
            mvVec = input_state['movement_vec']

        if mvVec is None:
            mvVec = StepRC(0, 0, 0, 0)

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            # Mouse relative pitch and yaw
            hprVec[0] -= mx * lookSensitivity * dt
            hprVec[1] -= my * lookSensitivity * dt

        hprVec[0] -= mvVec.velr * lookSensitivity * 3e-2 * dt
        hprVec[1] += mvVec.velz * lookSensitivity * 3e-2 * dt

        hprVec = tuple(self.restrict_hpr(hprVec))
        self._app.camera.set_hpr(hprVec)

        # Get updated camera matrix
        camRotVecFB = self._app.camera.get_mat().get_row3(1)
        camRotVecLR = self._app.camera.get_mat().get_row3(0)
        camRotVecFB.normalize()
        camRotVecLR.normalize()

        # New camera position based on user control and camera facing direction.
        # This allows movement in any direction
        flyVec = camRotVecLR * mvVec.velx * self._flySpeed * \
            dt + camRotVecFB * mvVec.vely * self._flySpeed * dt
        self._app.camera.set_pos(xyzVec + flyVec)


class FlyCam(CameraControlBase):
    '''
    Implement Free camera movement

    It controls like Minecraft creative flying mode
    '''

    def update(self,
               dt: float,
               lookSensitivity: float = 2000.0,
               input_state: InputState = None,
               **kwargs):

        hprVec = self._app.camera.get_hpr()
        xyzVec = self._app.camera.get_pos()
        mvVec: StepRC = None

        if input_state is not None:
            mvVec = input_state['movement_vec']

        if mvVec is None:
            mvVec = StepRC(0, 0, 0, 0)

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            # Mouse relative pitch and yaw
            hprVec[0] -= mx * lookSensitivity * dt
            hprVec[1] -= my * lookSensitivity * dt

        hprVec = tuple(self.restrict_hpr(hprVec))
        self._app.camera.set_hpr(hprVec)

        # Get updated camera matrix
        camRotVecFB = self._app.camera.get_mat().get_row3(1)
        camRotVecLR = self._app.camera.get_mat().get_row3(0)
        camRotVecFB.normalize()
        camRotVecLR.normalize()

        # New camera position based on user control and camera facing direction.
        # This allows movement in any direction
        flyVec = camRotVecLR * mvVec[0] * dt + camRotVecFB * mvVec[1] * dt
        self._app.camera.set_pos(xyzVec + flyVec)


class FPCamera(CameraControlBase):
    '''
    Implements a first-person view camera.

    It will kind of feel like riding a boat in Minecraft
    '''

    def assert_mode(self, app: "SimulatorApplication", *args, **kwargs):
        super().assert_mode(app, *args, **kwargs)
        self._followObj: Actor = app.activeVehicleNode

    def update(self,
               dt: float,
               lookSensitivity: float = 2000.0,
               **kwargs):
        hprVec = self._app.camera.get_hpr()

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            # Mouse relative pitch and yaw
            hprVec[0] -= mx * lookSensitivity * dt
            hprVec[1] -= my * lookSensitivity * dt

        hprVec = tuple(self.restrict_hpr(hprVec))
        self._app.camera.set_hpr(hprVec)
        self._app.camera.set_pos(self._followObj.get_pos())


class TPCamera(CameraControlBase):
    '''
    Implements a third-person view camera.
    '''

    def __init__(self, orbit_radius: float = 30.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._orbit_radius = orbit_radius
        self._cam_hprVec = asarray([0, 0, 0], dtype=float)

    def state(self):
        return {
            **super().state(),
            'orbitRadius': self._orbit_radius
        }

    def update_scroll(self, dir: float):
        # Inspired by Blender view3d fly
        time_wheel = self._getTickDiffTime()
        time_wheel = 1 + (10 - (20 * min(time_wheel, 0.5)))
        self._orbit_radius += dir * time_wheel * 0.25
        self._orbit_radius = min(max(self._orbit_radius, 5.0), 50.0)

    def assert_mode(self, app: "SimulatorApplication", *args, **kwargs):
        super().assert_mode(app, *args, **kwargs)
        self._followObj: Actor = app.activeVehicleNode

    def update(self,
               dt: float,
               lookSensitivity: float = 2000.0,
               **kwargs):

        if self.mouseLocked:
            mx, my = self._grabMouseLockRelative()
            # Mouse relative pitch and yaw
            self._cam_hprVec[0] += mx * lookSensitivity * dt
            self._cam_hprVec[1] += my * lookSensitivity * dt

        # Limit pitch not exactly to +/-90 degree so that lookAt does not flip image when it is exactly 90
        self._cam_hprVec = self.restrict_hpr(
            self._cam_hprVec, p_range=(-89.999, 89.999))

        _target_pos = self._followObj.get_pos()
        heading_rads = deg2rad(self._cam_hprVec[0])
        pitch_rads = deg2rad(self._cam_hprVec[1])
        pitch_cos = cos(pitch_rads)

        # Orbit control
        _cam_orbit_xyz = (
            _target_pos[0] + sin(heading_rads) *
            pitch_cos * self._orbit_radius,
            _target_pos[1] + cos(heading_rads) *
            pitch_cos * self._orbit_radius,
            _target_pos[2] + sin(pitch_rads) * self._orbit_radius
        )

        self._app.camera.set_pos(_cam_orbit_xyz)
        self._app.camera.look_at(self._followObj)
