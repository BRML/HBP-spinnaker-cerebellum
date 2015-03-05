/****h* neuron/synapse.c
 *  NAME
 *    synapse.c
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

#include "spin1_api.h"
#include "dma.h"
#include "synapse.h"

/****v* synapse.c/psp
 *  NAME
 *    psp
 *  SYNOPSIS
 *    synapse_psp_t psp[SYNAPSE_PSP_BUFFER_SIZE];
 *  PURPOSE
 *    A flat buffer area for post-synaptic potentials (or spikes)
 *  SOURCE
*/
synapse_psp_t psp[SYNAPSE_PSP_BUFFER_SIZE]; /* All psps are dealt with together */
/************ psp */
/****v* synapse.c/current
 *  NAME
 *    current
 *  SYNOPSIS
 *    current_t current[SYNAPSE_BUFFER_SIZE];
 *  PURPOSE
 *    Input currents for all neurons
 *  SOURCE
*/
current_t current[SYNAPSE_BUFFER_SIZE];
/************ current */
/****v* synapse.c/excitatory_decays
 *  NAME
 *    excitatory_decays
 *  SYNOPSIS
 *    excitatory_decays;
 *  PURPOSE
 *    Input currents for all neurons
 *  SOURCE
*/
union_decay_t excitatory_decays;
/************ excitatory_decays */
/****v* synapse.c/inhibitory_decays
 *  NAME
 *    inhibitory_decays
 *  SYNOPSIS
 *    inhibitory_decays;
 *  PURPOSE
 *    Input currents for all neurons
 *  SOURCE
*/
union_decay_t inhibitory_decays;
/************ inhibitory_decays */
/****v* synapse.c/time
 *  NAME
 *    time
 *  SYNOPSIS
 *    uint32_t time;
 *  PURPOSE
 *    Current low-order time. Set once at the beginning of timer_callback.
 *  SOURCE
*/
uint32_t time; 
/************ time */
/****f* synapse.c/post_synaptic_processing
 *  NAME
 *    post_synaptic_processing
 *  SYNOPSIS
 *    void post_synaptic_processing (synaptic_row_t* synaptic_row, uint32_t i)
 *  PURPOSE
 *    This is a program stub, which can be adapted (later) for different row types
 *  BUGS
 *    This inlines the called function if agressive optimization is utilized
 *  SOURCE
*/
void post_synaptic_processing (synaptic_row_t* synaptic_row, uint32_t i)
{
  sparse_post_synaptic_processing ((sparse_synaptic_row_t*) synaptic_row, i);
}
/************ post_synaptic_processing */
/****f* synapse.c/sparse_post_synaptic_processing
 *  NAME
 *    sparse_post_synaptic_processing
 *  SYNOPSIS
 *    void sparse_post_synaptic_processing (sparse_synaptic_row_t* synaptic_row, uint32_t i)
 *  PURPOSE
 *    Transfer of synaptic row information into post-synaptic potential buffers
 *  IDEAS
 *    Could be suitable for __leaf__ and/or __inline__ attributes
 *  SOURCE
*/
void sparse_post_synaptic_processing (sparse_synaptic_row_t* synaptic_row, uint32_t i)
{
  register uint32_t *xp = synaptic_row -> indices_delays_weights;
  register uint32_t x,d;
  register synapse_weight_t w;
  register uint32_t off, index;
  register synapse_psp_t *pspp = psp;
  register uint32_t t = time;

  for ( ; i > 0; i--) {
    x = *xp++;

    d     = sparse_delay(x);
    index = sparse_index_type(x);
    w     = sparse_weight(x);
    off   = offset_sparse(d+t,index);

    pspp[off] += w;
  }
}
/************ sparse_post_synaptic_processing */
/****f* synapse.c/pre_synaptic_processing_delta
 *  NAME
 *    pre_synaptic_processing_delta
 *  SYNOPSIS
 *    void pre_synaptic_processing_delta (int32_t n)
 *  PURPOSE
 *    Transfer of post-synaptic potential buffers into neuron inputs.
 *    This version dumps the current onto the membrane in one go.
 *  SOURCE
*/
void pre_synaptic_processing_delta (int32_t n)
{
  register uint32_t       offset = offset_sparse(time,0);
  register current_t*     cp     = current;
  register synapse_psp_t* pp     = & psp[offset];
  uint32_t cpsr;

  DISABLE_IRQ; /* we don't want incoming spikes to be brought forward 16 cycles! */
  for ( ; n >= 0; n--) {
    *cp++ = *pp;       // transfer spike to current
    *pp++ = 0;         // zero buffer
  }
  ENABLE_IRQ;
}
/************ pre_synaptic_processing_delta */
/****f* synapse.c/pre_synaptic_processing_exp_constant
 *  NAME
 *    pre_synaptic_processing_exp_constant
 *  SYNOPSIS
 *    void pre_synaptic_processing_exp_constant (int32_t n, decay_t decay_x, decay_t decay_i)
 *  PURPOSE
 *    Transfer of post-synaptic potential buffers into neuron inputs.
 *    This version decays the transfer to the membrane over a period. The decays
 *    are fixed for all synapses in the population.
 *  IDEAS
 *    Consider using fix-point multiplication for the decay.
 *  SOURCE
*/
void pre_synaptic_processing_exp_constant (int32_t n)
{
           decay_t        decay_x = excitatory_decays.constant_decay;
	   decay_t        decay_i = inhibitory_decays.constant_decay;
  register uint32_t       offset  = offset_sparse(time, 0);
  register current_t*     cp      = current + SYNAPSE_TYPE_MASK;
  register synapse_psp_t* pp      = & psp[offset | SYNAPSE_TYPE_MASK];
  register int32_t        i       = n;
           uint32_t       cpsr;

  DISABLE_IRQ; /* we don't want incoming spikes to be brought forward 16 cycles! */
  for ( ; i >= 0; i--) {
    *cp   -= (current_t) (((uint64_t)decay_i * (*cp)) >> 32);     // decay current
    *cp++ += *pp;   // transfer spike to current
    *pp++  = 0;      // zero buffer
  }
  cp = current;
  pp = & psp[offset];
  for (i = n; i >= 0; i--) {
    *cp   -= (current_t) (((uint64_t)decay_x * (*cp)) >> 32);     // decay current
    *cp++ += *pp;     // transfer spike to current
    *pp++  = 0;       // zero buffer
  }
  ENABLE_IRQ;
}
/************ pre_synaptic_processing_exp_constant */
/****f* synapse.c/pre_synaptic_processing_exp_variable
 *  NAME
 *    pre_synaptic_processing_exp_variable
 *  SYNOPSIS
 *    void pre_synaptic_processing_exp_variable (uint32_t n, decay_t* decay)
 *  PURPOSE
 *    Transfer of post-synaptic potential buffers into neuron inputs.
 *    This version decays the transfer to the membrane over a period. The decays
 *    are potentially different for all synapses in the population.
 *  IDEAS
 *    Consider using fix-point multiplication for the decay.
 *  SOURCE
*/
void pre_synaptic_processing_exp_variable (int32_t n)
{
  register uint32_t       offset = offset_sparse(time,0);
  register current_t*     cp     = current;
  register synapse_psp_t* pp     = & psp[offset];
  register decay_t*       dp     = excitatory_decays.variable_decay;
  uint32_t cpsr;

  DISABLE_IRQ;
  for ( ; n >= 0; n--) {
    *cp -= (current_t) (((uint64_t)(*dp++) * (*cp)) >> 32);     // decay current
    *cp++ += *pp;                                               // transfer spike to current
    *pp++ = 0;                                                  // zero buffer
  }
  ENABLE_IRQ;
}
/************ pre_synaptic_processing_exp_variable */




