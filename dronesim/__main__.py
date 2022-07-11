
import os
from sre_parse import State
from xml.dom.pulldom import START_DOCUMENT
import numpy as np

import pygame
import pygame.locals

from OpenGL import GL as gl
from dronesim.render import pygl
from OpenGL.GL import shaders as glsl

# Simulated drone
from dronesim import DroneSimulator, DroneState, SimRPC, SimulatedDroneHandler
from dronesim.utils import callevery

# Scene rendering
from dronesim.render.scene import RenderableScene, Dimension
from dronesim.stream import SimulatedDroneViewStreamer

from typing import Tuple

package_base = os.path.dirname(__file__)
ASSET_PATH = os.path.join(package_base, 'assets')
SHADER_PATH = os.path.join(package_base, 'shaders')

class SimulatedDroneRenderer(RenderableScene):
    def renderInit(self):
        #Default background color
        gl.glClearColor(.1, .1, .1, 1)

        #Textures need to be enabled to be rendered
        gl.glEnable(gl.GL_TEXTURE_2D)

        #Enable Backface culling
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glCullFace(gl.GL_BACK)

        #Compile shaders and create shader program
        self._initShaders()

        self.tex_floor = pygl.GLTexture(pygame.image.load(os.path.join(ASSET_PATH, 'ceramic-tiles-texture-5.jpg')))
        self.tex_path = pygl.GLTexture(pygame.image.load(os.path.join(ASSET_PATH, 'loop.png')))

    def _initShaders(self):
        _shaders = []
        with open(os.path.join(SHADER_PATH, 'vertex.vs'), 'rb') as f: _shaders.append(glsl.compileShader(f.read(), gl.GL_VERTEX_SHADER))
        with open(os.path.join(SHADER_PATH, 'fragment.fs'), 'rb') as f: _shaders.append(glsl.compileShader(f.read(), gl.GL_FRAGMENT_SHADER))
        self.shader = glsl.compileProgram(*_shaders)
        self._mvp_uniform = pygl.GLUniform("MVP", self.shader)

    def renderScene(self, viewport : Dimension, state=None):
        '''
        Renders POV of drone's bottom camera in the current framebuffer
        '''

        if state is None: return
        observation, reward, done, info = state

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()

        # Move camera with the drone
        (_dx, _dy, _dz), (_dax, _day, _daz) = info['state'][:2]
        self.camera.x = _dx
        self.camera.y = _dy
        self.camera.z = _dz + 0.06  # Camera slightly higher than drone's feet
        self.camera.tilt = np.rad2deg(_daz)

        # We are moving the world relative to the camera
        self.camera.performWorldTransform(viewport)


        #with self.shader:
        
        self.RenderFloor()
        self.RenderPath()

    def RenderFloor(self):
        tex_s = 10
        self.tex_floor()
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(1,1,1)
        gl.glTexCoord2f(0,0)
        gl.glVertex3fv((-1000,-1000,0))
        gl.glTexCoord2f(tex_s,0)
        gl.glVertex3fv((1000,-1000,0))
        gl.glTexCoord2f(tex_s,tex_s)
        gl.glVertex3fv((1000,1000,0))
        gl.glTexCoord2f(0,tex_s)
        gl.glVertex3fv((-1000,1000,0))
        gl.glEnd()

    def RenderPath(self):
        self.tex_path()
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(1,1,1)
        gl.glTexCoord2f(0,0)
        gl.glVertex3fv((-100,-100,0))
        gl.glTexCoord2f(1,0)
        gl.glVertex3fv((100,-100,0))
        gl.glTexCoord2f(1,1)
        gl.glVertex3fv((100,100,0))
        gl.glTexCoord2f(0,1)
        gl.glVertex3fv((-100,100,0))
        gl.glEnd()

def prepareHUD(surface : pygl.GLTexture, drone : DroneSimulator):
    font = pygame.font.Font(None, 64)
    textSurface = font.render("Test", True, (255,255,255,40),
                              (0,0,0,20))
    ix, iy = textSurface.get_width(), textSurface.get_height()
    image = pygame.image.tostring(textSurface, "RGBX", True)
    surface()
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, ix, iy, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, image)

def renderTexture(tex : pygl.GLTexture):
    gl.glLoadIdentity()
    tex()
    gl.glBegin(gl.GL_QUADS)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-1.0/8, -1.0/8,  0.0)
    gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f( 1.0/8, -1.0/8,  0.0)
    gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f( 1.0/8,  1.0/8,  0.0)
    gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(-1.0/8,  1.0/8,  0.0)
    gl.glEnd()

@callevery(0.1)
def sendStateInfo(hdl : SimulatedDroneHandler, data):
    hdl.send(SimRPC(command="state", param=data))

class Action:
    data_timeout = 300
    data_timer = 0
    action_set = [0,0,0,0]


# Drone simulator window launcher

