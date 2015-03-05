__author__ = 'stokesa6'

import threading
import thread
import time
import pacman103.conf as conf
from visualiser_main import VisualiserMain
from port_listener import VisulaiserListener

import logging
logger = logging.getLogger(__name__)
import gtk


def _timeout(visualiser, timeout):
    time.sleep(timeout)
    visualiser.stop()

class Visualiser(threading.Thread):
    #sets up listeners
    def __init__(self, dao, timeout=0.0,
                 start_simulation_method = None):
        gtk.threads_init()
        self.visulaiser_main = None
        self.visulaiser_listener = None
        threading.Thread.__init__(self)
        self.bufsize = 65536
        self.done = False
        self.dao = dao
        self.port = None
        self.start_simulation_method = start_simulation_method
        self.finish_event = threading.Event()
        if timeout > 0:
            thread.start_new_thread(_timeout, (self, timeout))
            
    def start_now(self):
        self.start_simulation_method()
        self.finish_event.set()
        
    def wait_for_finish(self):
        self.finish_event.wait()

    def set_timeout(self, timeout):
        print("Timeout set to %f" % timeout)
        if timeout > 0:
            thread.start_new_thread(_timeout, (self, timeout))

    def set_bufsize(self, bufsize):
        self.bufsize = bufsize;

    def stop(self):
        logger.info("[visualiser] Stopping")
        self.done = True
        if (conf.config.getboolean("Visualiser", "have_board") and
            self.visulaiser_listener != None):
            self.visulaiser_listener.stop()

    #runs the visulaiser tools
    def run(self):
        start_method = None
        print "Start: ", self.start_simulation_method
        if self.start_simulation_method is not None:
            start_method = getattr(self, "start_now")

        if conf.config.getboolean("Visualiser", "have_board") and self.port != None:
            self.visulaiser_listener = VisulaiserListener(self.dao.machineTimeStep, 
                    self.dao.time_scale_factor)
            self.visulaiser_listener.set_port(self.port)
        else:
            logger.warn("you are running the visualiser without a board."
                        " Aspects of the visualiser may not work")
        self.visulaiser_main = VisualiserMain(self.dao, self, start_method)
        self.visulaiser_listener.set_visualiser(self.visulaiser_main)

        logger.info("[visualiser] Starting")
        if self.visulaiser_listener is not None:
            self.visulaiser_listener.start()

        gtk.threads_enter()
        self.visulaiser_main.main()
        gtk.threads_leave()
        logger.debug("[visualiser] Exiting")


    def set_port(self, port):
        self.port = port


if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    visulaiser = Visualiser(None)
    visulaiser.start()
