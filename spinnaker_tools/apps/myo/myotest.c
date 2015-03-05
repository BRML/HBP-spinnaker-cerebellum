/*
 *  Project: 	 GRIDMAP
 *  File: 	 network.c
 *  Version: 	 0.02
 *  Created on:  January 16th 2014
 *  Modified on: April 4th 2014
 *  Description: implementation of a network on SpiNNaker
 * 
 *  Implementation:
 *  At every tick of the timer all neurons are updated.
 *  Every time a neuron fires a multicast packet is sent.
 *  Once the packet is received, a DMA transfer is necessary to retrieve
 *  the synaptic weights of the neuron that fired.
 *  
 *  Author:  	Marcello Mulas (marcello.mulas@tum.de)
 */

#include "../../../neural_modelling/common/common-impl.h"
#include "spin1_api.h"
#include <stdfix.h>

#define REAL accum
#define REAL_CONST( x ) x##k
//#include "spinn_io.h"

//#include <stdfix.h>  // for fixed point arithmetic
//#include <math.h>      // for floating point arithmetic

/*
#define EAST        (1 << 0)
#define NORTH_EAST  (1 << 1)
#define NORTH       (1 << 2)
#define WEST        (1 << 3)
#define SOUTH_WEST  (1 << 4)
#define SOUTH       (1 << 5)
*/
#define EAST        0x1
#define NORTH_EAST  0x2
#define NORTH       0x4
#define WEST        0x8
#define SOUTH_WEST  0x10
#define SOUTH       0x20


#define CHIP_TO_NORTH(chip)     (chip + 1)
#define CHIP_TO_SOUTH(chip)     (chip - 1)
#define CHIP_TO_EAST(chip)      (chip + (1 << 8))
#define CHIP_TO_WEST(chip)      (chip - (1 << 8))


#define CORE(n)     (1 << (n + 6))
#define ALL_DIRECTIONS  0x003FFFFF
//#define ALL_DIRECTIONS  0xFFFFFFFF



#define SIMULATION_DURATION_SEC  	50
#define TIME_STEP_MICROSEC              1000
#define N_NEURONS 		        100


#define TIMER_PRIORITY 			1
#define MC_PACKET_EVENT_PRIORITY 	0
#define DMA_TRANSFER_DONE_PRIORITY 	0

#define SEC_TO_MICROSEC         	1000000

#define N_XCHIPS 2
#define N_YCHIPS 2

#define IOMASK 0x11100000

#define	PWM_AGONIST      0x00
#define PWM_ANTAGONIST	 0x01
#define NEURON_ID_MASK   0x0FF //256 neurons is enough!
#define DUAL_SET_MOTOR_ID 58 << 4


#define DEFAULTIOKEY 0xFEFFF800 
#define MYOKEY   ( DEFAULTIOKEY | 12<<7 )
#define MYOSENSORKEY ( MYOKEY | ((1<<3) << 2) )
#define MYOSETPOINTKEY ( MYOKEY | ((1<<5) << 2) )
#define MYOMOTORKEY ( MYOKEY | ((0<<3) << 2 ) )

#define SENSORRANGE 1664  // CHECK: are these valid 
#define SENSOROFFSET 255    // for all angle sensors?
#define MIDPOINT ( SENSORRANGE / 2 ) - SENSOROFFSET

#define SENSOR_TO_UINT32SCALE  ( UINT32_MAX / SENSORRANGE )

static uint32_t time;
static uint32_t *counters;
static REAL *output_vars;

static uint32_t sensor_vals[8] = {0,0,0,0,0,0,0,0};
static uint32_t setpoint_vals[8] = {0,0,0,0,0,0,0,0};

static uint32_t iokey = 0x11100000;
static uint32_t intkey;
static REAL output_scale;
static uint32_t sample_time;
static REAL decay_factor;
static REAL kernel_amplitude;
static int threshold; // in absolute, myorob input terms
static uint32_t n_neurons;
static REAL sensor_scale;




uint chipID;
uint coreID;
uint spikeNumber;

