import threading
import thread
import collections
import socket
import logging
logger = logging.getLogger(__name__)

def _timeout(visualiser, timeout):
    visualiser.stop()


class PortQueuer(threading.Thread):
    '''
    thread that holds a queue to try to stop the loss of packets from the socket
    '''

    def __init__(self):
        threading.Thread.__init__(self)
        self.queue = collections.deque()
        self.bufsize = 65536
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(1)
        self.done = False
        self.exited = False

    def set_timeout(self, timeout):
        '''
        set time before engaging thread
        '''
        print("Timeout set to %f" % timeout)
        if timeout > 0:
            thread.start_new_thread(_timeout, (self, timeout))

    def set_bufsize(self, bufsize):
        '''
        sets the buf size (whats this for again? ABS)
        '''
        self.bufsize = bufsize;

    def set_port(self, port):
        '''
        sets the port to whcih we are listening
        '''
        try:
            self.sock.bind(("0.0.0.0", port))
        except socket.error as e:
            if e.errno == 98:
                logger.error("socket already in use, "
                            "please close all other spinn_views")
            else:
                logger.error(e.message)
        print

    def stop(self):
        '''
        method to kill the thread
        '''
        logger.info("[queuer] Stopping")
        self.done = True
        while not self.exited:
            pass
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            logger.warn("tries to close a non-connected socket, ignoring and continuing")
            return 0
        self.sock.close()


    def run(self):
        '''
        runs by just putting packets into a non-blocking queue for the port listener to read from
        '''
        logger.info("[port_queuer] starting")
        while not self.done:
            try:
                data, addr = self.sock.recvfrom(self.bufsize)
                self.queue.append(data)
            except socket.timeout:
                pass
        self.queue.append(None)
        self.exited = True

    def get_packet(self):
        '''
        allows the port listener to pull a packet from the non-blocking queue
        '''
        got = False
        packet = None
        while not got:
            if len(self.queue) != 0:
                packet = self.queue.popleft()
                got = True
        return packet















