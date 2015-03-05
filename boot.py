from pacman103.core.spinnman.scp.scp_connection import SCPConnection
from pacman103.core.spinnman.scp.boot import boot
from pacman103.conf import config

import sys
import getopt
import os

def _printargs():
    print sys.argv[0], " ", "[-h <hostname>] [-c <configfile>] [-b <bootfile>] [-s <structfile>]"
    print "    -h <hostname> - Optional.  The hostname or IP of the board to boot"
    print "    -c <configfile> - Optional.  The name of the config file e.g. spin5.conf"
    print "    -b <bootfile> - Optional.  The scamp file to boot with"
    print "    -s <structfile> - Optional.  The sark.struct file to boot with"
    sys.exit(2)
    
def _checkfile(test_file):
    real_file = test_file
    if not os.path.isfile(real_file):
        real_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 
                "spinnaker_tools", "boot", real_file)
    if not os.path.isfile(real_file):
        print "File %s not found" % test_file
        sys.exit(3)
    return real_file

opts = None
args = None
try:
    opts, args = getopt.getopt(sys.argv[1:], "?h:b:c:s:", \
        ["hostname=", "bootfile=", "configfile=", "structfile="])
except getopt.GetoptError:
    _printargs()
hostname = None
bootfile = None
configfile = None
structfile = None
for opt, arg in opts:
    if opt == "-?":
        _printargs()
    elif opt in ("-h", "--hostname"):
        hostname = arg
    elif opt in ("-b", "--bootfile"):
        bootfile = _checkfile(arg)
    elif opt in ("-c", "--configfile"):
        configfile = _checkfile(arg)
    elif opt in ("-s", "--structfile"):
        structfile = _checkfile(arg)

for arg in args:
    if hostname is None:
        print "Using %s as hostname" % arg
        hostname = arg
    elif configfile is None:
        print "Using %s as configfile" % arg
        configfile = _checkfile(arg)
    elif bootfile is None:
        print "Using %s as bootfile" % arg
        bootfile = _checkfile(arg)
    elif structfile is None:
        print "Using %s as structfile" % arg
        structfile = _checkfile(arg)

if hostname is None:
    hostname = config.get("Machine", "machineName")
    if hostname == "None":
        print "machineName is not defined in pacman.cfg and has not been specified"
        sys.exit(2)

if configfile is None:
    version = config.get("Machine", "version")
    if version == "None":
        print "version is not defined in pacman.cfg and config file has not been specified"
        sys.exit(2)
    configfile = _checkfile("spin{}.conf".format(version))

if bootfile is None:
    bootfile = _checkfile("scamp-130.boot")

if structfile is None:
    structfile = _checkfile("sark-130.struct")
    
try:
    conn = SCPConnection(hostname)
    version = conn.version(retries=3)
    print "{} already booted with {} {}".format(hostname, version.desc,
             version.ver_num)
except:
    boot(hostname, bootfile, configfile, structfile)
    try:
        conn = SCPConnection(hostname)
        version = conn.version()
        print "{} booted with {} {}".format(hostname, version.desc, 
                version.ver_num)
    except:
        print "Boot failed!"
