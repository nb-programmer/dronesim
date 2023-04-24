
from dronesim import DroneSimulator, DroneAction, DroneState
from dronesim.types import StateType

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import copy


class SimPlotGenerator:
    def __init__(self):
        self.simulator = DroneSimulator()
        self.default_state = self.simulator.state

    def get_init_state(self):
        return copy.copy(self.default_state)

    @staticmethod
    def update_state_history(plots : dict, state : StateType):
        physics_state = state[3]['state']

        for plt_name, plot_list in plots.items():
            if plt_name == 'uav_altitude_set_point':
                plot_list.append(physics_state['control'].z.setpoint)
            elif plt_name == 'uav_altitude':
                plot_list.append(physics_state['pos'].z)

    def generate_plot(self, state : StateType = None, takeoff_params : dict = {}, step_dt : float = None, max_iterations : int = 1000, stop_after_takeoff : bool = True):
        _plots = {'uav_altitude_set_point': [], 'uav_altitude': []}
        self.update_state_history(_plots, self.simulator.reset(state))
        self.update_state_history(_plots, self.simulator.step({'action': DroneAction.TAKEOFF, 'params': takeoff_params}, dt=step_dt))
        for _ in range(max_iterations):
            self.update_state_history(_plots, self.simulator.step(dt=step_dt))
            if stop_after_takeoff and self.simulator.state['operation'] != DroneState.TAKING_OFF:
                break
        else:
            if stop_after_takeoff and self.simulator.state['operation'] == DroneState.TAKING_OFF:
                print("Warning: Takeoff didn't complete after %d iterations. PID parameters may not be correct." % max_iterations)

        return _plots

if __name__ == "__main__":
    gen = SimPlotGenerator()
    init_state = gen.get_init_state()

    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.25, bottom=0.25)

    ax.set_title("Takeoff height plot")
    ax.set_xlabel('Time (steps)')
    ax.set_ylabel('Altitude')

    ax_kp = fig.add_axes([0.25, 0.15, 0.65, 0.03])
    ax_ki = fig.add_axes([0.25, 0.1, 0.65, 0.03])
    ax_kd = fig.add_axes([0.25, 0.05, 0.65, 0.03])
    ax_sp = fig.add_axes([0.05, 0.25, 0.0225, 0.63])
    ax_dt = fig.add_axes([0.15, 0.25, 0.0225, 0.63])

    slider_kp = Slider(ax_kp, "Kp", 0, 0.5, init_state['control'].z.Kp, track_color='darkred')
    slider_ki = Slider(ax_ki, "Ki", 0, 0.5, init_state['control'].z.Ki, track_color='darkgreen')
    slider_kd = Slider(ax_kd, "Kd", 0, 0.5, init_state['control'].z.Kd, track_color='darkblue')
    slider_sp = Slider(
        ax_sp, "Takeoff\naltitude", 1, 30, 10,
        orientation="vertical", track_color='cyan'
    )
    slider_dt = Slider(
        ax_dt, "Step\ndelta\ntime", 0.001, 0.1, 0.01,
        orientation="vertical", track_color='yellow'
    )

    _plot_lines = {}
    def _draw_plot(val = None):
        new_state = copy.deepcopy(init_state)
        new_state['control'].z.Kp = slider_kp.val
        new_state['control'].z.Ki = slider_ki.val
        new_state['control'].z.Kd = slider_kd.val
        plots = gen.generate_plot(
            new_state,
            {'altitude': slider_sp.val},
            max_iterations=800,
            step_dt=slider_dt.val
        )
        for plot_name, plot_data in plots.items():
            if plot_name not in _plot_lines:
                _plot_lines[plot_name] = ax.plot(plot_data, label=plot_name)[0]
            else:
                _plot_lines[plot_name].set_xdata(range(len(plot_data)))
                _plot_lines[plot_name].set_ydata(plot_data)

        fig.canvas.draw_idle()

    slider_kp.on_changed(_draw_plot)
    slider_ki.on_changed(_draw_plot)
    slider_kd.on_changed(_draw_plot)
    slider_sp.on_changed(_draw_plot)
    slider_dt.on_changed(_draw_plot)

    _draw_plot()
    ax.legend()
    plt.show()
