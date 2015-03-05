
Data Specification Generator
----------------------------

The data structure generator is responsible for creating a list of
instructions, one set for each core in the target application, which
describe the required steps to build data structures on the SpiNNaker
nodes ready for simulation.

=================== =========================================
    Field                Value
=================== =========================================
 Module                dataSpecGenerator
 PACMAN103 file        core/dataSpecGenerator.py
 Function              generateDataSpecs()
 Called by             core/generate_output()
 Input data            dao, containing mapping and routing info for all cores
 Calls                 app.customDataGenerator()
 Output data           Writes Spec files(one per core) in binary
                       and (optionally) textual format.
=================== =========================================

The generic dataSpecGenerator module iterates over the chips in the
target machine, calling a custom python script (the customDataGenerator)
for each chip.

This custom function is defined by the application developer, but must
conform to certain format restrictions.

The output of this process is a set of Spec file, in a binarty format.
Optionally, a textual version of each file can also be produced, for debug
purposes.

<TODO: What is the run-time option required to produce these textual versions?>


