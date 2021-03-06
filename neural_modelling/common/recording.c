#include "common-impl.h"

// Standard includes
#include <string.h>

//---------------------------------------
// Structures
//---------------------------------------
typedef struct recording_channel_t
{
  address_t counter;
  uint8_t *start;
  uint8_t *current;
  uint8_t *end;
} recording_channel_t;

//---------------------------------------
// Globals
//---------------------------------------
static recording_channel_t g_recording_channels[e_recording_channel_max];

//---------------------------------------
// Private API
//---------------------------------------
static inline bool recording_channel_in_use(recording_channel_e channel)
{
  return (g_recording_channels[channel].start != NULL &&  g_recording_channels[channel].end != NULL);
}

//---------------------------------------
// Public API
//---------------------------------------
bool recording_data_filled(address_t output_region, uint32_t flags, recording_channel_e channel, uint32_t size_bytes)
{
  use(flags);
  
  if(recording_channel_in_use(channel))
  {
    log_info("Recording channel %u already configured", channel);
    
    // CHANNEL already initialized
    return false;
  }
  else
  {
    recording_channel_t *recording_channel = &g_recording_channels[channel];

    // Cache pointer to output counter in recording channel and set it to 0
    recording_channel->counter = &output_region[0];
    *recording_channel->counter = 0;

    // Calculate pointers to the start, current position and end of this memory block
    recording_channel->start = recording_channel->current = (uint8_t*)&output_region[1];
    recording_channel->end = recording_channel->start + size_bytes;
    
    log_info("Recording channel %u configured to use %u byte memory block starting at %08x", channel, size_bytes, recording_channel->start);
    return true;
  }
}
//---------------------------------------
bool recording_record(recording_channel_e channel, void *data, uint32_t size_bytes)
{
  if(recording_channel_in_use(channel))
  {
    recording_channel_t *recording_channel = &g_recording_channels[channel];

    // If there's space to record
    if(recording_channel->current < (recording_channel->end - size_bytes))
    {
      // Copy data into recording channel
      memcpy(recording_channel->current, data, size_bytes);
      
      // Update current pointer
      recording_channel->current += size_bytes;
      return true;
    }
    else
    {
      log_info("ERROR: recording channel %u out of space", channel);
      return false;
    }
  }
  else
  {
    log_info("ERROR: recording channel %u not in use", channel);
   
    return false;
  }


}
//---------------------------------------
void recording_finalise()
{
  log_info("Finalising recording channels");

  // Loop through channels
  for(uint32_t channel = 0; channel < e_recording_channel_max; channel++)
  {
    // If this channel's in use
    if(recording_channel_in_use(channel))
    {
      recording_channel_t *recording_channel = &g_recording_channels[channel];

      // Calculate the number of bytes that have been written and write back to SDRAM counter
      uint32_t num_bytes_written = recording_channel->current - recording_channel->start;
      log_info("\tFinalising channel %u - %x bytes of data starting at %08x", channel, num_bytes_written + sizeof(uint32_t), recording_channel->counter);
      *recording_channel->counter = num_bytes_written;
    }	
  }
}
