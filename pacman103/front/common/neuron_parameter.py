'''
Created on 1 Apr 2014

@author: zzalsar4
'''
import numpy

class NeuronParameter(object):
    
    def __init__(self, value, datatype, scale):
        self._value = value
        self._datatype = datatype
        self._scale = numpy.array([scale])
        
    def get_value(self):
        return self._value
    
    def get_datatype(self):
        return self._datatype
    
    def get_scale(self):
        return self._scale
