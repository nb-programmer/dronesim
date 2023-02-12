
from dronesim import SimulatorApplication, make_uav

from common import mount_examples_assets_dir

from panda3d.core import (
    GeoMipTerrain,
    NodePath,
    DirectionalLight,
    Spotlight
)

def main():
    mount_examples_assets_dir()
    _, _, uav = make_uav()

    terrain = GeoMipTerrain("mySimpleTerrain")
    terrain.setHeightfield("/examples/assets/simple_heightmap.png")
    terrain.setBruteforce(True)
    terrain.getRoot().setSz(100)
    terrain.generate()

    dlight = DirectionalLight('dlight')
    dlight.setColor((1, 1, 1, 1))
    dlight.setShadowCaster(True)
    dlnp = NodePath(dlight)
    dlnp.setHpr(0, -60, 0)

    droneWindow = SimulatorApplication(uav, scene_model=terrain.get_root(), attach_lights=[dlnp])
    droneWindow.run()

if __name__ == "__main__":
    main()
