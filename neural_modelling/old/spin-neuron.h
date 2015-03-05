/****h* spin-neuron/spin-neuron.h
 *  NAME
 *    spin-neuron.h
 *
 *  SUMMARY
 *    SpiNNaker Neuron-modelling API file
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *    A header file that can be used as the API for the spin-neuron.a library.
 *    To use the code is compiled with
 *
 *      #include "debug.h"
 *
 *  CREATION DATE
 *    21 July, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 27 July 2013
 *    Version          : $Revision: 1.1 $
 *    Last modified on : $Date: 2013/08/06 15:31:48 $
 *    Last modified by : $Author: dave $
 *    $Id: spin-neuron.h,v 1.1 2013/08/06 15:31:48 dave Exp dave $
 *
 *    $Log: spin-neuron.h,v $
 *    Revision 1.1  2013/08/06 15:31:48  dave
 *    Initial revision
 *
 *
 *********/


/*
 * Data representation in sparse psp:
 * 
 * +----------+----------+----------+----------+
 * |       weight        |   delay x|   index  |
 * +----------+----------+----------+----------+
 *
 * Standard Default layout:
 *
 *   [31:16] weight is 16 bits,
 *   [12:9]  delay  is 4 bits,
 *   [8]     x      is an optional one bit indicating whether
 *                       we need seperate excitatory/inhibitory synapses. 
 *   [7:0]   index  is 8 bits of neuron index.
 *
 * We can manipulate the quantities in delay/x/index, provided the
 * total is less than or equal to 13 (for 32 bit buffers), or 14
 * (for 16 bit buffers).
 *
 */

#ifndef __SPIN_NEURON_H__
#define __SPIN_NEURON_H__

#include "spin-neuron-typedefs.h"

// Declarations for spin1-api-configuration.c

bool system_configured ();

void incoming_spike_callback (uint key,    uint payload);
void dma_callback            (uint unused, uint tag);
void feed_dma_pipeline       (uint unused, uint unused1);
void timer_callback          (uint unused, uint unused1);
void sdp_packet_callback     (uint msg,    uint unused);

/* Declarations for tests.c */

void print_ring                           (void);
void print_currents                       (void);
void reset_outspike                       (void);
void print_outspikes                      (void);

bool  incoming_spike_tests (void);

#endif /* __SPIN_NEURON_H__ */
