
from dronesim import DroneSimulator
from dronesim.simapp import SimulatorApplication
from dronesim.interface import IDroneControllable
from dronesim.types import DroneAction, StepRC
from dronesim.sensor.panda3d.camera import Panda3DCameraSensor

import threading

import cv2

class AIDroneControlAgent(threading.Thread, IDroneControllable):
    def __init__(self):
        super().__init__(daemon=True)

        #Environment
        self.drone = DroneSimulator()
        self.model = None

        #Add some sensors
        self.drone.addSensor(
            down_camera_rgb = Panda3DCameraSensor("downCameraRGB", size=(320,320)),
            down_camera_depth = Panda3DCameraSensor("downCameraDepth", size=(160,160), camera_type=Panda3DCameraSensor.CAMERA_TYPE_DEPTH)
        )

        self.__state = None
        self.__debug_data = dict()

    def initEnv(self, app):
        self.drone.sensors['down_camera_rgb'].attachToEnv(app.render, app.graphicsEngine, app.win)
        self.drone.sensors['down_camera_depth'].attachToEnv(app.render, app.graphicsEngine, app.win)

        #Attach camera to the UAV, point downwards facing the floor
        self.drone.sensors['down_camera_rgb'].reparentTo(app.getUAVModelNode())
        self.drone.sensors['down_camera_rgb'].setHpr(0, -90, 0)
        self.drone.sensors['down_camera_depth'].reparentTo(app.getUAVModelNode())
        self.drone.sensors['down_camera_depth'].setHpr(0, -90, 0)

    def run(self):
        #Set to True to show an OpenCV window of the RGB camera
        show_camera = False

        #Tell simulator to takeoff
        self.drone.step({'action': DroneAction.TAKEOFF})

        #Skip some frames till takeoff completes (TODO: wait for state change instead)
        for _ in range(200):
            self.__state = self.drone.step()

        #Cycle for 2000 steps
        for _ in range(2000):
            self.__state = self.drone.step(StepRC(0,0.6,0,0))
            self.__update_debug_state(self.__state)

            if show_camera:
                ret, img = self.drone.sensors['down_camera_rgb'].renderAndGetFrameBuffer()
                #Show image only if we got one
                if ret:
                    cv2.imshow("Camera frame", img)

            cv2.waitKey(10)
            
        cv2.destroyAllWindows()

    def __update_debug_state(self, state):
        observation, reward, done, info = state
        self.__debug_data.update({
            'simulator': info['metrics'],
            'generation': 0,
            'iteration': 0,
            'training_epoch': 0,

            'reward': reward,
            'state': info['state'],
            'observation': observation,
            'sensors': len(self.drone.sensors)
        })

    def get_current_state(self):
        return self.__state

    def get_debug_data(self) -> dict:
        return self.__debug_data

def main():
    droneControl = AIDroneControlAgent()
    droneWindow = SimulatorApplication(droneControl)
    droneControl.initEnv(droneWindow)
    droneControl.start()
    droneWindow.run()

if __name__ == "__main__":
    main()
