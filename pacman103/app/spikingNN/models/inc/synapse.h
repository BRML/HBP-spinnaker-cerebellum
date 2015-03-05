/****h* neuron/synapse.h
 *  NAME
 *    synapse.h
 *
 *  DESCRIPTION
 *    Replacement implementation of synaptic processing
 *
 *  COPYRIGHT
 *    (c) 2013, Dave Lester, The University of Manchester
 *
 *  CREATION DATE
 *    18 July, 2013
 *
 *  HISTORY
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

#ifndef __SYNAPSE_H__
/****d* synapse.h/__SYNAPSE_H__
 *  NAME
 *    __SYNAPSE_H__
 *  SOURCE
*/
#define __SYNAPSE_H__

#include <stdint.h>

/************ __SYNAPSE_H__ */
/****d* synapse.h/DISABLE_IRQ
 *  NAME
 *    DISABLE_IRQ
 *  PURPOSE
 *    Disables irq, to prevent unwanted interactions.
 *  SOURCE
*/
#define DISABLE_IRQ do { cpsr = spin1_irq_disable(); } while (0)
/************ DISABLE_IRQ */
/****d* synapse.h/ENABLE_IRQ
 *  NAME
 *    ENABLE_IRQ
 *  PURPOSE
 *    Re-enables irq, after of critical section.
 *  SOURCE
*/
#define ENABLE_IRQ  do { spin1_mode_restore(cpsr);   } while (0)

#ifndef SYNAPSE_INDEX_BITS
/************ ENABLE_IRQ */
/****d* synapse.h/SYNAPSE_INDEX_BITS
 *  NAME
 *    SYNAPSE_INDEX_BITS
 *  PURPOSE
 *    Number of bits used to index buffers. Has to be greater than the number of neurons
 *  SOURCE
*/
#define SYNAPSE_INDEX_BITS 8
#endif

/*
 * We can use common excitatory/inhibitory synapses under two conditions:
 *
 *   (1) We are implementing delta synapses (instantaneous transfer of
 *       weight onto membrane); or
 *   (2) Although there are both excitatory and inhibitory synapses,
 *       the decay time-constants are identical.
 *
 * In the first case, we do not need to have signed weights, if there
 * are no inhibitory synapses.
 *
 * We therefore have two flags:
 *
 *    COMBINED_EXCITATORY_INHIBITORY, which indicates that we do not need to distinguish
 *                                    synapse types (excitatory and inhibitory); and
 *    SYNAPSE_WEIGHTS_SIGNED,         which indicates whether the weights are signed (or not)
 *
 */
#ifdef COMBINED_EXCITATORY_INHIBITORY
/************ SYNAPSE_INDEX_BITS */
/****d* synapse.h/SYNAPSE_TYPE_BITS
 *  NAME
 *    SYNAPSE_TYPE_BITS
 *  SOURCE
*/
#define SYNAPSE_TYPE_BITS 0
#else
/************ SYNAPSE_TYPE_BITS */
/****d* synapse.h/SYNAPSE_TYPE_BITS
 *  NAME
 *    SYNAPSE_TYPE_BITS
 *  SOURCE
*/
#define SYNAPSE_TYPE_BITS 1
#endif

#ifndef SYNAPSE_DELAY_BITS
/************ SYNAPSE_TYPE_BITS */
/****d* synapse.h/SYNAPSE_DELAY_BITS
 *  NAME
 *    SYNAPSE_DELAY_BITS
 *  SOURCE
*/
#define SYNAPSE_DELAY_BITS 4
#endif

/************ SYNAPSE_DELAY_BITS */
/****d* synapse.h/SYNAPSE_BUFFER_SIZE
 *  NAME
 *    SYNAPSE_BUFFER_SIZE
 *  SOURCE
*/
#define SYNAPSE_BUFFER_SIZE (1 << (SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS))
/************ SYNAPSE_BUFFER_SIZE */
/****d* synapse.h/SYNAPSE_PSP_BUFFER_SIZE
 *  NAME
 *    SYNAPSE_PSP_BUFFER_SIZE
 *  SOURCE
*/
#define SYNAPSE_PSP_BUFFER_SIZE (SYNAPSE_BUFFER_SIZE * (1 << SYNAPSE_DELAY_BITS))

/*
 * If the elements of the spike buffers are 32 bit quantities, then the total:
 *
 *      SYNAPSE_DELAY_BITS + SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS <= 13
 *
 * (otherwise we will need to use the _whole_ of DTCM for the buffers).
 */

/* SYNAPSE_WEIGHT_BITS: number of bits in the weights of each synapse */
#ifndef SYNAPSE_WEIGHT_BITS
/************ SYNAPSE_PSP_BUFFER_SIZE */
/****d* synapse.h/SYNAPSE_WEIGHT_BITS
 *  NAME
 *    SYNAPSE_WEIGHT_BITS
 *  SOURCE
*/
#define SYNAPSE_WEIGHT_BITS 16
#endif
/* SYNAPSE_PSP_BITS: number of bits of the elements in the psp buffer */
#ifndef SYNAPSE_PSP_BITS
/************ SYNAPSE_WEIGHT_BITS */
/****d* synapse.h/SYNAPSE_PSP_BITS
 *  NAME
 *    SYNAPSE_PSP_BITS
 *  SOURCE
*/
#define SYNAPSE_PSP_BITS 32
#endif
/* CURRENT_BITS: number of bits in the neuron currents */
#ifndef CURRENT_BITS
/************ SYNAPSE_PSP_BITS */
/****d* synapse.h/CURRENT_BITS
 *  NAME
 *    CURRENT_BITS
 *  SOURCE
*/
#define CURRENT_BITS 32
#endif
/* DECAY_BITS: number of bits in the decay multipliers */
#ifndef DECAY_BITS
/************ CURRENT_BITS */
/****d* synapse.h/DECAY_BITS
 *  NAME
 *    DECAY_BITS
 *  SOURCE
*/
#define DECAY_BITS CURRENT_BITS
#endif

