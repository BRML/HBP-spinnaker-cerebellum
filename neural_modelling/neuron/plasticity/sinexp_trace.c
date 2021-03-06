#include "../spin-neuron-impl.h"
#include "../synapses_impl.h"
#include "../../common/compile_time_assert.h"
#include "events_impl.h"
#include "runtime_log.h"

// **NOTE** trace rule header is included by make file

#include <string.h>


#ifdef DEBUG
bool plastic_runtime_log_enabled = false;
#endif	// DEBUG

//---------------------------------------
// Synapse update loop
//---------------------------------------
static inline uint32_t plasticity_update_synapse(uint32_t last_update_time, uint32_t delay, uint32_t current_weight,
  const pre_synaptic_event_history_t *pre_synaptic_event_history, uint32_t post_synaptic_neuron_index)
{
  // Get time and index of first post-synaptic event that occurs in the time window between the last update time of this synaptic row and the current time
  uint32_t next_post_synaptic_event_time;
  uint32_t next_post_synaptic_event_index;
  post_synaptic_event_t last_post_synaptic_event;
  post_synaptic_event_find_first(post_synaptic_neuron_index, last_update_time, &next_post_synaptic_event_index, &next_post_synaptic_event_time, &last_post_synaptic_event);
  
  // Get the pre-synaptic event prior to the window and the one next within it
  uint32_t next_pre_synaptic_event_index;
  uint32_t next_pre_synaptic_event_time;
  pre_synaptic_event_t last_pre_synaptic_event;

  // Create initial deferred update state using weight
  deferred_update_state_t deferred_update_state = stdp_trace_rule_get_initial_deferred_update_state(current_weight);
//  io_printf(IO_BUF,"timer period: %d, delay: %d, size: %d\n", timer_period, plasticity_region_data.t_delay,STDP_TRACE_TAU_PLUS_SIZE);
  
  while(next_post_synaptic_event_index != UINT32_MAX) {
  // we want to start the search at postsyn.time - delay
  uint32_t t0 = MAX(0,last_post_synaptic_event.time - plasticity_region_data.t_delay - STDP_TRACE_TAU_PLUS_SIZE);
  pre_synaptic_event_find_first(pre_synaptic_event_history, t0, delay, &next_pre_synaptic_event_index, &next_pre_synaptic_event_time, &last_pre_synaptic_event);
    while(next_pre_synaptic_event_time < last_post_synaptic_event.time - plasticity_region_data.t_delay) {
      // Update last pre-synaptic event to point to new event we're processing, updating time to delayed version
      last_pre_synaptic_event.trace = pre_synaptic_event_history->traces[next_pre_synaptic_event_index];
      last_pre_synaptic_event.time = next_pre_synaptic_event_time;
//      io_printf(IO_BUF, "post > pre: %d, %d\n",last_post_synaptic_event.time,last_pre_synaptic_event.time);
      
      // Apply pre-synaptic event to deferred update state
      deferred_update_state = stdp_trace_rule_apply_deferred_post_synaptic_spike(last_post_synaptic_event.time, last_post_synaptic_event.trace, 
        last_pre_synaptic_event.time, last_pre_synaptic_event.trace, 
        deferred_update_state);

      // Go on to next pre-synaptic event
      pre_synaptic_event_find_next(pre_synaptic_event_history, delay, next_pre_synaptic_event_index, 
        &next_pre_synaptic_event_index, &next_pre_synaptic_event_time);
    }
      
    post_synaptic_event_find_next(post_synaptic_neuron_index, next_post_synaptic_event_index, 
        &next_post_synaptic_event_index, &next_post_synaptic_event_time);

  }

  // finally count and weight pre synaptic events
  pre_synaptic_event_find_first(pre_synaptic_event_history, last_update_time, delay, &next_pre_synaptic_event_index, &next_pre_synaptic_event_time, &last_pre_synaptic_event);
  while(next_pre_synaptic_event_index != UINT32_MAX) {
     // note that all of those parameters are not used at all 
     deferred_update_state = stdp_trace_rule_apply_deferred_pre_synaptic_spike(last_pre_synaptic_event.time, last_pre_synaptic_event.trace,
        last_post_synaptic_event.time, last_post_synaptic_event.trace, 
        deferred_update_state);
      // Go on to next pre-synaptic event
      pre_synaptic_event_find_next(pre_synaptic_event_history, delay, next_pre_synaptic_event_index, 
        &next_pre_synaptic_event_index, &next_pre_synaptic_event_time);
  }
  
    // Get final weight from learning rule
  uint32_t new_weight = stdp_trace_rule_get_final_weight(deferred_update_state, current_weight);
//  io_printf(IO_BUF,"update done.\n");
  // Return new weight
  return new_weight;
}