/* Process the psp buffers prior to neuron modelling, transferring the input currents,
 * re-setting emptied buffers to zero, and transferring the decaying current into the next
 * buffer
 */
/*void pre_synaptic_processing_alpha_variable (void)
{
  register int32_t n = SYNAPSE_BUFFER_SIZE;
  register uint32_t this_base_offset = offset_sparse(time,0);
  register uint32_t next_base_offset = offset_sparse(time+1,0);
  uint32_t cpsr;

  DISABLE_IRQ; // we don't want incoming spikes to be brought forward 16 cycles!
  for ( ; n >= 0; n--) {
    // decay currents
    current[this_base_offset | n] -= decay[n] * current[this_base_offset | n];
    if (with_alpha)
      alpha[this_base_offset | n] -= alpha_decay[n] *alpha[this_base_offset | n];
    // decay, decay_alpha are split excite/inhibite. inhibite first.

    // transfer spike to current(s), don't forget alpha.
    current[this_base_offset | n] += psp[this_base_offset | n]; // Transfer buffer to current
    if (with_alpha)
      alpha[this_base_offset | n] += psp[this_base_offset | n]; // Transfer buffer to alpha

    // reset buffer
    psp[this_base_offset | n] = 0;                              // Zero buffer
    // only when the reset has happened is it safe to accept new spikes into delay 16!
  }
  ENABLE_IRQ;
  }*/


