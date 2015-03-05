
.. _FrontEndPynnInterfaces:

pyNN Front End
--------------

The pyNN front-end  is called by the user's code and invokes PACMAN103 indirectly.
The folowing table provides an overview of the sources and sinks of information.

=================== =========================================
    Field                Value
=================== =========================================
 Module                pynn.spiNNaker
 PACMAN103 file        front/pynn/__init__.py
 Function              pynn.spiNNaker.run()
 Called by             User specification (python)
 Input data            User specification (python)
 Calls                 controller.map_module()
                       controller.generate_output()
                       controller.load_targets()
                       controller.run()
 Output data           Stored into Data Access Object (DAO)
=================== =========================================