/*
static inline uint32_t plasticity_update_synapse_old(uint32_t last_update_time, uint32_t delay, uint32_t current_weight,
  const pre_synaptic_event_history_t *pre_synaptic_event_history, uint32_t post_synaptic_neuron_index)
  {
  plastic_runtime_log_info("\tPerforming deferred synapse update at time:%u - last_post_synaptic_event.time:%u, last_pre_synaptic_event.time:%u(delayed), next_post_synaptic_event_time:%u, next_pre_synaptic_event_time:%u(delayed)\n", 
    time, last_post_synaptic_event.time, last_pre_synaptic_event.time, next_post_synaptic_event_time, next_pre_synaptic_event_time);
  io_printf(IO_BUF,"new run at %d\n", last_update_time);
  
  while(next_post_synaptic_event_index != UINT32_MAX)
  {
  
  // While any pre or post-synaptic events remain
  while(next_pre_synaptic_event_index != UINT32_MAX || next_post_synaptic_event_index != UINT32_MAX)
  {
    // If next pre-synaptic event occurs before the next post-synaptic event
    // **NOTE** If next pre-synaptic event time's UINT32_MAX, this will never be true and due to loop conditions, both will never be UINT32_MAX!
    io_printf(IO_BUF,"next: post: %d, pre: %d, delta: %d\n", next_post_synaptic_event_time, next_pre_synaptic_event_time, next_post_synaptic_event_time - next_pre_synaptic_event_time);
    io_printf(IO_BUF,"last: post: %d, pre: %d, delta: %d\n", last_post_synaptic_event.time, last_pre_synaptic_event.time, last_post_synaptic_event.time - last_pre_synaptic_event.time);
    if(next_pre_synaptic_event_time <= next_post_synaptic_event_time )
    {
      plastic_runtime_log_info("\t\tApplying pre-synaptic event at time:%u\n", next_pre_synaptic_event_time);
      
      // Update last pre-synaptic event to point to new event we're processing, updating time to delayed version
      last_pre_synaptic_event.trace = pre_synaptic_event_history->traces[next_pre_synaptic_event_index];
      last_pre_synaptic_event.time = next_pre_synaptic_event_time;
      io_printf(IO_BUF, "post > pre: %d, %d\n",last_post_synaptic_event.time,last_pre_synaptic_event.time);
      
       // Apply pre-synaptic event to deferred update state
      deferred_update_state = stdp_trace_rule_apply_deferred_pre_synaptic_spike(last_pre_synaptic_event.time, last_pre_synaptic_event.trace,
        last_post_synaptic_event.time, last_post_synaptic_event.trace, 
        deferred_update_state);

      // Go onto next pre-synaptic event
      pre_synaptic_event_find_next(pre_synaptic_event_history, delay, next_pre_synaptic_event_index, 
        &next_pre_synaptic_event_index, &next_pre_synaptic_event_time);
    }
    // Otherwise, if the next post-synaptic event occurs before the next pre-synaptic event
    if(next_post_synaptic_event_time <= next_pre_synaptic_event_time && next_post_synaptic_event_time != UINT32_MAX)
    {
// no need for action here!
      plastic_runtime_log_info("\t\tApplying post-synaptic event at time:%u\n", next_post_synaptic_event_time);
      
      // Update last post-synaptic trace parameters
      last_post_synaptic_event.trace = post_synaptic_event_history_traces[post_synaptic_neuron_index][next_post_synaptic_event_index];
      last_post_synaptic_event.time = post_synaptic_event_history_times[post_synaptic_neuron_index][next_post_synaptic_event_index];
      
      io_printf(IO_BUF, "post <= pre: %d, %d\n",last_post_synaptic_event.time,last_pre_synaptic_event.time);
      // Apply pre-synaptic event to deferred update state
      deferred_update_state = stdp_trace_rule_apply_deferred_post_synaptic_spike(last_post_synaptic_event.time, last_post_synaptic_event.trace, 
        last_pre_synaptic_event.time, last_pre_synaptic_event.trace, 
        deferred_update_state);

//      io_printf(IO_BUF,"delay:%u",plasticity_region_data.t_delay);
      // Go onto next post-synaptic event
      post_synaptic_event_find_next(post_synaptic_neuron_index, next_post_synaptic_event_index, 
        &next_post_synaptic_event_index, &next_post_synaptic_event_time);
    }
    
  }

  // Get final weight from learning rule
  uint32_t new_weight = stdp_trace_rule_get_final_weight(deferred_update_state, current_weight);
//  io_printf(IO_BUF,"update done.\n");
  // Return new weight
  return new_weight;
}
*/
//---------------------------------------
// PACMAN memory region reading
//---------------------------------------
void initialise_plasticity_buffers()
{
  log_info("initialise_plasticity_buffers: starting");
  
  // Initialise memory for post-synaptic events
  initialise_post_synaptic_event_buffers();
  
  log_info("initialise_plasticity_buffers: completed successfully");
}

