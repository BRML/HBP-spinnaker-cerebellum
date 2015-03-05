/* iaf_psc_exp.c
 *
 * Authors Dave, Yuri and Abigail
 *
 *  CREATION DATE
 *    1 August, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 1 August 2013
 *    Version          : $Revision: 1.1 $
 *    Last modified on : $Date: 2013/08/06 15:55:46 $
 *    Last modified by : $Author: dave $
 *    $Id: iaf_psc_exp.c,v 1.1 2013/08/06 15:55:46 dave Exp dave $
 *
 *    $Log: iaf_psc_exp.c,v $
 *    Revision 1.1  2013/08/06 15:55:46  dave
 *    Initial revision
 *
 *
 */

#include "spin-neuron-impl.h"

void iaf_psc_exp_dynamics(uint32_t n)
{

  if (absolutely_refractory(n))
    refractory_clock[n]--;
  else
    membrane_dynamics (n);

  synapse_dynamics (n);
  ring_buffer_transfer(n);

  spike_emission (n);
}

void membrane_dynamics (uint32_t n)
{
  synapse_input_t input = current_to_input(n);

  v_membrane[n] = v_membrane[n]* p22[n] + input * p21[n];
}

void synapse_dynamics (register uint32_t n) { current[n] *= p11[n]; }


