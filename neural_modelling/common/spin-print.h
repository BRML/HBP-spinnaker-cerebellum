/*
 * spin-print.h
 *
 *  SUMMARY
 *    For quick changing between host-side and spinnaker side C code printing
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *    A header file that can be used as with SpiNNaker to make IO more
 *    seamless.
 *
 *
 *  CREATION DATE
 *    29 July, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 29 July 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 *
 *
 */

#ifndef __SPIN_PRINT_H__
#define __SPIN_PRINT_H__

static inline void skip (void) { return; }

#ifdef DEBUG_ON_HOST
#include <stdlib.h>
#include <stdio.h>

#define spin1_dma_transfer(tag,s,t,d,l) \
  do log_info("spin1_dma_transfer (%u, %u)",(s),(t)); while(0)

#define spin1_trigger_user_event(a,b)   \
  do log_info("spin1_trigger_user_event (%d, %d)",(a),(b)); while(0)

#define c_main c_main(void); int main(void) { c_main(); return (0); } void c_main

#else /* DEBUG_ON_HOST */
#include "sark.h"
#include "spin1_api.h"

#undef  malloc
#define malloc spin1_malloc
#undef  srandom
#define srandom spin1_srand
#undef  random
#define random spin1_rand
#undef  fprintf
#define fprintf io_printf
#undef  stdout
#define stdout IO_BUF
#undef  stderr
#define stderr IO_BUF
#undef  printf
#define printf(s, ...) do { io_printf(IO_BUF, s, ##__VA_ARGS__); } while (0)
#undef  putchar
#define putchar(c) do { io_printf(IO_BUF, "%c", c); } while (0)
#undef  exit
#define exit(n) do { spin1_exit(n); } while (0)

//void c_main ();

#endif /* DEBUG_ON_HOST */
#endif /* __SPIN_PRINT_H__ */
