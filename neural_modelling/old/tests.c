/* 
 * test.c
 *
 *
 *  SUMMARY
 *    Tests for spin-neuron.a library
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
 *    
 *
 *  CREATION DATE
 *    11 August, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 11 August 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "spin-neuron-impl.h"


void print_router_table (uint n, uint32_t* key, uint32_t* mask, uint32_t* route)
{
  uint32_t i;
  int j;

  printf ("MC Router Table\n");
  printf ("--------------------------------------------------------------------------------\n");
  for (i = 0; i < n; i++) {
    printf ("%4u (k=%08x, m=%08x, r=%08x): ", i, key[i], mask[i], route[i]);
    for (j = 32; j > 0; j--)
      print_router_bit ((mask[i] >> (j-1) &1), (key[i] >> (j-1) &1));
    printf(":   ");
    for (j = 24; j > 0; j--) {
      if (j == 6) printf("  ");
      printf ("%c", (((route[i] >> (j-1)) & 1) == 0)? '0':'1');
    }
    printf ("\n");
  }
  printf ("--------------------------------------------------------------------------------\n");
}

void print_router_bit (uint32_t m, uint32_t k)
{
  if (m == 0)
    if (k == 0) printf ("x"); else printf ("?");
  else
    if (k == 0) printf ("0"); else printf ("1");
}

void echo_router_table (void)
{
  uint32_t  key      = 0;
  uint32_t  mask     = 0x0;
  uint32_t  route    = 1 << (spin1_get_core_id() + 6);
  uint32_t* key_p    = &key;
  uint32_t* mask_p   = &mask;
  uint32_t* route_p  = &route;

  print_router_table     (1, key_p, mask_p, route_p);
  //configure_router_table (1, key_p, mask_p, route_p);
  log_info("echo router table: set up");
  
}

void print_dma_buffers (void)
{
  uint32_t i,j;
  bool empty;

  printf ("current DMA buffer (index = %d, busy = %c)\n",
	  dma_index, (dma_busy? 'Y': 'N'));
  for (i = 0; i < 32; i++) {
    empty = true;
    for (j = 0; j < 8; j++)
      empty = empty && (current_dma_buffer()[8*i + j] == 0);
    if (!empty) {
      printf ("%4d: ", i);
      for (j = 0; j < 8; j++)
	printf(" %08x", current_dma_buffer()[8*i + j]);
      printf ("\n");
    }
  }

  printf ("next DMA buffer (index = %d)\n", dma_index^1);
  for (i = 0; i < 32; i++) {
    empty = true;
    for (j = 0; j < 8; j++)
      empty = empty && (next_dma_buffer()[8*i + j] == 0);
    if (!empty) {
      printf ("%4d: ", i);
      for (j = 0; j < 8; j++)
	printf(" %08x", next_dma_buffer()[8*i + j]);
      printf ("\n");
    }
  }
}


void print_sdram (uint32_t start, uint32_t items)
{
  uint32_t  count   = 0;
  uint32_t* x       = (uint32_t*)start;
  uint32_t  address = start;
  uint32_t  i       = 0;

  while (count < items && address < SDRAM_TOP) {
    if (!(x[i] == 0 && x[i+1] == 0 && x[i+2] == 0 && x[i+3] == 0)) {
      printf ("%08x: %08x %08x %08x %08x\n",
	      address, x[i], x[i+1], x[i+2], x[i+3]);
    }
    count   +=  4;
    i       +=  4;
    address += 16;
  }
}
