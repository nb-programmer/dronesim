
# TODO list

Pretty long at the moment. It is in no particular order

- [ ] Completely implement other high-level functions in DefaultDroneControl
- [ ] [PEP 8](https://peps.python.org/pep-0008/) compliant function names
  - [ ] Also use snake_case function calls of Panda3D instead of camelCase ones (see [this](https://discourse.panda3d.org/t/drop-camelcase-in-favor-of-snake-case-in-future-versions-of-panda3d/24436))
- [x] Complete movement swap (camera to player)
  - [x] Implement UAV movement by user
- [ ] Show skybox texture
- [ ] Simulator engine should use Armed state before takeoff
- [ ] Event emitter should actually emit events
- [ ] Landing is bugged, so needs a landing (and also takeoff) routine
- [ ] Support for Ardupilot SITL interface
  - [ ] Using Mavlink (which can support any UAV)
  - [ ] Using integrated SITL as optional dependency
  - [ ] Using dronekit
- [ ] Joystick support
- [ ] Add a menu interface
  - [ ] Options to rebind keys and joystick input
- [ ] Implement objectives
- [ ] Implement sensor interface
- [ ] Physics engine using Panda3D's bullet physics engine
- [ ] Implement IMU and other sensors
- [x] Show crosshair
  - [ ] Crosshair blend mode (invert) with what's on screen below it
- [ ] Allow sensor access to physics engine
- [ ] Bump mapping on scene to make depth more realistic
