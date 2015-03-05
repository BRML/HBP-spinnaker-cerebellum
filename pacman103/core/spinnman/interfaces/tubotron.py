'''
Created on 4 Feb 2014

@author: zzalsar4
'''

import socket
import struct
import threading
import thread
import time

import logging
logger = logging.getLogger(__name__)

def _timeout(tubotron, timeout):
    time.sleep(timeout)
    tubotron.stop()

class Tubotron(threading.Thread):
    def __init__(self, port, timeout=0.0):
        raise Exception(" currently not supported, use spinnakertools_tools_tubortron")
        '''
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)
        self.sock.bind(("0.0.0.0", port))
        self.bufsize = 65536
        self.done = False
        if timeout != 0.0 and timeout > 0.0:
            thread.start_new_thread(_timeout, (self, timeout))
        '''
            
    def set_timeout(self, timeout):
        print("Timeout set to %f" % timeout)
        if timeout > 0.0:
            thread.start_new_thread(_timeout, (self, timeout))
            
    def set_bufsize(self, bufsize):
        self.bufsize = bufsize;
    
    def stop(self):
        print("[tubotron] Stopping")
        self.done = True
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
    
    def run(self):
        logger.debug("[tubotron] Starting")
        while not self.done:
            try:
                print "trying to receive"
                data, addr = self.sock.recvfrom(self.bufsize)
                print "recieved"
                textlen = len(data) - 14
                (pad, flags, tag, dp, sp, da, sa, cmd, cf, text) =\
                    struct.unpack("<HBBBBHHHH%ds" % textlen, data)
                logger.debug(text[:-1])
            except socket.timeout:
                print "socket timed out"
            except Exception as e:
                if not self.done:
                    logger.debug("[tubotron] Error receiving data")
                else:
                    print e.message
        logger.debug("[tubotron] Exiting")

if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    tubotron = Tubotron(17892)
    tubotron.start()