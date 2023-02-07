
from direct.actor.Actor import Actor
from panda3d.core import NodePath

from dronesim.interface.control import IDroneControllable
from dronesim.utils import rad2deg
from dronesim.types import StateType

import os
import typing
import random

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
                 control_source : IDroneControllable,
                 shell_model : typing.Union[NodePath, os.PathLike] = None,
                 propellers : typing.Dict[str, typing.Union[NodePath, os.PathLike]] = None,
                 propeller_spin : typing.Dict[str, float] = None):
        self._control_source = control_source

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

    @property
    def controller(self) -> IDroneControllable:
        return self._control_source

    def update(self):
        state : StateType = self._control_source.get_current_state()
        if state is not None:
            state_info = state[3]
            transformState = state_info.get('state')
            if transformState is not None:
                self.setPos(*transformState['pos'])
                rotx, roty, rotz = transformState['angle']
                self.setHpr(rad2deg(rotz), rad2deg(roty), rad2deg(rotx)) #TODO: Need more transformations for pitch and roll based on velocity
                thrust = transformState['thrust_vec']
                prop_vel = thrust.z * 1e5

                for bone in self.joints['propellers'].values():
                    #Rotate with respect to spin direction and thrust
                    bone['bone'].setH(bone['bone'].getH() + prop_vel*bone['spinDir'])

        super().update()
