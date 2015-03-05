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

#define TO_IO_BOARD_MASTER_KEY   		0xFFFFE800
#define FROM_IO_BOARD_DEFAULT_MASTER_KEY	0xFEFFF800
#define IO_BOARD_MASK  				0xFFFFFFFF
#define PAUSE      				100  		// microseconds
#define IO_BOARD_ROUTE  			CORE(2) | WEST


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
spin1_send_mc_packet

#define CORE(n)     (1 << (n + 6))
#define ALL_DIRECTIONS  0x003FFFFF
//#define ALL_DIRECTIONS  0xFFFFFFFF



#define SIMULATION_DURATION_SEC  	1
#define TIME_STEP_MICROSEC              100
#define N_NEURONS 		        100


#define TIMER_PRIORITY 			1
#define MC_PACKET_EVENT_PRIORITY 	0
#define DMA_TRANSFER_DONE_PRIORITY 	0

#define SEC_TO_MICROSEC         	1000000

#define N_XCHIPS 2
#define N_YCHIPS 2


uint core_map[4] =
{
   0x1fffe,  0x1fffe, // (0, 0), (0, 1)
   0x1fffe,  0x1fffe  // (1, 0), (1, 1)
};



uint chipID;
uint coreID;
uint spikeNumber;

uint routingKeys[1024];
uint nRoutingKeys = 0;


// declare application types and variables

uint nIterations = 0;


/**************************
 *	 FUNCTIONS
 **************************/

uint getKey(uint id, uint format, uint dim)
{
   uint key = (TO_IO_BOARD_MASTER_KEY | (id << 4) | (format << 3) | dim);
   return key;
}


void addRoutingKey(uint key)
{
   routingKeys[nRoutingKeys] = key;
   nRoutingKeys++;
   io_printf(IO_STD, "New routing key: %x\n", key);


}


int isRoutingKey(uint key)
{
   int isKeyFound = 0;
   for(int i = 0; i < nRoutingKeys; i++)
   {
      if (routingKeys[i] == key)
      {
         isKeyFound = 1;
         break;
      }
   }
   if (isKeyFound == 0)
         io_printf(IO_STD, "key: %x not found\n", key);
   return isKeyFound;
}



void configureRetina(int enabled, int dataFormat)
{
   int id = 0;
   int format = 0;
   int dim = enabled;
   int payload = dataFormat; // 0: no timestamps
   int key = getKey(id, format, dim);

    chipID = spin1_get_chip_id();
    coreID = spin1_get_core_id();
    if (chipID == 0 && coreID == 1)
    {
       if (!isRoutingKey(key))
       {
           uint e = rtr_alloc(1);
           if (e == 0)
               rt_error (RTE_ABORT);

           rtr_mc_set(e,			// entry
	              key, 			// key
	              IO_BOARD_MASK,         	// mask
	              IO_BOARD_ROUTE            // route
	              );
           addRoutingKey(key);
       }
    }
    io_printf(IO_STD, "Configure retina E+/- (%d)\n", enabled);
    spin1_delay_us(PAUSE);
    spin1_send_mc_packet(key, payload, 1);


    if (chipID == 0 && coreID == 1)
    {
       if (!isRoutingKey(0xFEFFF800))
       {
           uint e = rtr_alloc(1);
           if (e == 0)
              rt_error (RTE_ABORT);

            // to plot retina events on tubotron
            rtr_mc_set (e,			// entry
	              0xFEFFF800, 		// key
                      FROM_IO_BOARD_DEFAULT_MASTER_KEY,		// mask
                      // 0xFEFFF800 works
                      // 0xFFFFE800 does not work
	              CORE(3)
	              );
            addRoutingKey(0xFEFFF800);
       }
    }

}



void configureMotorDriver(int enabled)
{
   int id = 2;
   int format = 0;
   int dim = 0;
   int payload = enabled;
   int key = getKey(id, format, dim);

    chipID = spin1_get_chip_id();
    coreID = spin1_get_core_id();
    if (chipID == 0 && coreID == 1)
    {
   if (!isRoutingKey(key))
   {
      uint e = rtr_alloc (1);
      if (e == 0)
          rt_error (RTE_ABORT);

       rtr_mc_set (e,			// entry
      	           key, 			// key
	           IO_BOARD_MASK,         	// mask
	           IO_BOARD_ROUTE            // route
	          );
       addRoutingKey(key);
   }
   }
    io_printf(IO_STD, "Configure motor driver !M+/- (%d)\n", enabled);
    spin1_delay_us(PAUSE);
    spin1_send_mc_packet(key, payload, 1);
}


void setSpeedMotors(int motorNumber, int speed, int isPermanent)
{
   int id = 32;
   int format = 0;
   int dim = motorNumber;
   if (!isPermanent)
       dim += 2;

   int key = getKey(id, format, dim);
   int payload = speed; // payload = desired velocity

    chipID = spin1_get_chip_id();
    coreID = spin1_get_core_id();
    //if (chipID == 0 && coreID == 1)
    {
       //io_printf(IO_STD, "try to set speed\n");
   if (!isRoutingKey(key))
   {
       uint e = rtr_alloc (1);
       if (e == 0)
          rt_error (RTE_ABORT);

        rtr_mc_set (e,			// entry
	           key, 			// key
	           IO_BOARD_MASK,         	// mask
	           IO_BOARD_ROUTE            // route
	           );
       addRoutingKey(key);
   }
   }
    if (isPermanent)
    {
       io_printf(IO_STD, "!MV%d=%d (set motor %d speed)\n", motorNumber, speed);
    }
    else
    {
       io_printf(IO_STD, "!MVD%d=%d (set motor %d speed)\n", motorNumber, speed);
    }

    spin1_delay_us(PAUSE);
    spin1_send_mc_packet(key, payload, 1);
}






