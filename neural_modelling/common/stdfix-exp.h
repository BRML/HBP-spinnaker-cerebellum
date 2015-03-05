/*
 * stdfix-exp.h
 *
 *
 *  SUMMARY
 *    The API file for a non-garbage-collected memory manager.
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

#ifndef __STDFIX_EXP_H__
#define __STDFIX_EXP_H__

#include <stdint.h>
#include <stdfix.h>
#include <stdbool.h>

#include "stdfix-full-iso.h"


// stdfix-exp API

accum expk( accum x );

uint32_t exp_series (uint32_t x);

#endif /*__STDFIX_EXP_H__*/
