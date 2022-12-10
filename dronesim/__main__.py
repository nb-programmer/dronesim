
#Simulated drone
from dronesim import DroneSimulator
from dronesim.interface import DefaultDroneControl

#App window
from dronesim.simapp import SimulatorApplication

import argparse

def main():
    parser = argparse.ArgumentParser()
    #TODO: Having some options would be nice
    parser.parse_args()

    #Simulator environment
    drone = DroneSimulator()
    droneControl = DefaultDroneControl(drone, update_enable=True)
    droneWindow = SimulatorApplication(droneControl)
    droneWindow.run()
    
if __name__ == "__main__":
    main()
