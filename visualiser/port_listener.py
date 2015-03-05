__author__ = 'stokesa6'

import socket
import struct
import threading
import thread
import time
import logging
import datetime
import traceback
from pacman103.conf import config
logger = logging.getLogger(__name__)
from pacman103.core.utilities import packet_conversions
from port_queuer import PortQueuer


def _timeout(visualiser, timeout):
    time.sleep(timeout)
    visualiser.stop()


class VisulaiserListener(threading.Thread):

    def __init__(self, machine_time_step, time_scale_factor):
        threading.Thread.__init__(self)
        self.machine_time_step = machine_time_step
        self.time_scale_factor = time_scale_factor
        self.visualiser = None
        self.done = False
        self.queuer = PortQueuer()
        self.DEBUG = config.getboolean("Visualiser", "debug")

    def set_visualiser(self, vis):
        self.visualiser = vis

    def set_timeout(self, timeout):
        print("Timeout set to %f" % timeout)
        if timeout > 0:
            thread.start_new_thread(_timeout, (self, timeout))
            self.queuer.set_timeout(timeout)

    def set_bufsize(self, bufsize):
        self.bufsize = bufsize;

    def stop(self):
        logger.info("[port_listener] Stopping")
        self.queuer.stop()
        self.done = True

    def set_port(self, port):
        self.queuer.set_port(port)

    def run(self):
        logger.info("[port_listener] starting")
        self.queuer.start()
        last_update_time = datetime.datetime.now()
        t_tic = 0
        last_time_packet_recieved = datetime.datetime.now()
        if self.DEBUG:
            max_neuronid = 200
        while not self.done:
            try:
                t_tic, last_update_time = self.handle_timer_forces(
                        last_update_time, last_time_packet_recieved, t_tic)
                # if done every 200 ms


                if not self.DEBUG:
                    #print "trying to recive"
                    data = self.queuer.get_packet()
                    if data is None:
                        break
                    
                    # print "received"
                    (ip_time_out_byte, pad_byte, flags_byte, tag_byte,
                     dest_port_byte, source_port_byte, dest_addr_short,
                     source_addr_short, command_short, sequence_short,
                     arg1_int, arg2_int, arg3_int) =\
                        struct.unpack_from("<BBBBBBHHHHiii", data, 0)
                    header_length = 26
                    spikedatalen = len(data) - header_length
                    t_tic = arg1_int
                    last_time_packet_recieved = datetime.datetime.now()

                    for spike in range(0, spikedatalen, 4):
                        spikeWord = struct.unpack_from("<I", data, spike + header_length)[0]
                        x = packet_conversions.get_x_from_key(spikeWord)
                        y = packet_conversions.get_y_from_key(spikeWord)
                        p = packet_conversions.get_p_from_key(spikeWord)
                        nid = packet_conversions.get_nid_from_key(spikeWord)
                        # logger.debug("received packet from {},{},{}".format(x,y,p))
                        self.visualiser.spike_recieved({'coords':[x,y,p],
                                                       'neuron_id':nid,
                                                       'tag': tag_byte,
                                                       'time_in_ticks': t_tic,
                                                       'spike_word': spikeWord})
                else:#create fake spikes
                    t_tic = self.generate_fake_spikes(packet_count, t_tic)

            except socket.timeout:
                pass
            except Exception as e:
                if not self.done:
                    traceback.print_exc()
                    logger.debug("[visualiser_listener] Error receiving data: %s" % e)


    def handle_timer_forces(self, last_update_time, last_time_packet_recieved, t_tic):
        
        now = datetime.datetime.now()
        time_since_last_update = now - last_update_time
        if time_since_last_update.microseconds >= 100:
            time_since_last_packet_received = (datetime.datetime.now() 
                    - last_time_packet_recieved)
            extra = ((time_since_last_packet_received.total_seconds() 
                            * 1000000.0) 
                    / (self.machine_time_step * self.time_scale_factor))
            t_tic = t_tic + extra
            self.visualiser.cool_downer()
            self.visualiser.redraw_graphs(t_tic)
            last_update_time = now
        #deal with possible call backs
        resets = self.visualiser.get_resets()
        for entry in resets:
            if entry['pt'] is None and t_tic >= entry['t']:
                entry['p'].reset_values()
                entry['pt'] = t_tic
                entry['p'].set_reset(entry)
            if entry['pt'] is not None and t_tic >= entry['t']+entry['pt']:
                entry['p'].reset_values()
                entry['pt'] = t_tic
                entry['p'].set_reset(entry)
        return t_tic, last_update_time


    def generate_fake_spikes(self, packet_count, t_tic):
        time.sleep(0.1)
        x = 0
        y = 0
        p = 2
        nid = packet_count
        spike_word = x << 24 | y << 16 | p - 1 << 11 | nid

        packet_count += 1
        if packet_count >= 100:
            packet_count = 0
        last_time_packet_recieved = datetime.datetime.now()
        self.visualiser.spike_recieved({'coords':[x,y,p],
                                       'neuron_id':nid,
                                       'tag': None,
                                       'time_in_ticks': t_tic,
                                       'spike_word': spike_word})
        t_tic += 1
        return t_tic


