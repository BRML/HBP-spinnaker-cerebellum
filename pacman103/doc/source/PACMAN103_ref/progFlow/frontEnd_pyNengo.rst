PyNengo Front End
#################

The PyNengo front end provides a means of running an existing PyNengo
(http://github.com/ctn-waterloo/nengo) model on SpiNNaker.  For simple models
only minimal changes are required. More complex models will require some more
significant changes to reflect the fact that SpiNNaker is an embedded device.

Getting Started
===============

Three steps are required in converting an existing Nengo model into a model
capable of being run on SpiNNaker.  Consideration of these steps is still of
use when creating an entirely new model for a SpiNNaker simulation.

1. First, the SpiNNaker front end for PyNengo must be imported *alongside*
   PyNengo itself::

       import nengo
       from pacman103.front import pynengo as spinn

2. Secondly, it is necessary to change some components (in particular:
   nodes) to their SpiNNaker equivalents.  Some of these components are
   accessible through :mod:`~pacman103.front.pynengo.helpers` which match the
   PyNengo API as closely as possible.  In other cases it may be necessary to
   add completely new objects from :mod:`~pacman103.front.pynengo.objects`.
   A table of necessary changes and modifications, along with some indication
   as to why, is provided below.

3. Thirdly, you must construct a
   :class:`SpiNNaker simulator<pacman103.front.pynengo.simulator.Simulator>`
   from your model, and use this to run the simulation::

       sim = model.simulator( sim_class = spinn.simulator.Simulator, args )
       sim.run( ... )

   Where ``args`` are arguments required by the SpiNNaker simulator.

Understanding the build and run process
=======================================

The PyNengo library builds an abstract representation of the Nengo model you
wish to simulate.  When ``model.simulate`` is called a new simulator is
instantiated, typically this instantiation process involves a build step in
which the abstract Nengo representation is translated into a representation
understood by the specific simulator. In the case of the SpiNNaker simulator,
the :class:`~pacman103.front.pynengo.builder.Builder` is used to perform this
transformation.  A blank PACMAN representation for the model is created then:

1. Each Ensemble and Node is added to the PACMAN representation as a vertex.
2. Each Probe is added to the PACMAN representation as a vertex.
3. Each Connection is added to the PACMAN representation as an edge.

Once this process is completed the simulator is returned a reference to the
PACMAN controller.  When ``run`` is called on the simulator PACMAN is called
to place and configure the SpiNNaker machine, load the data onto the machine
and commence the simulation. (In the case that place and configure or load
have already been performed we don't bother to do these again.)

Configuring the SpiNNaker machine entails generating the data files to be used
by the executables run on SpiNNaker.  It is at this point that neuron tuning
curves and Encoder and Decoder weight settings are determined - thus the
first :func:`~pacman103.front.pynengo.simulator.Simulator.run` or 
:func:`~pacman103.front.pynengo.simulator.Simulator.step` of the simulator can
seem to be unnecessarily slow!

Converting models to SpiNNaker compatible models
================================================

The PyNengo API provides the :class:`~nengo.objects.Node` class and
:func:`~nengo.model.Model.make_node` functions as a way of inserting
non-neural/environmental data into the model environment.  In the reference
implementation nodes may contain completely arbitrary functions written in
Python, this, however, is more general than can be accommodated in SpiNNaker
-- an embedded platform.

As a result we cannot provide the full generality of the reference
implementation, though for the following use cases we have provided a means of
achieving the same effect (that of inserting some time or environment
dependent data into a simulation).

Supported use cases
-------------------

.. todo::
   Finalise and implement the following.

1. Constant values
2. Functions of time
    i. Piecewise linear functions
    ii. Sine and cosine
    iii. Arbitrary functions for a specified period of time
3. Insertion of sensor data
4. User input from the host computer

.. warning::
   Various network and operating system latencies can result in
   unreliability (noise) when transmitting data from the host computer into
   a running SpiNNaker simulation.  For any serious experiments it is 
   recommended to provide input stimuli using either a pregenerated arbitrary
   function or a sensor system.
