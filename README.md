# Drone Simulator

This package includes modules and tools to simulate an aerial vehicle similar to a quadcopter, and
makes it easy to use it for various A.I. applications such as path following, obstacle avoidance, etc.

## Installation

Install the package using pip from :

```bash
pip install git+https://github.com/nb-programmer/dronesim.git
```

## Usage

Run the default simulator which launches a window with keyboard controls, Video stream though UDP and a scene with an elliptical path to traverse.

To run the simulator, execute the package using the Python interpreter:

```bash
python -m dronesim
```

Use the keyboard to control the drone, with the following binds:

Key|Action
---|---
R|Reset simulator state
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
