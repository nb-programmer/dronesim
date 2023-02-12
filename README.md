# Drone Simulator

This package includes modules and tools to simulate an aerial vehicle similar to a quadcopter, and
makes it easy to use it for various A.I. applications such as path following, obstacle avoidance, etc.

It comes with a bunch of sensors that can be attached to the UAV, such as a Camera (RGB and Depth), IMU (motion), and more to come.
The simulator can have an "objective" set to generate observations for machine learning applications.

## Features
TODO

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

Refer to the `examples/` folder for running the simulator with custom controllers. You will need to clone this repo in order to access the examples.

## Controls

### Simulator controls

Use the keyboard and mouse to interact with the simulator app.

The default mouse control is set to `Free mode` with mouse for looking.

Key|Action
---|---
Esc|Unlock/Lock and Show/Hide mouse
F1|Toggle visibility of HUD
F3|Toggle visibility of debug view
Shift+F3|Connect to Panda3D's PStats tool for profiling
F5|Change camera mode from one of [Free, First Person or Third Person]
F6|Toggle your control between camera and UAV
F11|Toggle fullscreen
v|Show/hide all buffers
`\`|Dump current simulator state to console

### Default drone/camera controls

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
Mouse wheel|Free cam: change fly speed; Third Person cam: Change orbit radius
