#include "../common/spike_source_impl.h"

#include "../../common/simulate.h"
#include <stdfix.h>
#include "../../common/stdfix-exp.h"
#include <math.h>
 
#include <string.h>

typedef struct slow_spike_source_t
{
  uint32_t neuron_id;
  uint32_t start_ticks;
  uint32_t end_ticks;
  
  accum mean_isi_ticks;
  accum time_to_spike_ticks;
} slow_spike_source_t;

typedef struct fast_spike_source_t
{
  uint32_t neuron_id;
  uint32_t start_ticks;
  uint32_t end_ticks;
  
  unsigned long fract exp_minus_lambda;
} fast_spike_source_t;

// Globals
static uint32_t listenkey;
static slow_spike_source_t *slow_spike_source_array = NULL;
static fast_spike_source_t *fast_spike_source_array = NULL;
static uint32_t num_slow_spike_sources = 0;
static uint32_t num_fast_spike_sources = 0;
static mars_kiss64_seed_t spike_source_seed;
static uint32_t ticks = 0;
static uint32_t final_tick = 0;

#define REAL accum
static REAL gauss_width = 20.;
static REAL recip_max_rate = 0.; // 1 / (maximal rate) in units of ticks
static REAL recip_min_rate = 0.;       // 1 / (minimal rate) in units of ticks
static REAL *gauss_lut = NULL; 
#define LUTSIZE 256
static REAL sensorvalue_to_spikerate;
static REAL sensorvalue_to_lutidx;
static REAL sensorvalue_to_neuidx;
static REAL neuidx_to_sensorvalue;
static REAL true_luthwhm = LUTSIZE / 3.0;

#define DEFAULTIOKEY 0xFEFFF800 
#define MYOKEY   ( DEFAULTIOKEY | 12<<7 )
#define MYOSENSORKEY ( MYOKEY | ((1<<3) << 2) )
#define MYOSETPOINTKEY ( MYOKEY | ((1<<5) << 2) )

static int32_t sensormax = + 1444;
static int32_t sensormin = - 256;
static int32_t sensorrange = 1700;
static uint32_t inputshift = 0; 
static uint32_t bunchsize = 32;


static inline accum slow_spike_source_get_time_to_spike( accum mean_isi_ticks )
{
  return exponential_dist_variate( mars_kiss64_seed, spike_source_seed ) * mean_isi_ticks;
}

static inline uint32_t fast_spike_source_get_num_spikes( unsigned long fract exp_minus_lambda )
{
  return poisson_dist_variate_exp_minus_lambda( mars_kiss64_seed, spike_source_seed, exp_minus_lambda );
}

// fills the previously allocated gauss_lut
// the final index corresponds to an argument of true_lutcut
void fill_gauss_lut(void) {
  unsigned fract step = (REAL) 1.17741 * 3.0 / LUTSIZE; // = HWHM / ( LUTSIZE / 3 )
  unsigned accum arg = 0.0;                             // so lut finishes at 0.002
  uint i;
  
  for ( i = 0; i < LUTSIZE; i++) {
    arg = step*i;
    gauss_lut[i] = recip_max_rate * expk( (arg*arg)*0.5k );
    if (gauss_lut[i] > recip_min_rate) gauss_lut[i] = recip_min_rate;
    // recip_min_rate is a slight offset to our gaussian
//    log_info("lut(%d, %k, %k) = %k",i, arg, recip_max_rate, gauss_lut[i]);
  }
  true_luthwhm = LUTSIZE / 3.0; // this is the (broken) index at which to find 0.5;
  sensorvalue_to_lutidx = true_luthwhm / gauss_width; //(gauss_width*gauss_width);
}



