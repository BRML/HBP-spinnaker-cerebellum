"""
Parameter management aids.  This has yet to be finalised or integrated into
the rest of PACMAN, but integration should be fairly seemless.  The idea is to
create proto-types which can be manipulated normally but have a way of being
cast into the appropriate form for storage.

Example:
   >>> x = S1615( 1. + 2**(-15) ) # x = 0x00008001
   >>> x += 2**-2                 #   = 0x0000A001
   >>> x.converted
   '\x00\x00\xA0\x01'
"""

import collections
import numbers
import struct

def _accepts_parameter_instance( f ):
    def f_( self, a ):
        if isinstance( a, ParameterInstance ):
            return f( self, a._v )
        return f( self, a )
    return f_

class ParameterInstance( object ):
    def __init__( self, value, conversion_func ):
        self._v = value
        self._cf = conversion_func

    @property
    def converted( self ):
        """This parameter converted for storage on SpiNNaker."""
        return self._cf( self._v )

    @_accepts_parameter_instance
    def __add__( self, a ):
        return ParameterInstance( self._v + a, self._cf )

    @_accepts_parameter_instance
    def __sub__( self, a ):
        return ParameterInstance( self._v - a, self._cf )

    @_accepts_parameter_instance
    def __mul__( self, a ):
        return ParameterInstance( self._v * a, self._cf )

    @_accepts_parameter_instance
    def __div__( self, a ):
        return ParameterInstance( self._v / a, self._cf )

    @_accepts_parameter_instance
    def __pow__( self, a ):
        return ParameterInstance( self._v ** a, self._cf )

    @_accepts_parameter_instance
    def __rpow__( self, a ):
        return ParameterInstance( a ** self._v, self._cf )

    # TODO:
    # __floordiv__
    # __truediv__
    # __mod__
    # __divmod__
    # __lshift__
    # __rshift__
    # __and__
    # __or__
    # __xor__
    # __rdiv__
    # Additional reflected operators

    # Reflected operators
    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__

    def __str__( self ):
        return str( self._v )

class ParameterType( object ):
    """A ParameterType acts to encapsulate the work required to convert
    values in Python code to values suitable for storage and manipulation
    on SpiNNaker.
    
    :param n_bytes: Number of bytes this will occupy in memory.
    :param conversion_func: Function which accepts an numerical value and
                            returns the appropriate bits for storage on
                            SpiNNaker.
    """

    def __init__( self, n_bytes, conversion_func ):
        self._n_bytes = n_bytes
        self._cf = conversion_func
    
    def __call__( self, obj ):
        """Convert an object of this type into a parameter which may
        be mathematically manipulated before being resolved into the
        appropriate format for the machine."""
        if isinstance( obj, collections.Iterable ):
            return [ ParameterInstance( v, self._cf ) for v in obj ]

        if not isinstance( obj, numbers.Real ):
            raise TypeError( "Cannot directly convert an object of type %d to"
                " bitstream." % type( obj ) )

        return ParameterInstance( obj, self._cf )

    @property
    def n_bytes( self ):
        return self._n_bytes

    @property
    def n_bits( self ):
        return self._n_bytes * 8

"""
Conversion function and some parameter types.

Thanks Jamie!
"""

length_str = {
    8: 'b',
    16: 'h',
    32: 'i',
    64: 'q',
}

def _num_to_fixed_point( n_bits, n_frac, signed, v ):
    """Convert arbitrary numerical type to S1615."""
    v = int( float( v ) * 2**n_frac ) # Shift as appropriate

    try:
        b = length_str[ n_bits ]
    except KeyError, e:
        raise ValueError( "Invalid number of bits %s." % e )

    packed = struct.pack(
        "<%s" % ( b if signed else b.upper() ),
        v
    )
    return struct.unpack( "<%s" % b, packed )[0]


S1615 = ParameterType( 4, lambda v : _num_to_fixed_point( 32, 15, True, v ) )
S87   = ParameterType( 4, lambda v : _num_to_fixed_point( 16,  7, True, v ) )

def s1615(v):
    if isinstance(v, collections.Iterable):
        return [p.converted for p in S1615(v)]
    return S1615(v).converted
