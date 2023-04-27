
from direct.showbase.Loader import Loader
from panda3d.core import (
    VirtualFileSystem,
    Filename,
    Shader
)
from dronesim.types import PandaFilePath

import json
from typing import Optional, Callable, Dict, Any


class VFSFileReaderMixin:
    @staticmethod
    def read_file_vfs(vfs: VirtualFileSystem, file_path: PandaFilePath) -> bytes:
        return vfs.readFile(file_path, False)


class AnyFileReaderMixin(VFSFileReaderMixin):
    @classmethod
    def read_file(cls, file_path: PandaFilePath, vfs: Optional[VirtualFileSystem] = None) -> bytes:
        if vfs is None:
            # Use the default global VFS object if not passed
            vfs = VirtualFileSystem.get_global_ptr()
        try:
            return cls.read_file_vfs(vfs, file_path)
        except OSError:
            with open(file_path, 'rb') as f:
                return f.read()


def read_json_file(assets_file: PandaFilePath, vfs: Optional[VirtualFileSystem] = None):
    asset_conf = AnyFileReaderMixin.read_file(assets_file, vfs)
    return json.loads(asset_conf)


def loader_load_shader(cfg: dict, loader: Loader):
    shader_program_language = Shader.SL_GLSL
    vertex_path: Filename = Filename(cfg.get('vertex_path', ''))
    fragment_path: Filename = Filename(cfg.get('fragment_path', ''))
    geometry_path: Filename = Filename(cfg.get('geometry_path', ''))

    shader_program = Shader.load(
        shader_program_language,
        vertex=vertex_path,
        fragment=fragment_path,
        geometry=geometry_path
    )

    return shader_program


ASSET_LOADERS: Dict[str, Callable[[dict, Loader], Any]] = {
    'shader': loader_load_shader
}


class AssetHolder(dict):
    def __init__(selfs):
        super().__init__()

    def load_from_config(self, assets_file: PandaFilePath, loader: Loader, vfs: Optional[VirtualFileSystem] = None):
        self.load(read_json_file(assets_file, vfs), loader, vfs)

    def load(self, assets_config: dict, loader: Loader, vfs: Optional[VirtualFileSystem] = None):
        mounts: dict = assets_config.get('mounts', {})
        config_data: dict = assets_config.get('data', {})
        asset_load: dict = assets_config.get('load', {})

        for asset_type, asset_items in asset_load.items():
            load_method = ASSET_LOADERS.get(asset_type)
            if load_method:
                for asset_name, asset_config in asset_items.items():
                    is_enabled: bool = asset_config.pop('enabled', True)
                    if is_enabled:
                        asset = load_method(asset_config, loader)
                        self[asset_name] = asset


GLOBAL_ASSET_HOLDER = AssetHolder()