void timer_callback(uint key, uint payload)
{
    chipID = spin1_get_chip_id();
    coreID = spin1_get_core_id();

    if (nIterations == 4 && chipID == 0 && coreID == 1)
    {
        //configureRetina(0);
        //configureRetina(1,0);
         configureMotorDriver(1);
	//configureMotorDriver(0);
	//configureMotorDriver(1);
        //setSpeedMotors(0, 10, 0);
        //setSpeedMotors(1, -10, 0);
/*
      //io_printf(IO_STD, "Enable retina (E+ !E0) [chip: %d, core: %d]\n", chipID, coreID);
      //spin1_send_mc_packet(0x00000001, 0, 1);

      io_printf(IO_STD, "Enable motor command !M+ [chip: %d, core: %d]\n", chipID, coreID);
      //spin1_send_mc_packet(0xFEFFFFF0 + , 0, 1);
      spin1_send_mc_packet(0xAAAAA020, 1, 1);
*/
    }
    nIterations++;
    //updateNeurons();
}


uint getPolarity(uint payload)
{
   uint polarity = ((payload & 0x80000000) >> 31);
   return polarity;
}

uint getX(uint payload)
{
   uint x = ((payload & 0x007F0000) >> 16);
   return x;
}

uint getY(uint payload)
{
   uint x = (payload & 0x0000007F);
   return x;
}



void multiCastPacketReceived_with_payload_callback(uint key, uint payload)
{
   //io_printf(IO_STD, "Packet arrived! key = %x, payload = %x\n", key, payload);
   //return;

   uint id, dim, subdim;
   uint idMask = 15 << 7;
   uint dimMask = 31 << 2;
   uint subdimMask = 3;

   //io_printf(IO_STD, "Packet from IO board (%d: id:%d, dim:%d, subdim:%d)!\n", payload, id, dim, subdim);
   //io_printf(IO_STD, "Event received with payload %d!\n", payload);
   //spin1_send_mc_packet(0x00000002, payload, 1);

   //io_printf(IO_STD, "key (%x)!\n", key);
   //io_printf(IO_STD, "key and ioboard (%x)!\n", key & FROM_IO_BOARD_DEFAULT_MASTER_KEY);

//   if (leadAp)
//      spin1_led_control (LED_INV (1));

   if (key  == 0xEEEEEE03)
   {
        uint byte0 = (payload & 0x000000FF);
        uint byte1 = ((payload & 0x0000FF00) >> 8);

        int speed0, speed1;
        if (byte0 < 100)
        {
            speed0 = byte0;
        }
        else
        {
            speed0 = -(byte0 - 100);
        }
        if (byte1 < 100)
        {
            speed1 = byte1;
        }
        else
        {
            speed1 = -(byte1 - 100);
        }

	io_printf(IO_STD, "Setting motor command: %d, %d\n", speed0, speed1);
        setSpeedMotors(0, speed0, 1);
        setSpeedMotors(1, speed1, 1);

   }
   
   
   if ((key & FROM_IO_BOARD_DEFAULT_MASTER_KEY) == FROM_IO_BOARD_DEFAULT_MASTER_KEY)
   {

      id = key & idMask;
      id = id >> 7;

      dim = key & dimMask;
      dim = dim >> 2;

      subdim = key & subdimMask;

      //io_printf(IO_STD, "Packet from IO board (%d: id:%d, dim:%d, subdim:%d)!\n", payload, id, dim, subdim);
      uint polarity = getPolarity(payload);
      uint x = getX(payload);
      uint y = getY(payload);

      if (polarity)
      {
          io_printf(IO_STD, "+(%03d, %03d)\n", x, y);
      }
      else
      {
          io_printf(IO_STD, "-(%03d, %03d)\n", x, y);
      }

      uint toIoBoardPayload = x + y * 256;
   }
}


void multiCastPacketReceived_callback(uint key, uint payload)
{
   io_printf(IO_STD, "Event received without payload (%d)!\n", key);

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



    if (chipID == 0 && coreID == 1)
    {
        configureRetina(1,0);

  /* ------------------------------------------------------------------- */
  /* initialise routing entries                                          */
  /* ------------------------------------------------------------------- */
  /* set a MC routing table entry to send my packets back to me */
   uint motorCommandKey = 0xEEEEEE03;
   if (!isRoutingKey(motorCommandKey))
   {
       uint e = rtr_alloc (1);
       if (e == 0)
          rt_error (RTE_ABORT);

       // motor commands
        rtr_mc_set (e,			// entry
                  motorCommandKey,
                  0xFFFFFFFF,
	          CORE(5)
	           );
       addRoutingKey(motorCommandKey);
   }




    io_printf(IO_STD, "Pushbot program\n");
    //io_printf(IO_STD, "Setting routing table on (chip: %d, core: %d)...\n", chipID, coreID);

    }


    // Call hardware and simulation configuration functions
    spin1_set_timer_tick(TIME_STEP_MICROSEC);

    // Register callbacks
    spin1_callback_on(TIMER_TICK, timer_callback, TIMER_PRIORITY);
    spin1_callback_on(MC_PACKET_RECEIVED, multiCastPacketReceived_callback, MC_PACKET_EVENT_PRIORITY);
    spin1_callback_on(MCPL_PACKET_RECEIVED, multiCastPacketReceived_with_payload_callback, MC_PACKET_EVENT_PRIORITY);

    spin1_start(SYNC_WAIT);
}






