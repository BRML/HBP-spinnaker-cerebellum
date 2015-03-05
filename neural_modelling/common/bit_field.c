/*
 * bit_field.c
 *
 *
 *  SUMMARY
 *    Bit field manipulation.
 *
 *    A bit field is a vector of machine words which is
 *    treated as a vector of bits.
 *
 *    For SpiNNAker each machine word is 32 bits, and so a
 *    bit_field for each neuron (assuming 256 neurons)
 *    would be 8 words long.
 *
 *    The API includes:
 *
 *     (-) bit_field_test (b, n)
 *         returns true of false depending on whether bit n is set or clear
 *     (-) bit_field_set (b, n) / bit_field_clear (b, n)
 *         used to set or clear bit n
 *     (-) not_bit_field (b, s)
 *         logically inverts a bit field of size s.
 *     (-) and_bit_field / or_bit_field
 *         logically ands/ors two bit_fields together. Requires size.
 *     (-) clear_bit_field/set_bit_field
 *         Initializes bit_field with all false (= clear) or true (= set).
 *         Requires size.
 *
 *    There are also support functions for:
 *     
 *     (-) printing (if #def'd)
 *     (-) randomly setting up a bit field
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
 *    12 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 12 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "bit_field.h"

size_t get_bit_field_size(size_t bits)
{
  // **NOTE** in floating point terms this is ceil(num_neurons / 32)
  const uint32_t bits_to_words_shift = 5;
  const uint32_t bits_to_words_remainder = (1 << bits_to_words_shift) - 1;
  
  // Down shift number of bits to words
  uint32_t words = bits >> bits_to_words_shift;
  
  // If there was a remainder, add an extra word
  if((bits & bits_to_words_remainder) != 0)
  {
    words++;
  }
  
  return words;
}

#ifdef DEBUG
#include "sark.h"

static inline void print_bit_field_entry (uint32_t e)
{
  counter_t i = 32;

  for ( ; i > 0; i--) {
    io_printf (IO_BUF, "%c", ((e & 0x1) == 0)? ' ': '1');
    e = e >> 1;
  }
  io_printf (IO_BUF, "\n");
}

void print_bit_field_bits (bit_field_t b, size_t s)
{
  index_t i;

  for (i = 0; i < s; i++)
    print_bit_field_entry (b [i]);
}

void print_bit_field (bit_field_t b, size_t s)
{
  index_t i;

  for (i = 0; i < s; i++)
    io_printf (IO_BUF, "%08x\n", b [i]);
}

void random_bit_field (bit_field_t b, size_t s)
{
  index_t i;

  for (i = 0; i < s; i++)
    b [i] = sark_rand();
}
#else /*DEBUG*/
void print_bit_field_bits (bit_field_t b, size_t s) { use(b); use(s); return; }
void print_bit_field      (bit_field_t b, size_t s) { use(b); use(s); return; }
void random_bit_field     (bit_field_t b, size_t s) { use(b); use(s); return; }
#endif /*DEBUG*/
