/****h* debug.h/debug.h
 *  NAME
 *    debug.h
 *
 *  SUMMARY
 *    SpiNNaker debug header file
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013. All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *    A header file that can be used to incorporate and control debug information.
 *    It is switched ON  by default; to switch OFF, the code is compiled with
 *
 *      -DPRODUCTION_CODE
 *
 *    By default it is used for SpiNNaker ARM code; it can also  be used in host-side C,
 *    by compiling with -DDEBUG_ON_HOST
 *
 *  EXAMPLES
 *
 *    To use, you must `hash-include' debug.h:
 *
 *      #include "debug.h"
 *
 *    Assertions:
 *
 *      assert(0.0 < c && c < 1.0);                    // assertion checking
 *
 *    Logging errors, warnings and info:
 *
 *      log_error(17,"error");                         // not the most useful message..
 *      log_warning(0,"variable x = %8x", 0xFF);       // variable printing
 *      log_info("function f entered");                // trace
 *
 *    Checking:
 *
 *      check(1==1, "1 !=1 !!!!!!");                   // assertion with message
 *      xp = malloc(n); check_memory(xp);              // checks malloc is non-null
 *
 *    Sentinels:
 *
 *      switch(n) {
 *      ...
 *      default: sentinel("switch: out of range");     // used for control flow checks
 *      .... }
 *
 *    SpiNNaker memory checking:
 *
 *      If we are running on spinnaker hardware, we have the following additional checks available:
 *
 *      check_itcm(addr);
 *      check_dtcm(addr);
 *      check_sysram(addr);
 *      check_sdram(addr);
 *
 *    Controlling the volume of logging information:
 *
 *      -DNO_DEBUG_INFO            Switches OFF the [INFO] information
 *
 *      -D'DEBUG_LOG(n)=(n>10)'    Switches OFF [ERROR]s with number less than or equal 10 
 *
 *      -D'DEBUG_WARN(n)=(n>5)'    Switches OFF [WARNING]s with number less than or equal 5 
 *
 *    By default all information is printed.
 *
 *    There is no way to switch off [ASSERT]s except by using the compilation flag:
 *
 *      -DPRODUCTION_CODE
 *
 *  DETAILS
 *    Created on       : 27 July 2013
 *    Version          : $Revision: 1.1 $
 *    Last modified on : $Date: 2013/08/06 15:11:34 $
 *    Last modified by : $Author: dave $
 *    $Id: debug.h,v 1.1 2013/08/06 15:11:34 dave Exp $
 *
 *    $Log: debug.h,v $
 *    Revision 1.1  2013/08/06 15:11:34  dave
 *    Initial revision
 *
 *
 *********/
#ifndef __DEBUG_H__
#define __DEBUG_H__

#include "spin-print.h"

#ifndef DEBUG_ERROR
#define DEBUG_ERROR(n) (1)
#endif /* DEBUG_ERROR: defaults to logging all errors */

#ifndef DEBUG_WARN
#define DEBUG_WARN(n) (1)
#endif /* DEBUG_WARN: defaults to logging all warnings */

/****d* debug.h/abort
 *  NAME
 *    abort
 *  SOURCE
*/
#define abort(n) do { exit(n); } while (0)

#ifndef PRODUCTION_CODE
#define __debug_message(m1, m2, ...)					\
  do { fprintf(stderr, m1 "(%s:%4d): " m2 "\n",				\
	       __FILE__, __LINE__, ##__VA_ARGS__); } while (0)

#define check(a, s, ...)						\
  do { if (!(a)) __debug_message("[CHECK]    ", s, ##__VA_ARGS__);	\
     } while (0)

#define sentinel(s, ...)						\
  do { __debug_message("[SENTINEL] ", s, ##__VA_ARGS__); abort(0);	\
     } while (0)

#else  /* PRODUCTION_CODE */
#define __debug_message(m1, m2, ...) skip ()
#define check(a, s, ...)             skip ()
#define sentinel(s, ...)             skip ()
#endif /* PRODUCTION_CODE */

#define assert(a) __debug_maybe((!(a)), "[ASSERT]   ", "assertion check fails")

#define assert_info(a, s, ...)\
do { if (!(a)) { __debug_message("[ASSERT]   ", s, ##__VA_ARGS__); }} while (0)

#define debug(m, ...) __debug_message("[DEBUG]    ", m, ##__VA_ARGS__)

#define __debug_maybe(c,m, ...) do { if ((c)) __debug_message(m, ##__VA_ARGS__); } while(0)

#define log_error(n,e, ...)						\
  __debug_maybe(DEBUG_ERROR(n), "[ERROR]   ", e, ##__VA_ARGS__)

#define log_warning(n, w, ...)						\
  __debug_maybe(DEBUG_WARN(n),  "[WARNING] ", w, ##__VA_ARGS__)

#ifndef NO_DEBUG_INFO
#define log_info(i, ...) __debug_message("[INFO]     ", i, ##__VA_ARGS__)
#else  /* NO_DEBUG_INFO */
#define log_info(i, ...) skip ()
#endif /* NO_DEBUG_INFO */

static inline unsigned int __addr__ (void* ptr) { return ((unsigned int)(ptr)); }

#define check_memory(a) check((a), "Out of memory")

#ifndef DEBUG_ON_HOST
#define check_itcm(a)   check((ITCM_BASE   <= __addr__(a) && __addr__(a) < ITCM_TOP),   \
			      "%x is not in ITCM", (a))

#define check_dtcm(a)   check((DTCM_BASE   <= __addr__(a) && __addr__(a) < DTCM_TOP),   \
			      "%x is not in DTCM", (a))

#define check_sysram(a) check((SYSRAM_BASE <= __addr__(a) && __addr__(a) < SYSRAM_TOP), \
			      "%x is not in sysRAM", (a))

#define check_sdram(a)  check((SDRAM_BASE  <= __addr__(a) && __addr__(a) < SDRAM_TOP),  \
			      "%x is not in sdram", (a))
#else  /* DEBUG_ON_HOST */
#define check_itcm(a)   skip ()
#define check_dtcm(a)   skip ()
#define check_sysram(a) skip ()
#define check_sdram(a)  skip ()
#endif /* DEBUG_ON_HOST */


#endif /* __DEBUG_H__ */