static inline accum lu_gauss(accum value) {
     uint lowidx, lowidx_plus_one;
     value = value * sensorvalue_to_lutidx; 
     if (value < 0) value = - value;
            
     lowidx = (uint) value; // let's interpolate from the lut
     lowidx_plus_one = lowidx + 1;
//     log_info("lowidx: %d, value: %k", lowidx, value);
     if ( lowidx_plus_one >= LUTSIZE ) return recip_min_rate; // outside of range
   
     value = gauss_lut[lowidx] * (REAL) (1.0k - ( value - lowidx) ) \
           + gauss_lut[lowidx_plus_one] * (REAL) (1.0k - (lowidx_plus_one - value) );
     return value; 
}


void incoming_update_callback(uint key, uint payload) {
// would be a much better idea to buffer incoming data and update periodically
    accum value;
//    uint joint_index;
    int neuid = 0;
    static int lasttick = 0;
    log_info("got packet, %08x.%08x",key,payload);
    payload = payload >> inputshift;
    if ( ticks - lasttick < 10) return; // limit updates to 100Hz
//    log_info("tick %d: received value %d, updating firing rate.",ticks, payload);
//    joint_index = key & 0x0000000F;
    // POSSIBLE PERFORMANCE IMPROVEMENT:
    // break if lu_gauss hits 0 (after hitting > 0)
//    if ( ( key & 0xFFFFFFF0 ) == MYOSENSORKEY) //this should be guaranteed by routing rule!
    else { 
#ifndef RBF
        value = (REAL) sensorrange/(payload - sensormin + 1) * recip_max_rate;
        log_info("new rate value: %k", value);
#endif
        for (uint i=0; i<num_slow_spike_sources; i++) {
            slow_spike_source_t *slow_spike_source = &slow_spike_source_array[i];
            neuid = slow_spike_source->neuron_id;
#ifdef RBF
            // distance of this neuron to setpoint (in sensor units)
            value = (REAL) ( (int32_t) ( neuid * neuidx_to_sensorvalue ) - ( payload - sensormin ) );            
            value = lu_gauss(value);
#endif

#ifdef POISSON
            if (value < slow_spike_source->mean_isi_ticks) {
              slow_spike_source->time_to_spike_ticks = slow_spike_source_get_time_to_spike(value);
            }
#else
//          log_info("neuid: %d, value: %k",neuid,value);

            if (value < slow_spike_source->time_to_spike_ticks) { // update time_to only if we want to go faster.
                slow_spike_source->time_to_spike_ticks = value; // the deterministic variant
            }
#endif
            slow_spike_source->mean_isi_ticks = value; // Update time to spike buffer

        }
    }
    lasttick = ticks;
    
    if ( ticks > final_tick ) {
        spin1_callback_off (MCPL_PACKET_RECEIVED );
        log_info("MCPL callbacks off.");
    }

}

