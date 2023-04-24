
from panda3d.core import (
    NodePath,
    PandaNode,
    Light,
    AmbientLight,
    Filename,
    LVecBase3f
)

from direct.showbase.Loader import Loader

from os import PathLike
from dronesim.types import PandaFilePath
from typing import Optional, Union, List


class Panda3DEnvironment(NodePath):
    # Default scene to load (from virtual assets directory that is mounted. Can be anywhere, really)
    DEFAULT_SCENE = Filename("scenes/simple_loop.glb")
    DEFAULT_LOADER = Loader(None)

    def __init__(self,
                 name: str,
                 scene_model: Optional[Union[PandaFilePath,
                                             NodePath]] = DEFAULT_SCENE,
                 attach_lights: List[Union[Light, NodePath]] = [],
                 enable_dull_ambient_light: bool = True,
                 loader: Loader = DEFAULT_LOADER):
        super().__init__(name)

        self._attach_lights = attach_lights
        self._loader = loader

        # Add ambient lighting (minimum scene light)
        if enable_dull_ambient_light:
            ambient = AmbientLight('ambient_dull_light')
            ambient.set_color((.1, .1, .1, 1))
            self._attach_lights.append(ambient)

        self._setup_scene_lighting()

        # Load the given scene, if any
        if scene_model is not None:
            self.load_attach_scene(scene_model)

    def load_attach_scene(self,
                          scene_path: Union[PandaFilePath, NodePath, PandaNode],
                          position: LVecBase3f = None,
                          rotation: LVecBase3f = None,
                          scale: LVecBase3f = None) -> NodePath:
        '''Attach a scene into this environment. The scene can be a NodePath, PandaNode
        or a File path to the model (physical or virtual file)'''
        if isinstance(scene_path, (str, PathLike, Filename)):
            # Load scene from given path
            scene_model = self._loader.load_model(scene_path)
        elif isinstance(scene_path, NodePath):
            scene_model = scene_path
        elif isinstance(scene_path, PandaNode):
            scene_model = NodePath(scene_path)
        else:
            raise TypeError("Argument `scene_path` is not a valid type.")

        self.attach_scene(scene_model)

        # Optional transformation
        if position:
            scene_model.set_pos(position)
        if rotation:
            scene_model.set_hpr(rotation)
        if scale:
            scene_model.set_scale(scale)

        return scene_model

    def attach_scene(self, scene_model: NodePath):
        '''Attach the NodePath (model) instance to the environment'''
        scene_model.instance_to(self)

    def _setup_scene_lighting(self):
        '''
        Move all declared lights into the environment
        '''
        for light_node in self._attach_lights:
            if isinstance(light_node, Light):
                self.attach_new_node(light_node)
            elif isinstance(light_node, NodePath):
                light_node.reparent_to(self)
            else:
                raise TypeError(
                    "Received a light that has incorrect type (must be a subclass of p3d.Light).")
