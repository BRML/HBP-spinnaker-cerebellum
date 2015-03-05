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


#include "spin1_api.h"
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
#define TIME_STEP_MICROSEC              100000
#define N_NEURONS 		        100


#define TIMER_PRIORITY 			1
#define MC_PACKET_EVENT_PRIORITY 	0
#define DMA_TRANSFER_DONE_PRIORITY 	0

#define SEC_TO_MICROSEC         	1000000

#define N_XCHIPS 2
#define N_YCHIPS 2

/*     ////////////////////////////
uint core_map[NUMBER_OF_XCHIPS][NUMBER_OF_YCHIPS] =
{
  {2, 2},
  {2, 2}
};
*/

/*
uint core_map[N_XCHIPS][N_YCHIPS] =
{
   {0x6,  0x6}, // (0, 0), (0, 1)
   {0x6,  0x6}  // (1, 0), (1, 1)
};
*/
/*
uint core_map[N_XCHIPS][N_YCHIPS] =
{
   {0x1fffe,  0x1fffe}, // (0, 0), (0, 1)
   {0x1fffe,  0x1fffe}  // (1, 0), (1, 1)
};
*/


uint core_map[4] =
{
   0x1fffe,  0x1fffe, // (0, 0), (0, 1)
   0x1fffe,  0x1fffe  // (1, 0), (1, 1)
};



uint chipID;
uint coreID;
uint spikeNumber;

// declare application types and variables

uint nIterations = 0;


/**************************
 *	 FUNCTIONS
 **************************/


/*
void updateNeurons()
{
    if (chipID == 0 && coreID == 3 && nIterations == 0)
    {
	spin1_send_mc_packet(0x127, 0, 0);
        io_printf(IO_STD, "Spike sent!\n");
    }
    nIterations++;
    return;
}

*/


/**************************
 *        CALLBACKS@00000100
 **************************/

