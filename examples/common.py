
from panda3d.core import (
    VirtualFileSystem,
    VirtualFileMountSystem,
    Filename
)

import os


ASSETS_VFS = VirtualFileSystem.getGlobalPtr()

def list_vfs_contents(dir : str = '/'):
    ASSETS_VFS.ls(dir)

def mount_examples_assets_dir(to_vfs_dir : str = "/examples/assets/"):
    '''Mounts the 'assets' dir present in this folder to the vfs'''
    ASSETS_VFS.mount(
        VirtualFileMountSystem(Filename.from_os_specific(
            os.path.normpath(os.path.join(os.path.dirname(__file__), 'assets/'))
        )),
        to_vfs_dir,
        VirtualFileSystem.MFReadOnly
    )
