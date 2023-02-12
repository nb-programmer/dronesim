
#Simulated drone and application
from dronesim import SimulatorApplication, make_uav

#Sensors
from dronesim.sensor.panda3d.camera import Panda3DCameraSensor

import argparse

def main():
    parser = argparse.ArgumentParser()
    #TODO: Having some options would be nice
    parser.parse_args()

    #Add a single Quad UAV drone
    sim, controller, drone = make_uav()

    #Application window with the drone entity added
    simulator_window = SimulatorApplication(drone)

    # ** Configure the simulator by adding sensors **

    #Add a camera sensor facing down
    #NOTE: having texture of a power of 2 helps in memory optimization
    down_cam = Panda3DCameraSensor("downCameraRGB", size=(512,512))
    sim.add_sensor(down_camera_rgb = down_cam)
    #Insert camera into main app window and attach to the scene
    down_cam.attach_to_env(simulator_window.render, simulator_window.graphicsEngine, simulator_window.win)
    #Move and rotate camera with the UAV object
    down_cam.reparentTo(drone)
    #Face down
    down_cam.setHpr(0, -90, 0)

    #Start the app
    simulator_window.run()

if __name__ == "__main__":
    main()