void timer_callback(uint key, uint payload)
{
    chipID = spin1_get_chip_id();
    coreID = spin1_get_core_id();
    uint newID;
    uint newKey;

    if (nIterations == 1 && chipID == 0 && coreID == 1)
    {
    io_printf(IO_STD, "Switching to Spomnibot project\n");

      spin1_send_mc_packet(0x111007F1, 2, 1);
    }
    
    if (nIterations == 2 && chipID == 0 && coreID == 1)
    {
      spin1_send_mc_packet(0x111002b7, 0, 1);
      io_printf(IO_STD, "Beep!\n");
    }

    if (nIterations == 10 && chipID == 0 && coreID == 1)
    {
      spin1_send_mc_packet(0x111002c3, 10, 1); // 10Hz
      io_printf(IO_STD, "Setting up sensor streaming\n");
      spin1_send_mc_packet(0x111002c2, 1<<4|1 , 1); // bump + compass

    }
    
    if (nIterations == 50 && chipID == 0 && coreID == 1)
    {
      spin1_send_mc_packet(0x111002a0, 0x30, 1); //driving forward
      io_printf(IO_STD, "driving forward\n");
    }

    if (nIterations == 200 && chipID == 0 && coreID == 1)
    {
      spin1_send_mc_packet(0x111002a7, 0x00, 1); //stop all
      io_printf(IO_STD, "stopping now\n");
    }
    
    if (chipID == 0 && coreID == 1) {
      io_printf(IO_STD, "iteration %d\n", nIterations); 
      nIterations++;
      }
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


void multiCastPacketReceived_callback(uint key, uint payload)
{
   io_printf(IO_STD, "Event received with key %08x, without payload!\n", key);

   //spin1_send_mc_packet(payload, key, 1);

   //spin1_send_mc_packet(0xFFFF0000|127<<4|1, 0,1);
   //spin1_send_mc_packet(0x1, 0,1);

   //io_printf(IO_STD, "Event sent back!\n");
}


void bump_received(uint key, uint payload)
{
   io_printf(IO_STD, "this was a bump! %08x.%08x \n", key, payload);
   if (payload & 23) //react to front facing bumpers
   {
   spin1_send_mc_packet(0x80000000 | 9  << 7 | 4 << 2 |2,0,0); // notify core 3 (compass guard)
   io_printf(IO_STD, "sending an enable message in return.\n");

   spin1_send_mc_packet(0x111002b6,0,1); // beep
   io_printf(IO_STD, "Beep.\n");
   
   spin1_send_mc_packet(0x111002a0,0xFFFFFFF0,1); // slowly backwards
   io_printf(IO_STD, "Go backwards.\n");

   spin1_send_mc_packet(0x111002a2,0x18,1); //turn around
   io_printf(IO_STD, "And turn!\n");

   }
   
   if (payload & 18) //react to rear facing bumper
   {
   spin1_send_mc_packet(0x111002a7, 0x00, 1);
   }
}

int heading = -1;

void compass_received(uint key, uint payload)
{
   io_printf(IO_STD, "this was a compass message: %08x,%08x \n", key, payload);
   if ( abs(heading - payload) > 100000) {
       spin1_send_mc_packet(0x111002a0,0x40,1); // slowly forwards
       io_printf(IO_STD, "Go forwards again.\n");
       spin1_send_mc_packet(0x111002a2,0,1); // no roll 
       spin1_callback_off(MCPL_PACKET_RECEIVED); // deregister my callback
       heading = -1; //reset heading
   }
}

void enable_packet_received(uint key, uint payload)
{
   io_printf(IO_STD, "this was an enable message (no payload)! %08x.%08x \n", key, payload);
   io_printf(IO_STD, "enabling compass tracking!");
   if (heading < 0) {
       // register compass callback on first notification
       spin1_callback_on(MCPL_PACKET_RECEIVED, compass_received, MC_PACKET_EVENT_PRIORITY);
       }
   heading = payload;
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


    if (chipID == 0 && coreID == 1)
    {
  /* ------------------------------------------------------------------- */
  /* initialise routing entries                                          */
  /* ------------------------------------------------------------------- */
  /* set a MC routing table entry to send my packets back to me */

  io_printf(IO_STD, "Setting routing table on (chip: %d, core: %d)...\n", chipID, coreID);

   uint e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);

    rtr_mc_set (e,			// entry
	      0x11100001, 			// key
	      0xFFFF0001,		// mask
	      SOUTH_WEST
	      );
   e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);
    rtr_mc_set (e,			// entry
	      0x11100000, 			// key
	      0xFFFF0001,		// mask
	      SOUTH_WEST
	      );

   e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);

    rtr_mc_set (e,
        0x80000000 | 9 << 7 | 0 << 2,
        0x80000000 | 15 << 7 | 31 << 2,
        CORE(2) // core 2 handles bump sensor
        );

   e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);

    rtr_mc_set (e,
        0x80000000 | 9  << 7 | 4 << 2 | 2,
        0x80000000 | 15 << 7 | 31 << 2 | 3,
        CORE(3) // core 3 handles compass sensor
        );

   e = rtr_alloc (1);
   if (e == 0)
      rt_error (RTE_ABORT);

    rtr_mc_set (e,
        0x80000000 , //| 9  << 7 | 0 << 2,
        0x80000000 , //| 15 << 7 | 0 << 2,
        CORE(4) // core 4 logs data 
        );

    }

    // Call hardware and simulation configuration functions
    spin1_set_timer_tick(TIME_STEP_MICROSEC);

    if (chipID == 0 && coreID == 1) //core1 handles time-based stuff
    {
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER_PRIORITY);
    }

    if (chipID == 0 && coreID == 2)
    {    
    spin1_callback_on(MCPL_PACKET_RECEIVED, bump_received, MC_PACKET_EVENT_PRIORITY);
    }
    
    if (chipID == 0 && coreID == 3)
    {
    spin1_callback_on(MC_PACKET_RECEIVED, enable_packet_received, MC_PACKET_EVENT_PRIORITY);

    }
    
    if (chipID == 0 && coreID == 4)
    {
    // Register callbacks
    spin1_callback_on(MC_PACKET_RECEIVED, multiCastPacketReceived_callback, MC_PACKET_EVENT_PRIORITY);
    spin1_callback_on(MCPL_PACKET_RECEIVED, multiCastPacketReceived_with_payload_callback, MC_PACKET_EVENT_PRIORITY);
    }

    // transfer control to the run-time kernel
    //if (chipID == 0 && coreID == 1)
    {
       spin1_start(0);


    }

}






