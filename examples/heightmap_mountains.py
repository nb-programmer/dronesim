
from dronesim import SimulatorApplication, Panda3DEnvironment, make_uav

from common import mount_examples_assets_dir

from panda3d.core import (
    GeoMipTerrain,
    NodePath,
    DirectionalLight,
    LVecBase3f,
    Spotlight,
    TextureStage
)

from direct.showbase.Loader import Loader


def main():
    mount_examples_assets_dir()

    LOADER = Loader(None)

    tex_grass = LOADER.loadTexture('/examples/assets/grass_texture_hd_31.jpg')

    terrain = GeoMipTerrain("mySimpleTerrain")
    terrain.set_heightfield("/examples/assets/simple_heightmap.png")
    terrain.set_block_size(32)
    # terrain.setBruteforce(True)
    terrain.generate()

    terrain_holder = NodePath("terrain_holder")
    terrain_root = terrain.get_root()
    terrain_root.reparent_to(terrain_holder)

    # Center align the terrain
    terrain_bbox_p1, terrain_bbox_p2 = terrain_root.get_tight_bounds()
    terrain_mid = (terrain_bbox_p2 + terrain_bbox_p1)/2
    height_at_origin = terrain.get_elevation(*terrain_mid.xy)
    terrain_mid.z = height_at_origin
    print(terrain_bbox_p1, terrain_bbox_p2, terrain_mid, height_at_origin)
    terrain_holder.set_pos(-terrain_mid)
    terrain_holder.set_scale(10,10,100)

    terrain_root.set_texture(TextureStage.get_default(), tex_grass)
    terrain_root.set_tex_scale(TextureStage.get_default(), 500)
    terrain_root.set_shader_auto() # Don't use PBR shader for this model

    # Lighting
    dlight = DirectionalLight('dlight')
    dlight.set_color((1, 1, 1, 1))
    dlight.set_shadow_caster(True)
    dlnp = NodePath(dlight)
    dlnp.set_hpr(0, -60, 0)

    _, _, uav = make_uav()

    env = Panda3DEnvironment("basic_env", scene_model=terrain_holder, attach_lights=[dlnp])

    droneWindow = SimulatorApplication(env, uav)
    def print_elev(task):
        #print(terrain.getElevation(*uav.get_pos().xy) * terrain_root.get_scale().z)
        return task.cont
    droneWindow.task_mgr.add(print_elev)
    droneWindow.run()

if __name__ == "__main__":
    main()
