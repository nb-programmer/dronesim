
#Simulated drone
from dronesim import make_uav

#Sensors
from dronesim.sensor.panda3d.camera import Panda3DCameraSensor

#App window
from dronesim.simapp import SimulatorApplication

import argparse

def main():
    parser = argparse.ArgumentParser()
    #TODO: Having some options would be nice
    parser.parse_args()

    #Add a single Quad UAV drone
    sim, controller, drone = make_uav()

    #Application window with the drone entity added
    droneWindow = SimulatorApplication(drone)

    # ** Configure the simulator by adding sensors **

    #Add a camera sensor facing down
    #NOTE: having texture of a power of 2 helps in memory optimization
    downCam = Panda3DCameraSensor("downCameraRGB", size=(512,512))
    sim.add_sensor(down_camera_rgb = downCam)
    #Insert camera into main app window and attach to the scene
    downCam.attach_to_env(droneWindow.render, droneWindow.graphicsEngine, droneWindow.win)
    #Move and rotate camera with the UAV object
    downCam.reparentTo(drone)
    #Face down
    downCam.setHpr(0, -90, 0)

    #Start the app
    droneWindow.run()

if __name__ == "__main__":
    main()