//---------------------------------------
// Synaptic row plastic-region implementation
//---------------------------------------
static inline weight_t* plastic_weights(address_t plastic)
{
  const uint32_t pre_synaptic_event_history_size_words = sizeof(pre_synaptic_event_history_t) / sizeof(uint32_t);
  COMPILE_TIME_ASSERT(pre_synaptic_event_history_size_words * sizeof(uint32_t) == sizeof(pre_synaptic_event_history_t), pre_synaptic_event_history_t_should_be_word_padded)

  return (weight_t*)(&plastic[pre_synaptic_event_history_size_words]); 
}
//---------------------------------------
static inline pre_synaptic_event_history_t *plastic_event_history(address_t plastic)
{
  return (pre_synaptic_event_history_t*)(&plastic[0]);
}
//---------------------------------------
void plasticity_process_teaching_synaptic_event(uint32_t neuron_index)
{
#ifdef DEBUG
  plastic_runtime_log_enabled = false;
#endif  // DEBUG

  plastic_runtime_log_info("Processing post-synaptic event at time:%u\n", time);
  
  // Get last post-synaptic event. If there are none, initialise primary trace to initial value and last_spike_time to zero
  post_synaptic_event_t last_post_synaptic_event = post_synaptic_event_last(neuron_index);

  // Get new event from learning rule
  post_synaptic_trace_entry_t new_post_synaptic_trace_entry = stdp_trace_rule_add_post_synaptic_spike(time, last_post_synaptic_event.time, last_post_synaptic_event.trace);

  // Append primary trace value to history
  post_synaptic_event_add(neuron_index, time, new_post_synaptic_trace_entry);
}

//---------------------------------------
void plasticity_process_post_synaptic_event(uint32_t neuron_index)
{
    use(neuron_index);
}

//---------------------------------------
void process_plastic_synapses (address_t plastic, address_t fixed, ring_entry_t *ring_buffer)
{
#ifdef DEBUG
  plastic_runtime_log_enabled = false;
#endif  // DEBUG
//  io_printf(IO_BUF,"plastic: %08x, fixed: %08x\n", plastic, fixed);
  // Extract seperate arrays of weights (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  weight_t *weights = plastic_weights(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);

  // Get event history from synaptic row
  pre_synaptic_event_history_t *event_history = plastic_event_history(plastic);

  // Get last pre-synaptic event from event history
  // **NOTE** at this level we don't care about individual synaptic delays
  pre_synaptic_event_t last_pre_synaptic_event = pre_synaptic_event_last(event_history);

  // Loop through plastic synapses
  for ( ; plastic_synapse > 0; plastic_synapse--) 
  {
    // Get next weight and control word (autoincrementing control word)
    uint32_t weight = *weights;
    uint32_t control_word = *control_words++;

     // Extract control-word components
    // **NOTE** cunningly, control word is just the same as lower 
    // 16-bits of 32-bit fixed synapse so same functions can be used
    uint32_t delay = sparse_delay(control_word);
    uint32_t index = sparse_type_index(control_word);

    // Update synapse weight
    uint32_t updated_weight = plasticity_update_synapse(last_pre_synaptic_event.time, delay, weight ,event_history, index);
//    io_printf(IO_BUF,"update n%d: %d -> %d\n",index,weight,updated_weight);
    // Convert into ring buffer offset
    uint32_t offset = offset_sparse(delay + time, index);

    // Add weight to ring-buffer entry
    // **NOTE** Dave suspects that this could be a potential location for overflow
    ring_buffer[offset] += weight;

    // Write back updated weight to plastic region
    // **THINK** is this actually the right operator-mess to store and autoincrement
    *weights++ = updated_weight;
  }

  plastic_runtime_log_info("Processing pre-synaptic event at time:%u\n", time);
// I think we don't need that for our SinAdd rule!
  pre_synaptic_trace_entry_t new_pre_synaptic_trace_entry = stdp_trace_rule_add_pre_synaptic_spike(time, last_pre_synaptic_event.time, last_pre_synaptic_event.trace);

  // Add pre-synaptic event to history
  pre_synaptic_event_add(event_history, time, new_pre_synaptic_trace_entry);
}
//---------------------------------------
#ifdef DEBUG
void print_plastic_synapses(address_t plastic, address_t fixed)
{
  // Extract seperate arrays of weights (from plastic region),
  // Control words (from fixed region) and number of plastic synapses
  const weight_t *weights = plastic_weights(plastic);
  const control_t *control_words = plastic_controls(fixed);
  size_t plastic_synapse  = num_plastic_controls(fixed);
  const pre_synaptic_event_history_t *event_history = plastic_event_history(plastic);

  io_printf (IO_BUF,"Plastic region %u synapses pre-synaptic event buffer start index:%u count:%u:\n", plastic_synapse, event_history->start_index, event_history->count);

  // Loop through plastic synapses
  for (uint32_t i = 0; i < plastic_synapse; i++) 
  {
    // Get next weight and control word (autoincrementing control word)
    uint32_t weight = *weights++;
    uint32_t control_word = *control_words++;

    io_printf (IO_BUF, "%08x [%3d: (w: %5u (=", control_word, i, weight);
//    print_weight (weight);
    io_printf (IO_BUF, "pA) d: %2u, %c, n = %3u)] - {%08x %08x}\n",
      sparse_delay(control_word),
      (sparse_type(control_word)==0)? 'X': 'I',
      sparse_index(control_word),
      SYNAPSE_DELAY_MASK,
      SYNAPSE_TYPE_INDEX_BITS
    );
  }
}
#endif  // DEBUG
