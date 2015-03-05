
.. _DaoInterfaces:

Data Access object (DAO)
------------------------

The Data Access Object (DAO) is a generic interface to an encapsulated database.
The databse holds all design information, from the initial vertices and edges
of the user's design specification, through to the placement and routing data.

It is a passive object, responding to queries from other modules.

=================== =========================================
    Field                Value
=================== =========================================
 Class                 dao
 PACMAN103 file        core/dao.py
 Function              Many
 Called by             control
 Input data            Read/write requests to database
 Calls                 None
 Output data           Read data from database
=================== =========================================