// declare application types and variables

uint nIterations = 0;


/**************************
 *	 FUNCTIONS
 **************************/
static inline void send_agoantago(uint8_t motor_index, int agocount, int antagocount) {
	uint32_t direction_key = motor_index | iokey | DUAL_SET_MOTOR_ID;
	uint32_t payload = (int16_t) agocount;
	payload = payload << 16 | (int16_t) antagocount;
	while (!spin1_send_mc_packet(direction_key, payload, WITH_PAYLOAD)) {
		spin1_delay_us(1);
	}
	setpoint_vals[motor_index] = agocount;
	setpoint_vals[motor_index+1] = antagocount;
}

static inline void do_motion(uint32_t direction_index, uint32_t opposite_index) {
  int agonist_count = (int) ( output_vars[direction_index] * output_scale);
  int antagonist_count = (int) ( output_vars[opposite_index] * output_scale);
  log_info("agonist = %d, antagonist = %d, threshold = %u",
		  agonist_count, antagonist_count, threshold);
  if ((agonist_count >= threshold) || (antagonist_count >= threshold))
  {
	send_agoantago(direction_index, agonist_count, antagonist_count);
  }
}
/**************************
 *        CALLBACKS@00000100
 **************************/

uint ifd2key(uint id, uint format, uint dim) {
    uint ret;
    
    ret = dim & 0x7;   
    ret |= (format & 0x1) << 3;
    ret |= (id & 0x7F) << (1+3);
//    io_printf(IO_STD, "%x, %x, %x => %x", id, format, dim, ret);
    return ret|IOMASK;
} 
    
#define MAXPWM 600
void timer_callback(uint key, uint payload)
{    
    if (nIterations == 0) { 
      while (!spin1_send_mc_packet(0x7f1| IOMASK, 4, WITH_PAYLOAD)) {
		    spin1_delay_us(50);
	    }
      while (!spin1_send_mc_packet(0x0380| IOMASK, 0x01200110, WITH_PAYLOAD)) {
		    spin1_delay_us(50);
	    } 
      while (!spin1_send_mc_packet(0x0381| IOMASK, 0x01250115, WITH_PAYLOAD)) {
		    spin1_delay_us(50);
	    }
    }
    if (nIterations == 2) {
      // enable sensor
      while (!spin1_send_mc_packet(IOMASK|60<<4 | 0, 0x0000050, WITH_PAYLOAD)) {
		    spin1_delay_us(50);
        }
    }
    if (nIterations == 4) {
      while (!spin1_send_mc_packet(IOMASK|59<<4 | 0, 0x0000002, WITH_PAYLOAD)) {
		    spin1_delay_us(50);
        }
    }
    if (nIterations == 6) {
          while (!spin1_send_mc_packet(IOMASK|59<<4 | 1, 0x0000002, WITH_PAYLOAD)) {
		    spin1_delay_us(50);
        }
    }
    if (nIterations == 10) {
        send_agoantago(0,MAXPWM,MAXPWM);
    }

    if (nIterations == 4000) {
        send_agoantago(0,000,MAXPWM);
    }
    
    if (nIterations == 4200) {
        send_agoantago(0,MAXPWM,MAXPWM);
    }

    if (nIterations == 6000) {
        send_agoantago(0,MAXPWM,0);
    }
    if (nIterations == 6200) {
        send_agoantago(0,MAXPWM,MAXPWM);
    }

    if (nIterations > 8000-MAXPWM && nIterations % 10) {
      int value = 8000-nIterations;
      send_agoantago(0,value,value);
      }
    if (nIterations == 8000) {
      // relax
      send_agoantago(0,0,0);
        //deregister sensor
      while (!spin1_send_mc_packet(IOMASK|60<<4 | 0, 0x0000000, WITH_PAYLOAD)) {
		spin1_delay_us(100);
		}
        spin1_exit(0);
    }
//    io_printf(IO_STD,"iteration: %d\n",nIterations);
    io_printf(IO_BUF,"%d\t%d\t%d\t%d\t%d\t%d\n", nIterations, sensor_vals[0],setpoint_vals[0],setpoint_vals[1],sensor_vals[1],sensor_vals[2]);

    nIterations++;
    //updateNeurons();
}


