__author__ = 'stokesa6'

class AbstractPartitioner:
    
    def __init__(self, dao):
        raise NotImplementedError

    def partition(self):
        raise NotImplementedError
