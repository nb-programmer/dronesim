
import dataclasses
import numpy as np

rad2deg = np.rad2deg
deg2rad = np.deg2rad

class IterEnumMixin:
    '''Helps to get next item in the enum using next()'''
    def __next__(self):
        nxt_idx = (self._member_names_.index(self.name) + 1) % len(self._member_names_)
        return getattr(self, self._member_names_[nxt_idx])
    
class HUDMixin:
    '''HUD field to nested dictionary with visibility flag for a dataclass'''
    def hud(self):
        return {k.name:getattr(self, k.name) for k in dataclasses.fields(self) if self.__shouldshow__(k.name)}
    
    def __shouldshow__(self, field : str): return True
