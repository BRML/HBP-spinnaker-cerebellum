try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    
import os
import shutil
import stat
    
def install_pacman_cfg():
    template_cfg = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                "pacman.cfg.template")
    home_cfg = os.path.expanduser("~/.pacman.cfg")
    if not os.path.isfile(home_cfg):
        shutil.copyfile(template_cfg, home_cfg)
        print "************************************"
        print "%s has been created - please edit this file and change \"None\""
        print "after \"machineName\" to the hostname or IP address of your"
        print "SpiNNaker board, and change \"None\" after \"version\" to the"
        print "version of SpiNNaker hardware you are running on:"
        print "[Machine]"
        print "machineName = None"
        print "version = None"
        print "************************************"
    else:
        print "Warning - not overwriting existing .pacman.cfg in home directory"
        
def update_permissions():
    spinnaker_tools = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                "spinnaker_tools")
    spinnaker_tools_tools = os.path.join(spinnaker_tools, "tools")
    file_list = os.listdir(spinnaker_tools_tools)
    
    for file_name in file_list:
        path = os.path.join(spinnaker_tools_tools, file_name)
        mode = os.lstat(path).st_mode
        os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    makes = [os.path.join(spinnaker_tools, "sark", "make_gnu"),
             os.path.join(spinnaker_tools, "sark", "make_arm"),
             os.path.join(spinnaker_tools, "spin1_api", "make_gnu"),
             os.path.join(spinnaker_tools, "spin1_api", "make_arm")]
    
    for path in makes:
        mode = os.lstat(path).st_mode
        os.chmod(path, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

"""
Correctly installs PACMAN103, but not its requirements -- need to investigate.
"""
setup(
    name = "SpiNNaker Package",
    version = "alpha103",
    description="Tools for the SpiNNaker platform.",
    url="https://solem.cs.man.ac.uk",
    packages=['pacman103'],
    requires = [
        'numpy',
        'scipy',
        'matplotlib',
#       'nengo',
        'pynn'
    ],
)

# Install the pacman.cfg in the user's home directory
install_pacman_cfg()

# Set permissions on extracted files
update_permissions()
