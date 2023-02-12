
from dronesim import DroneSimulator, DroneAction, DroneState
from dronesim.types import StateType
from dronesim.physics import Vec4PID
from simple_pid import PID

import matplotlib.pyplot as plt

STRAFE_CONTROL_PARAM = {'Kp': 0.02, 'Ki': 0.0, 'Kd': 0.0}
LIFT_CONTROL_PARAM = {'Kp': 0.03, 'Ki': 0.0, 'Kd': 0.0}
TURN_CONTROL_PARAM = {'Kp': 0.2, 'Ki': 0.0, 'Kd': 0.0}

if __name__ == "__main__":
    set_point = []
    height_list = []
    def update_state_history(state : StateType):
        physics_state = state[3]['state']
        set_point.append(physics_state['control'].z.setpoint)
        height_list.append(physics_state['pos'].z)

    simulator = DroneSimulator()
    default_state = simulator.state
    default_state.update({
        'control': Vec4PID(
            x=PID(sample_time=None, **STRAFE_CONTROL_PARAM),
            y=PID(sample_time=None, **STRAFE_CONTROL_PARAM),
            z=PID(sample_time=None, **LIFT_CONTROL_PARAM),
            w=PID(sample_time=None, **TURN_CONTROL_PARAM)
        )
    })
    update_state_history(simulator.reset(default_state))
    update_state_history(simulator.step(DroneAction.TAKEOFF))
    for _ in range(1000):
        update_state_history(simulator.step())
        if simulator.state['operation'] != DroneState.TAKING_OFF:
            break

    plt.clf()
    plt.plot(set_point)
    plt.plot(height_list)
    plt.legend(["Z-setpoint", "Z-position"])
    plt.show()