bool spike_source_poisson_parameters_filled(address_t address, uint32_t flags)
{
  use(flags);
  
  log_info("spike_source_poisson_parameters_filled: starting");
#ifdef RBF
  log_info("RBF active");
#endif
#ifdef POISSON
  log_info("Poisson active");
#endif
  
  // changed from above for new file format 13-1-2014
  key   = address[0];
  log_info("\tkey = %08x, (x: %u, y: %u) proc: %u",
           key, key_x (key), key_y (key), key_p (key));
  listenkey = address[1];
           
  sensormin = (int32_t) address[2];
  sensormax = (int32_t) address[3];
  
  memcpy(&recip_max_rate, &address[4], 4);
  memcpy(&recip_min_rate, &address[5], 4);
  gauss_width = (int32_t) address[6];
//  memcpy(&gauss_width, &address[6], 4);
  bunchsize = (uint32_t) address[7];

  while ( sensormin <= -32767 || sensormax >= 32767 ) {
    sensormin = sensormin >> 1;
    sensormax = sensormax >> 1;
    gauss_width = gauss_width >> 1;
    inputshift++;
    }

  sensorrange = sensormax - sensormin;
  
  uint32_t seed_size = sizeof(mars_kiss64_seed_t) / sizeof(uint32_t);
  memcpy( spike_source_seed, &address[8], seed_size * sizeof(uint32_t));
  validate_mars_kiss64_seed( spike_source_seed);

  log_info("\tSeed (%u) = %u %u %u %u", seed_size, spike_source_seed[0], spike_source_seed[1], spike_source_seed[2], spike_source_seed[3]);

  num_slow_spike_sources = address[8 + seed_size];
  num_fast_spike_sources = address[9 + seed_size];
  num_spike_sources = num_slow_spike_sources + num_fast_spike_sources;
  log_info("\tslow spike sources = %u, fast spike sources = %u, spike sources = %u", num_slow_spike_sources, num_fast_spike_sources, num_spike_sources);
  
  
  // Allocate DTCM for array of slow spike sources and copy block of data
  slow_spike_source_array = (slow_spike_source_t*)spin1_malloc( num_slow_spike_sources * sizeof(slow_spike_source_t) );
  memcpy( slow_spike_source_array, &address[10 + seed_size], num_slow_spike_sources * sizeof(slow_spike_source_t) );
  
  // Loop through slow spike sources and initialise 1st time to spike
  for(index_t s = 0; s < num_slow_spike_sources; s++)
  {
    slow_spike_source_array[s].time_to_spike_ticks = slow_spike_source_get_time_to_spike(slow_spike_source_array[s].mean_isi_ticks);
    if ( final_tick < slow_spike_source_array[s].end_ticks ) final_tick = slow_spike_source_array[s].end_ticks;
  }
  final_tick = final_tick >= 50? final_tick-50: 0;
  
  // Allocate DTCM for array of fast spike sources and copy block of data
  uint32_t fast_spike_source_offset = 9 + seed_size + (num_slow_spike_sources * (sizeof(slow_spike_source_t) / sizeof(uint32_t)));
  fast_spike_source_array = (fast_spike_source_t*)spin1_malloc( num_fast_spike_sources * sizeof(fast_spike_source_t) );
  memcpy( fast_spike_source_array, &address[fast_spike_source_offset], num_fast_spike_sources * sizeof(fast_spike_source_t) );

#ifdef DEBUG
  for (index_t s = 0; s < num_fast_spike_sources; s++)
  {
	log_info("\t\tNeuron id %d, exp(-k) = %0.8x", fast_spike_source_array[s].neuron_id, fast_spike_source_array[s].exp_minus_lambda);
  }
#endif // DEBUG
  log_info("Hello!");
    // Allocate DTCM for gaussian look-up-table and fill.
//#ifdef RBF
  gauss_lut = (accum *) spin1_malloc( LUTSIZE * sizeof(REAL) );
//#endif
  sensorvalue_to_neuidx = (REAL) (bunchsize - 1) / sensorrange;
  sensorvalue_to_spikerate = recip_min_rate / (REAL) sensorrange;
  neuidx_to_sensorvalue = (REAL) sensorrange / (bunchsize-1); // CHANGE THIS!
//#ifdef RBF
  fill_gauss_lut(); //not necessary for non-RBF
//#endif

  log_info("sensor_to_neu: %k, neu_to_sens: %k, sensor_to_lut: %k, sensor_to_spike: %k", \
            sensorvalue_to_neuidx,neuidx_to_sensorvalue,sensorvalue_to_lutidx,sensorvalue_to_spikerate);
  log_info("sensor_min: %d, sensor_max: %d, sensor_range: %d", \
            sensormin, sensormax, sensorrange);
  log_info("reciprocal max rate: %k, rec. min rate: %k, width: %k", recip_max_rate, recip_min_rate, gauss_width);

  log_info("spike_source_poisson_parameters_filled: completed successfully");
  return (true);
}

bool spike_source_data_filled(address_t base_address, uint32_t flags, uint32_t spike_history_recording_region_size, 
                              uint32_t neuron_potentials_recording_region_size, uint32_t neuron_gsyns_recording_region_size)
{
  use(neuron_potentials_recording_region_size);
  use(neuron_gsyns_recording_region_size);
  
  log_info("spike_source_data_filled: starting");
  
  if (!spike_source_poisson_parameters_filled (region_start(2, base_address), flags))  // modified for use with simon's data blob
    return (false);
  
  // Setup output recording regions
  if (!recording_data_filled (region_start(3, base_address), flags, e_recording_channel_spike_history, spike_history_recording_region_size))
    return (false);
 
  log_info("spike_source_data_filled: completed successfully");
  
  spin1_callback_off (MCPL_PACKET_RECEIVED);

  log_info("Told router to send myo-sensor data my way.");

  return true;
}

