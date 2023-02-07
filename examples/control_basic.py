
from dronesim import make_uav
from dronesim.interface import IDroneControllable
from dronesim.simapp import SimulatorApplication
from dronesim.types import DroneAction, StepRC

import threading

class SimpleMovementCommandGenerator(threading.Thread):
    def __init__(self, droneControl : IDroneControllable):
        super().__init__(daemon=True)
        self.drone = droneControl
        self.start()

    def run(self):
        #Tell simulator to takeoff
        print("Taking off...")
        self.drone.takeoff() #Will wait till takeoff completes
        print("Takeoff done")

def main():
    #Create simulator, attached to a 'DefaultDroneControl' interface, attached to a quad UAV model.
    #The simulator is started automatically and keep ticking
    droneSim, droneControl, uav = make_uav()

    #GUI to visualize (and control) the drone
    droneWindow = SimulatorApplication(uav)

    #Custom control class that can send movement commands to the drone
    SimpleMovementCommandGenerator(droneControl)

    #Start application
    droneWindow.run()

if __name__ == "__main__":
    main()
