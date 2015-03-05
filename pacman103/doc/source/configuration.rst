Configuring PACMAN103
*********************

PACMAN103 is configured through the use of config files.  When looking for
configuration PACMAN searches through for files in order, with
entries from later files overriding entries from earlier ones.
The configuration files are:

* ``pacman.cfg`` in the directory where PACMAN has been installed.
* ``.pacman.cfg`` in your home directory (i.e. ``~/.pacman.cfg``).
* ``pacman.cfg`` in the current working directory.

.. warning::
  It is *strongly recommended* that you don't modify the root PACMAN
  configuration file but instead make personal configuration changes in
  ``~/.pacman.cfg`` and project configuration changes in ``./pacman.cfg``.

Example
-------

If the SpiNNaker board you use is called ``spinn-32`` then the following
minimal configuration file (placed at ``~/.pacman.cfg``) suffices to ensure
that all your projects run on this board::

    [Routing]
    machineName = spinn-32

.. hint::
   For your board to have a "name" you may need to add appropriate lines
   to your ``/etc/hosts`` file.

Configuration Options
---------------------

Information about all options can be found in the ``pacman.cfg`` in the
location where you installed PACMAN.
