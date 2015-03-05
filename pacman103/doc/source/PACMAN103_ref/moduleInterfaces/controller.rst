
.. _ControllerInterfaces:

Controller
----------

The controller contains a set of functions that are called by the run() method
of the pyNN.spiNNaker module to set-up, compile and then simulate the user's 
specification.

=================== =========================================
    Field                Value
=================== =========================================
 Class                 control
 PACMAN103 file        core/control.py
 Functions             
 Called by             pynn.spiNNaker.run()
 Input data            Stored in dao (which it creates during _init_)
 Contains functions    add_vertex(), add_edge(), map_model(),
                       generate_output(), load_targets(),
                       run()
 Output data           Stored into Data Access Object (DAO)
=================== =========================================


