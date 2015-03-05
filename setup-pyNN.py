from distutils.core import setup

"""
Setup script for pyNN.spiNNaker.  This works using "python setup-pyNN.py install".
"""

setup(
    name = "pyNN",
    version = "-spiNNaker-103",
    description="Tools for the SpiNNaker platform.",
    url="https://solem.cs.man.ac.uk",
    package_dir={'':'pyNN-spiNNaker-src'},
    packages=['pyNN.spiNNaker'],
    zip_safe = False,
)
