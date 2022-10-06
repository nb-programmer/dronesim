

#Windows's scaling issue
import ctypes
ctypes.windll.user32.SetProcessDPIAware()

import pygame
import pygame.locals

#Typing
from .simulator import DroneSimulator
from .scene import RenderableScene

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


class SimulatorApplication:
    '''
    PyGame application to simulate a drone and render the scene in a window
    '''

    window_surface : pygame.Surface = None
    quit_flag : bool = False

    @classmethod
    def AppInit(cls, window_title = "Simulator"):
        pygame.init()
        pygame.display.init()
        pygame.display.set_caption(window_title)
        cls.window_surface = pygame.display.set_mode((1280, 720), pygame.locals.HWSURFACE | pygame.locals.DOUBLEBUF | pygame.locals.OPENGL)
        
    @classmethod
    def AppDel(cls):
        pygame.quit()
        
    def __init__(self, drone : DroneSimulator, scene : RenderableScene):
        self.drone : DroneSimulator = drone
        self.scene : RenderableScene = scene
        
    def loop(self):
        while not self.quit_flag:
            for event in pygame.event.get():
                if event.type in [pygame.locals.QUIT]:
                    #Exit loop
                    self.quit_flag = True
                    break
                
                elif event.type == pygame.locals.KEYDOWN:
                    self._handleKeyPress(event)
                elif event.type == pygame.locals.KEYUP:
                    self._handleKeyRelease(event)
                    

            self._handleControl()
            state = self.drone.step(None)
            self.scene.render(self.window_surface.get_size(), state=state)

            #Swap buffers
            pygame.display.flip()
            
    def _handleKeyPress(self, event : pygame.event.Event):
        for k,v in key_movement.items():
            if k == '__props': continue
            if v['bind'] == event.key:
                key_movement['__props']['is_updated'] = True
                if v['type'] == 'command':
                    key_movement['__props']['cmdq'].append(k)
                else:
                    v['value'] = 1
                break

    def _handleKeyRelease(self, event : pygame.event.Event):
        for k,v in key_movement.items():
            if k == '__props': continue
            if v['bind'] == event.key:
                key_movement['__props']['is_updated'] = True
                if v['type'] != 'command':
                    v['value'] = 0
                break

    def _handleControl(self):
        #Drone commands (from input device)
        if key_movement['__props']['is_updated']:
            #droneAction.data_timer = droneAction.data_timeout
            #updateMotionVecFromBind(key_movement)
            key_movement['__props']['is_updated'] = False
            key_movement['__props']['manual_override'] = True

        #Actions
        key_commands : list = key_movement['__props']['cmdq']
        #if len(key_commands):
            #performDroneActionFromBind(key_commands.pop(0), drone)

        if key_movement['__props']['manual_override']:
            #Send control data if local movement
            #droneAction.action_set = key_movement['__props']['vec']
            #Disable manual control once all controls are released
            if all([abs(x['value'] < key_movement['__props']['threshold']) for k,x in key_movement.items() if k != '__props' and 'value' in x]):
                key_movement['__props']['manual_override'] = False
        #else:
        #    #Stop remote movement if timeout occurs
        #    if droneAction.data_timer > 0:
        #        droneAction.data_timer -= 1
        #    else:
        #        droneAction.action_set = [0,0,0,0]