void spike_source_dma_callback(uint unused, uint tag)
{
  use(unused);
  use(tag);
}

void spike_source_generate(uint32_t tick)
{
  slow_spike_source_t *slow_spike_source = &slow_spike_source_array[0];
  
  if ( tick == slow_spike_source->start_ticks + 1) {
    uint e = rtr_alloc (1); //Rework in concordance to myorobot_motor_control.c
  if (e == 0)
      rt_error (RTE_ABORT);
  rtr_mc_set (e,
        listenkey
         , // route some data to me!
        0xFFFFFFFFF , 
        (1 << (spin1_get_core_id() + 6)) 
        );  

    spin1_callback_on (MCPL_PACKET_RECEIVED, incoming_update_callback, 3);
    log_info("MCPL callbacks requested for data input.");
  }
  if ( tick > slow_spike_source->end_ticks - 1 ) {
    spin1_callback_off (MCPL_PACKET_RECEIVED );
    log_info("MCPL callbacks off.");
  }
  ticks = tick;

  // Loop through slow spike sources
  for(index_t s = 0; s < num_slow_spike_sources; s++)
  {
    // If this spike source is active this tick
    slow_spike_source_t *slow_spike_source = &slow_spike_source_array[s];
    if(tick >= slow_spike_source->start_ticks && tick < slow_spike_source->end_ticks)
    {
      // If this spike source should spike now
      if(slow_spike_source->time_to_spike_ticks <= 0.0k)
      {
        // Write spike to out spikes
        out_spike(slow_spike_source->neuron_id);
        
        // Send package
        spin1_send_mc_packet(key | slow_spike_source->neuron_id, NULL, NO_PAYLOAD);
        
#ifdef SPIKE_DEBUG
          io_printf(IO_BUF, "Sending spike packet %x at %d\n",
        		  key | slow_spike_source->neuron_id, tick);
#endif // SPIKE_DEBUG

        // Update time to spike
#ifdef POISSON
        slow_spike_source->time_to_spike_ticks += slow_spike_source_get_time_to_spike(slow_spike_source->mean_isi_ticks);
#else
        slow_spike_source->time_to_spike_ticks += slow_spike_source->mean_isi_ticks;
#endif
      }
      
      // Subtract tick
      slow_spike_source->time_to_spike_ticks -= 1.0k;
    }
  }
  
  // Loop through fast spike sources
  for(index_t f = 0; f < num_fast_spike_sources; f++)
  {
    // If this spike source is active this tick
    fast_spike_source_t *fast_spike_source = &fast_spike_source_array[f];
    if(tick >= fast_spike_source->start_ticks && tick < fast_spike_source->end_ticks)
    {
      // Get number of spikes to send this tick
      uint32_t num_spikes = fast_spike_source_get_num_spikes(fast_spike_source->exp_minus_lambda);
      log_info("Generating %d spikes", num_spikes);
      
      // If there are any
      if(num_spikes > 0)
      {
        // Write spike to out spikes
        out_spike(fast_spike_source->neuron_id);
        
        // Send spikes
        const uint32_t spike_key = key | fast_spike_source->neuron_id;
        for(uint32_t s = 0; s < num_spikes; s++)
        {
#ifdef SPIKE_DEBUG
          io_printf(IO_BUF, "Sending spike packet %x at %d\n", spike_key, tick);
#endif // SPIKE_DEBUG
          while(!spin1_send_mc_packet(spike_key, NULL, NO_PAYLOAD)) {
              spin1_delay_us(1);
          }
        }
      }
    }
  }
}

