
.. _DataSpec:

Data Specification
------------------

Unlike the other data structures in this section, the *Data Spec* is not
a Python class. It is a binary file  and there is one such file generated 
for each core. This step occurs after routing is performed by the *Data 
Structure Generator*.

A Spec specifies the set of operations needed to reserve, construct and install
the required data structures for that core. See :ref:`dsg-overview`
for further details.

The process of reading and executing the list of instructions in the
*Data Spec* is carried out by the :ref:`spec-executor-overview`. This execution 
process can be handled in either of two ways:

* Host-based Executor: A Python module generates the data files for each
  core and they are subsequently loaded onto the machine via the Ethernet
  adaptor.

* Core-based Executor: A special 'C'-based application (the Spec Executor) is
  loaded to each core. Next, each core is sent it's own Spec. The Executor
  reads and executes the Spec, increasing parallelism and reducing data
  bandwidth requirements.

For further details of the Spec Executor, see :ref:`spec-executor-overview`

