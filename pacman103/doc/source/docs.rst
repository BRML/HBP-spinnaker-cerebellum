About this documentation
------------------------
This documentation is created using `Sphinx <http://sphinx-doc.org/>`_, which
draws upon the documentation strings in the PACMAN source code to automatically
generate what you see here, with the exception of this message. The formatting
of this documentation (headers, code highlighting, emphasised text, etc) is
all drawn from simple markup in the strings; you may click the ``show source``
link in the sidebar of any page to see the markup text from which the page was
drawn. When browsing the code documentation, you may also click the
``show source`` button opposite any class or function to see the Python source
code that makes up that entity.

Should you edit the PACMAN source code and, consequently, the documentation
strings, you must rebuild the documentation. To do so, you simply run
``make clean; make html`` in the :file:`doc` directory of the PACMAN package;
this will create output in the :file:`doc/build/html` directory.

Sphinx is guided by a series of :file:`*.rst` files that describe the packages,
modules, classes and functions that should be scanned for documentation strings.
If you add or move packages or modules, you will have to update the
:file:`*.rst` files to inform Sphinx of the changes. For example
:file:`doc/source/pacman103.core.rst` describes the contents of the
:mod:`pacman103.core` package::

    core Package
    ============

    :mod:`core` Package
    -------------------

    .. automodule:: pacman103.core
        :members:
        :undoc-members:
        :show-inheritance:

    :mod:`control` Module
    ---------------------

    .. automodule:: pacman103.core.control
        :members:
        :undoc-members:
        :show-inheritance:

If you change the name of the :mod:`pacman103.core.control` module to
:mod:`pacman103.core.controller` and add a module :mod:`pacman103.core.cthulhu`,
you must edit :file:`doc/source/pacman103.core.rst` to look like::

    core Package
    ============

    :mod:`core` Package
    -------------------

    .. automodule:: pacman103.core
        :members:
        :undoc-members:
        :show-inheritance:

    :mod:`cthulhu` Module
    ---------------------

    .. automodule:: pacman103.core.control
        :members:
        :undoc-members:
        :show-inheritance:

    :mod:`controller` Module
    ---------------------

    .. automodule:: pacman103.core.control
        :members:
        :undoc-members:
        :show-inheritance:

Sphinx is described in more detail in `its own
documentation <http://sphinx-doc.org/contents.html>`_.
