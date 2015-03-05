"""
THESE ARE STATIC DEFINITIONS
They form a dictionary including hostname, board type, plus X and Y maximum extent dimensions (default dimensions are 8x8 (per the spinn4-spinn5 board types)).
Type specifies the machine construction. If of an individual board: e.g. "spinn2", "spinn3", "spinn4" or "spinn5" series
For other machines you can use "unwrapped" for a static machine of arbitrary size which at its edges does not wrap around, and "wrapped" which does wrap at its edges.  
These static definitions assume all links are functional, and that there are 16 application cores per chip.
It is therefore recommented that "dynamic" is used for the type, which will explore the machine at the given host IP address and find its true core and link status (must be booted and numbered)
"""

machines = {'test0':  {'hostname':'test0',   'x':1, 'y':1, 'type':'wrapped'},
            'amu12':  {'hostname':'amu12',   'x':2, 'y':2, 'type':'spinn3' },
            'amu15':  {'hostname':'amu15',   'x':2, 'y':2, 'type':'spinn3' },
            'amu16':  {'hostname':'amu16',   'x':2, 'y':2, 'type':'spinn3' },
            'spinn-7':{'hostname':'spinn-7', 'x':8, 'y':8, 'type':'spinn4'}}
