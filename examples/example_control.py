from dronesim.control import SimulatedDroneControl
import time

if __name__ == "__main__":
    ds = SimulatedDroneControl()
    print("[Action] Take off")
    ds.takeoff()
    time.sleep(5)
    print("[Action] Move forward")
    t = time.time()
    while time.time() - t < 5:
        ds.send_rc_control(0,30,0,0)
        time.sleep(0.1)
    print("[Action] Turn")
    t = time.time()
    while time.time() - t < 5:
        ds.send_rc_control(0,0,0,30)
        time.sleep(0.1)
    print("[Action] Move forward")
    t = time.time()
    while time.time() - t < 5:
        ds.send_rc_control(0,30,0,0)
        time.sleep(0.1)
    print("[Action] Land")
    ds.land()
    