
from dronesim import make_uav
from dronesim.interface import IDroneControllable, DroneAction
from dronesim.simapp import SimulatorApplication
from dronesim.types import StepRC

import threading

class SimpleMovementCommandGenerator(threading.Thread):
    def __init__(self, drone_control : IDroneControllable):
        super().__init__(daemon=True)
        self.drone = drone_control
        self.start()

    def run(self):
        #Tell simulator to takeoff
        print("Taking off...")
        self.drone.takeoff() #Will wait till takeoff completes
        print("Takeoff done")

def main():
    #Create simulator, attached to a 'DefaultDroneControl' interface, attached to a quad UAV model.
    #The simulator is started automatically and is kept ticking
    drone_sim, drone_control, uav = make_uav()

    #GUI to visualize (and control) the drone
    drone_window = SimulatorApplication(uav)

    #Custom control class that can send movement commands to the drone
    SimpleMovementCommandGenerator(drone_control)

    #Start application
    drone_window.run()

if __name__ == "__main__":
    main()