void multiCastPacketReceived_with_payload_callback(uint key, uint payload)
{
   io_printf(IO_STD, "Event received with key %08x, payload %08x!\n", key, payload);

   //spin1_send_mc_packet(payload, key, 1);

   //spin1_send_mc_packet(0xFFFF0000|127<<4|1, 0,1);
   //spin1_send_mc_packet(0x1, 0,1);

   //io_printf(IO_STD, "Event sent back!\n");
}

void incoming_data_callback(uint key, uint payload) {
  uint index;
//  log_info("Received data %08x with key %08x.", payload, key); 
  index = (key & 0x0000000C) >> 2;
  key = key & 0xFFFFFFF0;
  
  if ( key == MYOSETPOINTKEY ) {
    setpoint_vals[index] = payload;  
    log_info("Setpoint %d is now %d.", index, payload);
  }
  else if ( key == MYOSENSORKEY ) {
    sensor_vals[0] = payload + SENSOROFFSET;  //here we could use averaging!
   }
  else if ( key == MYOMOTORKEY ) {
    sensor_vals[1+index] = payload;  //here we could use averaging!
   }

}


void multiCastPacketReceived_callback(uint key, uint payload)
{
   io_printf(IO_STD, "Event received with key %08x, without payload!\n", key);

   //spin1_send_mc_packet(payload, key, 1);

   //spin1_send_mc_packet(0xFFFF0000|127<<4|1, 0,1);
   //spin1_send_mc_packet(0x1, 0,1);

   //io_printf(IO_STD, "Event sent back!\n");
}




/**************************
 *	    MAIN
 **************************/

void c_main (void)
{
    int chipIDs[] = {0, 1, 256, 257};

    chipID = spin1_get_chip_id();
    coreID = spin1_get_core_id();
    spikeNumber = 0;
    //io_printf(IO_STD, "Simulation starting on (chip: %d, core: %d)...\n", chipID, coreID);

    // Set the number of chips in the simulation
    //spin1_set_core_map(64, (uint *)(0x74220000));

    // set the core map for the simulation
    //spin1_application_core_map(2, 2, core_map);
    //spin1_set_core_map(4, (uint *)(core_map));

    // initialise routing entries
    // set a MC routing table entry to send my packets back to me


 /* ------------------------------------------------------------------- */
  /* initialise routing entries                                          */
  /* ------------------------------------------------------------------- */
  /* set a MC routing table entry to send my packets back to me */
  
   uint e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);

   rtr_mc_set (e,			// entry
	      IOMASK | 0x00000001, 			// key
	      0xFFFF0001,		// mask
	      WEST
	      );
   e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);
    rtr_mc_set (e,			// entry
	      IOMASK | 0x00000000, 			// key
	      0xFFFF0001,		// mask
	      WEST
	      );


  spin1_callback_on (MCPL_PACKET_RECEIVED, incoming_data_callback, 3);
  // Register callbacks
//  spin1_callback_on (MC_PACKET_RECEIVED, own_spike_callback, 1);
  
//  log_info("MC callback requested.");

  // Set timer_callback
  spin1_set_timer_tick(TIME_STEP_MICROSEC);

  spin1_callback_on (TIMER_TICK, timer_callback, 0);

    
  e = rtr_alloc (1);
  if (e == 0)
      rt_error (RTE_ABORT);

  rtr_mc_set (e,
        MYOKEY , // route all myo-motor-sensor data to me!
        0xFFFFF800 | 15<<8 , //THINK, should be <<7!
        (1 << (spin1_get_core_id() + 6)) | (1 << (5 + 6))
        );
    // transfer control to the run-time kernel
    //if (chipID == 0 && coreID == 1)
  time = UINT32_MAX;
  spin1_start(0);


}






