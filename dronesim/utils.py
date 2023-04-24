
import numpy as np


asarray = np.array
rad2deg = np.rad2deg
deg2rad = np.deg2rad
clamp = np.clip
modulo = np.mod
sin, cos = np.sin, np.cos


def square_aspect2d_frame(size: float = 1.0):
    '''
    Returns a box spanning the given size in aspect2d space in Panda3d.
    
    Order of edges is (left, right, bottom, top), where any value of 0 is middle of the screen
    '''
    return (-size,size,-size,size)

class IterEnumMixin:
    '''Helps to get next item in the enum using next()'''

    def __next__(self):
        nxt_idx = (self._member_names_.index(
            self.name) + 1) % len(self._member_names_)
        return getattr(self, self._member_names_[nxt_idx])
