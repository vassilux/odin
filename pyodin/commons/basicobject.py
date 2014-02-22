import os
import sys
import re
import time

try:
    import json
except ImportError:
    import simplejson as json

##
## 
##
class BasicObject(object):
    def __init__(self, objecttype = "BasicObject"):
        self.objecttype = objecttype
    def __setattr__(self, key, value):
        self.__dict__[key] = value
    def __getattr__(self, key):
        return self.__dict__.get(key)
    def __delattr__(self, key):
        del self.__dict__[key]
    def __str__(self):
        out = [
            "",
            "##################################################",
            "# BasicObject Type: %s" % self.objecttype,
            "##################################################"
        ]
        keys = sorted(self.__dict__.keys())
        pad  = sorted([len(k) for k in keys])[-1]
        
        for key in keys:
            format = "%%%ds : %s" % (pad, '%s')
            value  = self.__dict__.get(key)
            out.append(format % (key, value))
        
        out.append("##################################################")
        
        return "\n".join(out)

class BasicObjectEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, BasicObject):
            return super(BasicObjectEncoder, self).default(obj)

        return obj.__dict__

#if __name__ == '__main__':
#	pass