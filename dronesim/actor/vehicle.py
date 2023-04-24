
from direct.actor.Actor import Actor
from dronesim.interface.control import IDroneControllable


class VehicleModel(Actor):
    '''A VehicleModel base class that has a controller (IDroneControllable).
    It reads state from the controller to make the model reflect the state,
    and it also has the ability to send commands to the IDroneControllable.'''
    @property
    def controller(self) -> IDroneControllable:
        raise NotImplementedError()