/************ DECAY_BITS */
/****d* synapse.h/__int_helper
 *  NAME
 *    __int_helper
 *  SOURCE
*/
#define __int_helper(b) int ## b ## _t
/************ __int_helper */
/****d* synapse.h/__int_t
 *  NAME
 *    __int_t
 *  SOURCE
*/
#define __int_t(b) __int_helper(b)
/************ __int_t */
/****d* synapse.h/__uint_helper
 *  NAME
 *    __uint_helper
 *  SOURCE
*/
#define __uint_helper(b) uint ## b ## _t
/************ __uint_helper */
/****d* synapse.h/__uint_t
 *  NAME
 *    __uint_t
 *  SOURCE
*/
#define __uint_t(b) __uint_helper(b)

#ifdef SYNAPSE_WEIGHTS_SIGNED
/************ __uint_t */
typedef  __int_t(SYNAPSE_WEIGHT_BITS) synapse_weight_t;
#else
typedef __uint_t(SYNAPSE_WEIGHT_BITS) synapse_weight_t;
#endif

#ifdef COMBINED_EXCITATORY_INHIBITORY
typedef  __int_t(SYNAPSE_PSP_BITS)    synapse_psp_t;
typedef  __int_t(CURRENT_BITS)        current_t;
#else
typedef  __uint_t(SYNAPSE_PSP_BITS)   synapse_psp_t;
typedef  __uint_t(CURRENT_BITS)       current_t;
#endif

typedef __uint_t(DECAY_BITS)          decay_t;


/****d* synapse.h/SYNAPSE_TYPE_MASK
 *  NAME
 *    SYNAPSE_TYPE_MASK
 *  SOURCE
*/
#define SYNAPSE_TYPE_MASK       (1 << SYNAPSE_INDEX_BITS)
/************ SYNAPSE_TYPE_MASK */
/****d* synapse.h/SYNAPSE_TYPE_INDEX_BITS
 *  NAME
 *    SYNAPSE_TYPE_INDEX_BITS
 *  SOURCE
*/
#define SYNAPSE_TYPE_INDEX_BITS (SYNAPSE_TYPE_BITS + SYNAPSE_INDEX_BITS)
/************ SYNAPSE_TYPE_INDEX_BITS */
/****d* synapse.h/SYNAPSE_TYPE_INDEX_MASK
 *  NAME
 *    SYNAPSE_TYPE_INDEX_MASK
 *  SOURCE
*/
#define SYNAPSE_TYPE_INDEX_MASK ((1 << SYNAPSE_TYPE_INDEX_BITS) - 1)
/************ SYNAPSE_TYPE_INDEX_MASK */
/****d* synapse.h/SYNAPSE_DELAY_MASK
 *  NAME
 *    SYNAPSE_DELAY_MASK
 *  SOURCE
*/
#define SYNAPSE_DELAY_MASK      ((1 << SYNAPSE_DELAY_BITS) - 1)
/************ SYNAPSE_DELAY_MASK */

typedef struct {
  uint32_t* indices_delays_weights;
} sparse_synaptic_row_t;

typedef union {
  decay_t  constant_decay; /* used if the control flag is 1, indicating fixed decays */
  decay_t* variable_decay; /* used if the control flag is 0, indicating an array of decays */
} union_decay_t;

/* Declarations for synapse.c */
void post_synaptic_processing             (synaptic_row_t*        synaptic_row, uint32_t i);
void sparse_post_synaptic_processing      (sparse_synaptic_row_t* synaptic_row, uint32_t i);
void pre_synaptic_processing_delta        (int32_t n);
void pre_synaptic_processing_exp_constant (int32_t n);
void pre_synaptic_processing_exp_variable (int32_t n);

/* Following are offset calculations into post-synaptic spike buffers */

/****d* synapse.h/sparse_index_type
 *  NAME
 *    sparse_index_type
 *  SOURCE
*/
#define sparse_index_type(x) ((x) & SYNAPSE_TYPE_INDEX_MASK)
/************ sparse_index_type */
/****d* synapse.h/sparse_delay
 *  NAME
 *    sparse_delay
 *  SOURCE
*/
#define sparse_delay(x)      (((x) >> SYNAPSE_TYPE_INDEX_BITS) & SYNAPSE_DELAY_MASK)
/************ sparse_delay */
/****d* synapse.h/sparse_weight
 *  NAME
 *    sparse_weight
 *  SOURCE
*/
#define sparse_weight(x)     ((synapse_weight_t)((x) >> (32-SYNAPSE_WEIGHT_BITS)))
/************ sparse_weight */
/****d* synapse.h/offset_sparse
 *  NAME
 *    offset_sparse
 *  SOURCE
*/
#define offset_sparse(d,ti)  ((((d) & SYNAPSE_DELAY_MASK) << SYNAPSE_TYPE_INDEX_BITS) | (ti))
/************ offset_sparse */
/****d* synapse.h/offset_psp
 *  NAME
 *    offset_psp
 *  SOURCE
*/
#define offset_psp(d,t,i)    ((((d) & SYNAPSE_DELAY_MASK) << SYNAPSE_TYPE_INDEX_BITS) | \
			      ((t) << SYNAPSE_INDEX_BITS) | (i))

#endif /* __SYNAPSE_H__ */
/************ offset_psp */
