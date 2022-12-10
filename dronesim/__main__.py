
import argparse

#Simulated drone
from dronesim import DroneSimulator
from dronesim.interface.default import DefaultDroneControl

#App window
from dronesim.simapp import SimulatorApplication

def main(args):
    #Simulator environment
    drone = DroneSimulator()
    droneControl = DefaultDroneControl(drone, update_enable=True)
    droneWindow = SimulatorApplication(droneControl)
    droneWindow.run()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    main(parser.parse_args())
