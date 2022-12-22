# Drone Simulator

This package includes modules and tools to simulate an aerial vehicle similar to a quadcopter, and
makes it easy to use it for various A.I. applications such as path following, obstacle avoidance, etc.

It comes with a bunch of sensors that can be attached to the UAV, such as a Camera (RGB and Depth), IMU (motion), and more to come.
The simulator can have an "objective" set to generate observations for machine learning applications.

## Installation

Install the package using pip from :

```bash
pip install git+https://github.com/nb-programmer/dronesim.git
```

## Usage

Run the default simulator which launches a window with keyboard controls and a scene with an elliptical path to traverse.

To run the simulator, call the package name in the terminal:

```bash
$ dronesim
```

Or alternatively, execute the package using the Python interpreter:

```bash
$ python -m dronesim
```

Refer to the `examples/` folder for running the simulator with custom controllers

## Controls

### Simulator controls

Use the keyboard and mouse to interact with the simulator app.

The default mouse control is set to `Free mode` with mouse for looking.

Key|Action
---|---
Esc|Unlock/Lock and Show/Hide mouse
F3|Show debug data
F5|Change camera mode from one of three [Free, First Person and Third Person]
F6|Toggle control between camera and UAV
F11|Toggle fullscreen

### Default drone controls

Use the keyboard to control the drone or camera, with the following binds:

Key|Action
---|---
I|Take off
K|Land
W|Move forwards
S|Move backwards
A|Move left
D|Move right
Up arrow|Increase altitude
Down arrow|Decrease altitude
Left arrow|Heading counter-clockwise
Right arrow|Heading clockwise

# TODO

Pretty long at the moment

- [ ] Complete movement swap (camera to player)
  - [ ] Implement UAV movement by user
- [ ] Support for Ardupilot SITL interface
  - [ ] Using Mavlink
  - [ ] Using integrated SITL as optional dependency
  - [ ] Using dronekit
- [ ] Implement objectives
- [ ] Implement sensor interface
- [ ] Physics engine using Panda3D's bullet physics engine
- [ ] Implement IMU and other sensors
- [ ] Show crosshair
