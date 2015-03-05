/*
 * bit_field.h
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

#ifndef __BIT_FIELD_H__
#define __BIT_FIELD_H__

#include <stdint.h>
#include <stdbool.h>

#ifndef use
#define use(x) do {} while ((x)!=(x))
#endif

typedef uint32_t* bit_field_t;

#ifndef __SIZE_T__
typedef uint32_t size_t;
#define __SIZE_T__
#endif /*__SIZE_T__*/

#ifndef __INDEX_T__
typedef uint32_t index_t;
#define __INDEX_T__
#endif /*__INDEX_T__*/

#ifndef __COUNTER_T__
typedef uint32_t counter_t;
#define __COUNTER_T__
#endif /*__COUNTER_T__*/

static inline bool bit_field_test (bit_field_t b, index_t n)
{ return ((b [n >> 5] & (1 << (n & 0x1F))) != 0); }

static inline void bit_field_clear(bit_field_t b, index_t n)
{ b [n >> 5] &= ~(1 << (n & 0x1F)); }

static inline void bit_field_set  (bit_field_t b, index_t n)
{ b [n >> 5] |= (1 << (n & 0x1F)); }

static inline void not_bit_field (bit_field_t b, size_t s)
{ for ( ; s > 0; s--) b [s-1] = ~ (b [s-1]); }

static inline void and_bit_fields (bit_field_t b1, bit_field_t b2, size_t s)
{ for ( ; s > 0; s--) b1 [s-1] &= b2 [s-1]; }

static inline void or_bit_fields  (bit_field_t b1, bit_field_t b2, size_t s)
{ for ( ; s > 0; s--) b1 [s-1] |= b2 [s-1]; }

static inline void clear_bit_field (bit_field_t b, size_t s)
{ for ( ; s > 0; s--) b [s-1] = 0; }

static inline void set_bit_field  (bit_field_t b, size_t s)
{ for ( ; s > 0; s--) b [s-1] = 0xFFFFFFFF; }

static inline bool empty_bit_field (bit_field_t b, size_t s)
{
  bool empty = true;

  for ( ; s > 0; s--)
    empty = empty && (b [s-1] == 0);

  return (empty);
}

static inline bool nonempty_bit_field  (bit_field_t b, size_t s)
{ return (!empty_bit_field (b, s)); }

// Helper to calculate the minimum bit-field size (in words) required to hold 'bits' bits
size_t get_bit_field_size(size_t bits);

#ifdef DEBUG
void print_bit_field_bits  (bit_field_t b, size_t s);
void print_bit_field       (bit_field_t b, size_t s);
void random_bit_field      (bit_field_t b, size_t s);
#endif /*DEBUG*/

#endif /*__BIT_FIELD_H__*/
