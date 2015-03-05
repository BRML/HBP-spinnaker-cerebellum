/*
 * stdfix-exp.c
 *
 *
 *  SUMMARY
 *   An implementation of exponential for fixpoint accum 
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
 *    20 February, 2014
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 20 February 2014
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "stdfix-exp.h"
#include "utils.h"

//#include "stdfix-exp-impl.h"
//#include "debug.h"

// The following array has entry [n]
static uint64_t __exp_hi [26] = 
  {9708,  26389,         71733,        194991,         530041,        1440801,
        3916503,      10646160,      28939262,       78665070,      213833830,
      581260615,    1580030169,    4294967296,    11674931555,    31735754293,
    86266724208,  234497268814,  637429664642,  1732713474316,  4710003551159,
 12803117065094,34802480465680,94602950235157,257157480542844,699026506411923};

static uint32_t __expm1_mid [16] =
  {         0,  260218914,  504671961,  734314346,
    950043403, 1152702096, 1343082321, 1521927990,
   1689937949, 1847768698, 1996036966, 2135322113,
   2266168400, 2389087112, 2504558555, 2613033936};

static uint32_t __exp_series [3] = { 5294, 4293434720, 2081624032};

// the following calculates a series expansion
// for 1 - exp (-x/2^15) for x in [0..2^11 - 1]

static inline uint32_t coef_mult (uint32_t c, uint32_t x)
{
  uint64_t tmp = ((uint64_t)c * (uint64_t)x) >> 32;

  return ((uint32_t)(tmp));
}

uint32_t exp_series (uint32_t x)
{
  uint32_t tmp;

  //log_info ("x = %u", x);
  tmp  = __exp_series [1] - coef_mult (__exp_series [2], x);

  //log_info (". tmp = %u", tmp);
  tmp  = coef_mult (tmp, x);
  //log_info (".. tmp = %u", tmp);
  tmp += __exp_series [0];
  //tmp = tmp >> 4;
  //log_info ("... tmp = %u (= %16.8K)", tmp, ukbits (tmp >> 16));

  return (tmp);
}

accum expk (accum x)
{
  int_k_t n = bitsk (x);
  int_k_t r;
  int32_t z, f;
  uint32_t y;
  uint64_t tmp1;

  if      ( 363408 < n) r = INT32_MAX; // overflow saturation
  else if (n < -340695) r = 0;         // overflow saturation
  else {
    z = (int32_t)(n) >> 15;       // truncated integer part.
    f = (int32_t)(n) - (z << 15); // fractional remainder

    if (f > 0) {
      z = z + 1;
      f = 32768 - f;

      tmp1  = __exp_hi [13+z];
      tmp1 -= scale64 (tmp1, __expm1_mid [f >> 11]);

      y = ((uint32_t)(f & 0x7FF)) << 17;

      tmp1 -= scale64 (tmp1, exp_series (y));
    }
    else {// (f == 0)
      tmp1 = __exp_hi [13+z];
    }
	 
	 r += 1 << 16;
    r = (int_k_t)(tmp1 >> 17);
  }

  return (kbits(r));
}
