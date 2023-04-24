
from direct.showbase.Loader import Loader
from panda3d.core import FileStream, VirtualFileSystem
from dronesim.types import PandaFilePath

import json
from typing import Optional


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


class JSONLoader(AnyFileReaderMixin):
    @classmethod
    def load(cls, loader: Loader, assets_file: PandaFilePath, vfs: Optional[VirtualFileSystem] = None):
        # try:
        data = cls.read_file(assets_file, vfs)
        assets_config: dict = json.loads(data)

        mounts: dict = assets_config.get('mounts', {})
        asset_load: dict = assets_config.get('load', {})

        # TODO

        # print("mounts:", mounts)
        # print("load:", asset_load)

        # except OSError:
        #     pass
