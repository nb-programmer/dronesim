import json

class SimRPC(dict):
    def __init__(self, *args, **kwargs):
        self['_version_'] = 1.0
        self['command'] = None
        self['param'] = None
        super().__init__(*args, **kwargs)
    @property
    def command(self):
        return self['command']
    @property
    def param(self):
        return self['param']
    def serialize(self):
        #TODO: Packet split if overflow
        return json.dumps(self).encode()
    @classmethod
    def deserialize(cls, data : bytes):
        return cls(json.loads(data))
