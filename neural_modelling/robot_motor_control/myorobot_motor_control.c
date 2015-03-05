#include "../common/common-impl.h"
#include <string.h>
#include <stdfix.h>
#include "../common/simulate.h"

#define REAL accum
#define REAL_CONST( x ) x##k

#define DEBUG 1
/*

#include <math.h>
#include <stdfix.h>

static REAL machine_timestep = REAL_CONST( 1.0 );  // in msecs
static REAL decay_factor = REAL_CONST(0.0);

// setup function which needs to be called in main program before any neuron code executes
// minimum 100, then in 100 steps...  
void provide_machine_timestep( uint16_t microsecs ){

	const double	time_step_multiplier = 0.00100;
    const double    tau_time_constant = 0.060 * 1e6; // from edlut's compute_output_activity(), in units of microseconds

	machine_timestep = (REAL)( microsecs * time_step_multiplier );
	decay_factor = (REAL) exp( - microsecs / tau_time_constant );
}
*/

// Counters
#define N_COUNTERS       2
#define	PWM_AGONIST      0x00
#define PWM_ANTAGONIST	 0x01
#define NEURON_ID_MASK   0x1FF //512 neurons is enough!
#define DUAL_SET_MOTOR_ID 58 << 4
#define SINGLE_SET_MOTOR_ID 57 << 4


#define DEFAULTIOKEY 0xFEFFF800 
#define MYOKEY   ( DEFAULTIOKEY | 12<<7 )
#define MYOSENSORKEY ( MYOKEY | ((1<<3) << 2) ) //fefffe20
#define MYOSPINDLEKEY ( MYOKEY | ((0<<3) << 2) | 1 ) //fefffe01
#define MYOSETPOINTKEY ( MYOKEY | ((1<<5) << 2) ) //fefffe80

#define SENSORRANGE 1664  // CHECK: are these valid 
#define SENSOROFFSET 255    // for all angle sensors?
#define MIDPOINT ( SENSORRANGE / 2 ) - SENSOROFFSET

#define SENSOR_TO_UINT32SCALE  ( UINT32_MAX / SENSORRANGE )

// Globals
static uint32_t time;
static uint32_t counter;
static REAL output_var;

static int32_t sensor_vals[8] = {0,0,0,0,0,0,0,0};
static int32_t setpoint_vals[8] = {0,0,0,0,0,0,0,0};
static int32_t spindle_vals[8] = {0,0,0,0,0,0,0,0};// in principle we have 2x as many spindles as there are sensors!

static uint32_t iokey;
static REAL output_scale;
static uint32_t sample_time;
static REAL decay_factor;
static REAL kernel_amplitude;
static int threshold; // in absolute, myorob input terms
static uint32_t n_neurons;
static REAL sensor_scale;

static uint32_t time_rand_scale;

#define SAFEMAX 800 //play it safe, for the moment! we're allowed to go up to 4000

static inline void send_motorcmd(REAL pwm_value) {
    if (pwm_value < -SAFEMAX) pwm_value = -SAFEMAX;
	else if (pwm_value > SAFEMAX) pwm_value = SAFEMAX;
    while (!spin1_send_mc_packet(iokey, (int32_t) pwm_value, WITH_PAYLOAD)) {
		spin1_delay_us(1);
	    }	
	}

void own_spike_callback (uint key, uint payload) {
  use(payload);
  // Process the incoming spikes
  uint32_t nid;
  nid = (key & NEURON_ID_MASK);

    if (nid < n_neurons) {
      log_info("received key %d, so I am increasing counter %d",key,nid);
      counter++;
    } else {
       log_info("Received spike from unknown neuron %d", nid);
    }
  
}

// Callbacks
void timer_callback (uint unused0, uint unused1)
{
  use(unused0);
  use(unused1);
  time++;
    
  if ((time % sample_time) == sample_time - 1 )
  {
    // decay the output
	output_var *= decay_factor;
	output_var += ( counter * kernel_amplitude );
	
	// Move ya!
	send_motorcmd(output_var * output_scale);

	// Reset the counters
	counter = 0;
  }

  if (time == 0)
  {
#ifdef DEBUG
	log_info("External Key = %08x, scaler = %k, sample_time = %d, decay_factor = %k, kernel_amplitude = %k, threshold = %d",
				iokey, output_scale, sample_time, decay_factor, kernel_amplitude, threshold);
	log_info("Myosetpointkey: %08x, Myosensorkey: %08x", MYOSETPOINTKEY, MYOSENSORKEY);
#endif

  }

  if (simulation_ticks != UINT32_MAX && time == simulation_ticks - 10 ) // + timer_period)
  {
    log_info("Simulation complete.\n");
    spin1_callback_off (MCPL_PACKET_RECEIVED);
    spin1_callback_off (MC_PACKET_RECEIVED);
    spin1_callback_off (TIMER_TICK);

    spin1_exit(0);
    return;
  }

}

bool robot_source_data_filled(address_t base_address) {
    address_t region_address = region_start(2, base_address);
	log_info("Reading data from 0x%.8x", region_address);
	iokey = region_address[0];
	memcpy(&output_scale,&region_address[1],4);
	sample_time = region_address[2];
	memcpy(&decay_factor,&region_address[3],4);
	memcpy(&kernel_amplitude,&region_address[4],4);
	threshold = region_address[5];
	n_neurons = region_address[6];
	
	iokey = iokey | SINGLE_SET_MOTOR_ID;
	counter = 0;
	output_var = 0;
	
	return (true);
}

bool system_load_dtcm(void) {

  // Get the address this core's DTCM data starts at from SRAM
  address_t address = system_load_sram();

  uint32_t version;
  uint32_t flags   = 0;
  if(!system_header_filled (address, &version, flags))
  {
	return (false);
  }
  if (!robot_source_data_filled(address)) {
	return (false);
  }

  return (true);
}

// Entry point
void c_main (void)
{
  // Configure system
  io_printf(IO_BUF, "Initializing robot code\n");
  system_load_dtcm();
 
  // Configure lead app-specific stuff
  if(leadAp)
  {
    system_lead_app_configured();
  }

//  spin1_callback_on (MCPL_PACKET_RECEIVED, incoming_data_callback, 3);
//
//  log_info("MCPL callbacks requested.");
  
  // Register callbacks
  spin1_callback_on (MC_PACKET_RECEIVED, own_spike_callback, 1);
  
  log_info("MC callback requested.");

  // Set timer_callback
  spin1_set_timer_tick(timer_period);
  log_info("time is ticking every %d!",timer_period);

  spin1_callback_on (TIMER_TICK, timer_callback, 0);

  log_info("timer tick callback requested.");

  
  log_info("Starting");

  // Start the time at "-1" so that the first tick will be 0
  time = UINT32_MAX;
  system_runs_to_completion();
}