if __name__ == "__main__":
    START_POSITION = (-0.9, 0, 0)

    old_op = None

    #Drone simulator environment
    drone = DroneSimulator(START_POSITION)
    drone.reset()

    pygame.init()
    pygame.display.init()
    pygame.display.set_caption("Drone Renderer")
    window = pygame.display.set_mode((1280, 720), pygame.locals.HWSURFACE | pygame.locals.DOUBLEBUF | pygame.locals.OPENGL)
    hudTexture = pygl.GLTexture()

    droneRenderer = SimulatedDroneRenderer()
    droneHandler = SimulatedDroneHandler()

    # Stream drone POV over network
    droneStreamer = SimulatedDroneViewStreamer(droneRenderer)

    quit_flag = False
    droneAction = Action()

    def myHandler(cmd : SimRPC):
        d_cmd = cmd.command
        droneAction.data_timer = droneAction.data_timeout

        if d_cmd == 'takeoff':
            drone.takeoff()
        elif d_cmd == 'land':
            drone.land()
        elif d_cmd == 'rc':
            droneAction.action_set = list(cmd.param)
        elif d_cmd == 'vurl':
            droneHandler.send(SimRPC(command="videourl", param=droneStreamer.stream_path))

    #TODO: Pass drone simulator directly to control
    droneHandler.setCommandHandler(myHandler)
    #droneStreamer.start()

    #Takeoff immediately
    #drone.takeoff()

    #TODO: Object-oriented, and bind the methods below with it
    key_movement = {
    #Meta properties
    '__props': {
        'is_updated': False,
        'manual_override': False,
        'threshold': 0.1,
        'vec': [0,0,0,0],
        'cmdq': []
    },

    #Movement
    'fw': {
        'value': False,
        'bind': pygame.locals.K_w,
        'type': 'movement'
    },
    'bw': {
        'value': False,
        'bind': pygame.locals.K_s,
        'type': 'movement'
    },
    'sl': {
        'value': False,
        'bind': pygame.locals.K_a,
        'type': 'movement'
    },
    'sr': {
        'value': False,
        'bind': pygame.locals.K_d,
        'type': 'movement'
    },
    'rl': {
        'value': False,
        'bind': pygame.locals.K_LEFT,
        'type': 'movement'
    },
    'rr': {
        'value': False,
        'bind': pygame.locals.K_RIGHT,
        'type': 'movement'
    },
    'au': {
        'value': False,
        'bind': pygame.locals.K_UP,
        'type': 'movement'
    },
    'ad': {
        'value': False,
        'bind': pygame.locals.K_DOWN,
        'type': 'movement'
    },

    #Commands
    'tk': {
        'bind': pygame.locals.K_i,
        'type': 'command'
    },
    'ld' : {
        'bind': pygame.locals.K_k,
        'type': 'command'
    },
    'rst': {
        'bind': pygame.locals.K_r,
        'type': 'command'
    }
    }

    def updateMotionVecFromBind(binding):
        binding['__props']['vec'] = [
            binding['sr']['value'] - binding['sl']['value'],
            binding['fw']['value'] - binding['bw']['value'],
            binding['au']['value'] - binding['ad']['value'],
            binding['rr']['value'] - binding['rl']['value']
        ]

    def performDroneActionFromBind(action : str, drone : DroneSimulator):
        if action == 'tk':
            drone.takeoff()
        elif action == 'ld':
            drone.land()
        elif action == 'rst':
            drone.reset()

    while not quit_flag:
        for event in pygame.event.get():
            if event.type in [pygame.locals.QUIT]:
                quit_flag = True
            elif event.type == pygame.locals.KEYDOWN:
                for k,v in key_movement.items():
                    if k == '__props': continue
                    if v['bind'] == event.key:
                        key_movement['__props']['is_updated'] = True
                        if v['type'] == 'command':
                            key_movement['__props']['cmdq'].append(k)
                        else:
                            v['value'] = 1
                        break
            elif event.type == pygame.locals.KEYUP:
                for k,v in key_movement.items():
                    if k == '__props': continue
                    if v['bind'] == event.key:
                        key_movement['__props']['is_updated'] = True
                        if v['type'] != 'command':
                            v['value'] = 0
                        break

        #Drone commands (from input device)
        if key_movement['__props']['is_updated']:
            droneAction.data_timer = droneAction.data_timeout
            updateMotionVecFromBind(key_movement)
            key_movement['__props']['is_updated'] = False
            key_movement['__props']['manual_override'] = True

        #Actions
        key_commands : list = key_movement['__props']['cmdq']
        if len(key_commands):
            performDroneActionFromBind(key_commands.pop(0), drone)

        if key_movement['__props']['manual_override']:
            #Send control data if local movement
            droneAction.action_set = key_movement['__props']['vec']
            #Disable manual control once all controls are released
            if all([abs(x['value'] < key_movement['__props']['threshold']) for k,x in key_movement.items() if k != '__props' and 'value' in x]):
                key_movement['__props']['manual_override'] = False
        else:
            #Stop remote movement if timeout occurs
            if droneAction.data_timer > 0:
                droneAction.data_timer -= 1
            else:
                droneAction.action_set = [0,0,0,0]

        state = drone.step(droneAction.action_set)
        observation, reward, done, info = state

        #TODO: Drone's status to be defined in protocol
        cli_state = {
            'pos': info['state'].tolist(),
            'obs': observation,
            'fl': drone.operation == DroneState.IN_AIR,
            'st': True,
            'b': 100
        }
        if old_op != drone.operation:
            print("State changed to", drone.operation)
            old_op = drone.operation
        #sendStateInfo(droneHandler, cli_state)

        #Render for camera input, then for the user
        droneRenderer.renderToFrameBuffer(state=state)
        droneRenderer.render(viewport=window.get_size(), state=state)
        
        # prepareHUD(hudTexture, drone)
        # renderTexture(hudTexture)

        pygame.display.flip()

    droneStreamer.stop()
    pygame.quit()
