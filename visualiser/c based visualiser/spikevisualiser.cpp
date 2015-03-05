// SpiNNaker visualiser software
// Cameron Patterson
// e.g. compile:  g++ visualiser.cpp -o visualiser -lGLU -lGL -lglut -lpthread
//
// you will need to have GLUT / freeglut libraries installed to use this software. CP 28/09/12 added -lpthread as not implicit in some builds
//
// --------------------------------------------------------------------------------------------------
//
//  NOTE: If using multiple windows you will have weird behaviour if resizing !  (at the moment)
//
// Full Version information found at the tail of the file. Current Version:
//
//  5th Oct 2012:  Fixed Bug with timer/wraparound (casting issue), and support for 48 chip model where chips are missing to be grey
//
// -----------------------------------------------------------------------------------------------------
//  Alter the defines below per preferences
// -----------------------------------------------------------------------------------------------------
//#define TESTING			// CP: Testing use only - should generally be commented out!

//#define LOADMAPPINGS		// uncomment this if you are using mappings (local to global populations from pacman toolchain (mapglobaltolocal.csv maplocaltoglobal.csv) files)
// if on and missing, the program may well crash headlong into the abyss.

#define SIMULATION	RATEPLOTLEGACY // select visualisation being used.  options: HEATMAP, RATEPLOT, RETINA, CHIPTEMP, CPUUTIL, INTEGRATORFG, MAR12RASTER, SEVILLERETINA, LINKCHECK, SPIKERVC

#define STARTCOLOUR	REDS	// starting colour-scheme, REDS, GREYS (b/w), MULTI, BLUES, GREENS, THERMAL
#define STARTMODE	TILED	// Options as below, TILED (normal), INTERPOLATED, HISTOGRAM, LINES, RASTER, EEGSTYLE

#define HIWATER		10	// for fixed scaling: the maximum, for dynamic scaling: the Starting HiWater value.
#define LOWATER		0	// for fixed scaling: the minimum, for dynamic scaling: the starting LoWater value.

#define WINBORDER	110	// output graphics window sizes - this is the grey border around the plot area, set to <100 for no titles/labels/key etc.
#define WINHEIGHT	800	// overall height
#define WINWIDTH	850	// overall width (excluding key)

#define KEYWIDTH	50	// the extra border size on the RHS to give space for the key (disregarded if displaykey is commented)
#define DISPLAYKEY		// comment this out if you don't want to see the key displayed
#define MAXFRAMERATE 	100 	// how fast you want to refresh the graphics (max rate - frames per second)

// --------------------------------------------------------------------------------------------------

// general, Ethernet and threading includes
#include <iostream>
#include <GL/glut.h>
#include <GL/freeglut.h>
#include <math.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#ifdef _WIN32
#include <stdint.h>
#include <winsock2.h>
#include <ws2tcpip.h>

int inet_aton(const char *cp, struct in_addr *addr) {
	addr->s_addr = inet_addr(cp);
	return (addr->s_addr == INADDR_NONE) ? 0 : 1;
}

/* The Win32 function Sleep() has a resolution of about 15 ms and takes
 at least 5 ms to execute.  We use this function for longer time periods.
 Additionally, we use busy-looping over short time periods, to get a
 resolution of about 0.01 ms.  In order to measure such short timespans,
 we use the QueryPerformanceCounter() function.  */

int nanosleep(const struct timespec *requested_delay,
		struct timespec *remaining_delay) {
	static bool initialized;
	/* Number of performance counter increments per nanosecond,
	 or zero if it could not be determined.  */
	static double ticks_per_nanosecond;

	if (requested_delay->tv_nsec < 0
			|| 1000000000L <= requested_delay->tv_nsec) {
		errno = EINVAL;
		return -1;
	}

	/* For requested delays of one second or more, 15ms resolution is
	 sufficient.  */
	if (requested_delay->tv_sec == 0) {
		if (!initialized) {
			/* Initialize ticks_per_nanosecond.  */
			LARGE_INTEGER ticks_per_second;

			if (QueryPerformanceFrequency(&ticks_per_second))
				ticks_per_nanosecond = (double) ticks_per_second.QuadPart
						/ 1000000000.0;

			initialized = true;
		}
		if (ticks_per_nanosecond) {
			/* QueryPerformanceFrequency worked.  We can use
			 QueryPerformanceCounter.  Use a combination of Sleep and
			 busy-looping.  */
			/* Number of milliseconds to pass to the Sleep function.
			 Since Sleep can take up to 8 ms less or 8 ms more than requested
			 (or maybe more if the system is loaded), we subtract 10 ms.  */
			int sleep_millis = (int) requested_delay->tv_nsec / 1000000 - 10;
			/* Determine how many ticks to delay.  */
			LONGLONG wait_ticks = requested_delay->tv_nsec
					* ticks_per_nanosecond;
			/* Start.  */
			LARGE_INTEGER counter_before;
			if (QueryPerformanceCounter(&counter_before)) {
				/* Wait until the performance counter has reached this value.
				 We don't need to worry about overflow, because the performance
				 counter is reset at reboot, and with a frequency of 3.6E6
				 ticks per second 63 bits suffice for over 80000 years.  */
				LONGLONG wait_until = counter_before.QuadPart + wait_ticks;
				/* Use Sleep for the longest part.  */
				if (sleep_millis > 0)
					Sleep(sleep_millis);
				/* Busy-loop for the rest.  */
				for (;;) {
					LARGE_INTEGER counter_after;
					if (!QueryPerformanceCounter(&counter_after))
						/* QueryPerformanceCounter failed, but succeeded earlier.
						 Should not happen.  */
						break;
					if (counter_after.QuadPart >= wait_until)
						/* The requested time has elapsed.  */
						break;
				}
				goto done;
			}
		}
	}
	/* Implementation for long delays and as fallback.  */
	Sleep(requested_delay->tv_sec * 1000 + requested_delay->tv_nsec / 1000000);
	done:

	/* Sleep is not interruptible.  So there is no remaining delay.  */
	if (remaining_delay != NULL) {
		remaining_delay->tv_sec = 0;
		remaining_delay->tv_nsec = 0;
	}
	return 0;
}
#else
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#endif
#include <signal.h>
#include <errno.h>
#include <pthread.h>
using namespace std;
#include <unistd.h>  // included for Fedora 17 Fedora17  28th September 2012 - CP

#ifdef _WIN32
typedef uint32_t uint;
#endif

//  -----------------------------------------------------------------------------------------------------
//  This section is conditonal defines based  on the define section at the top of this file / non-user alterable constants
//  -----------------------------------------------------------------------------------------------------

// which visualiser option
#define HEATMAP 	0
#define RATEPLOT 	1
#define RETINA		2
#define INTEGRATORFG    3
#define RATEPLOTLEGACY  4
#define MAR12RASTER     5
#define SEVILLERETINA	6
#define LINKCHECK	7
#define SPIKERVC	8
#define CHIPTEMP	98
#define CPUUTIL		99

// different colour maps available
#define MULTI 		1
#define GREYS 		2
#define REDS 		3
#define GREENS          4
#define BLUES           5
#define THERMAL		6
#define RED		7
#define BLUE		8

// view mode
#define TILED 		0

#define SDPPORT	17893	// UDP port number used for SDP
#define FIXEDPOINT	0	// number of bits in word of data that are to the right of the decimal place
#define CHIPSX 	7	// total dimensions of system (CPUs in X dimension)
#define CHIPSY 	7	//                            (CPUs in Y dimension)
#define CORESX	4	// cores in X dimension on chip (=sqrt(cores per chip))
#define CORESY	4	// cores in Y dimension on chip (=sqrt(cores per chip))
#define BUFFERS 100 // Number of buffers that the sum will be over

// GLOBAL VARIABLES, my bad.
float highwatermark = HIWATER;// for auto-scaling of plot colours, can dynamically alter this value (255.0 = top of the shop)
float lowwatermark = LOWATER;// for auto-scaling of plot colours, can dynamically alter this value (0 = bottom of the shop)
char somethingtoplot = 0;// determines when we should update the screen (no point in plotting no change eh?)
char freezedisplay = 0;	// whether we should pause the display updates (and send a pause packet to the sim)
int64_t freezetime;	// when pausing the simulation we hold time at the time of pausing (for screen display purposes)
int boxsize = 40, gap = 5;// used for button creation and gaps between these boxes and the edge of the screen
int win1 = 0;			// the main graphics window used by OpenGL
int windowToUpdate;		// used to know which window to update
int colourused = STARTCOLOUR;	// start with requested colour scheme
int displaymode = STARTMODE;	// initialise mode variable for the start
int xdim = CHIPSX * CORESX;		// number of items to plot in the x dimension
int ydim = CHIPSY * CORESY;		// number of items to plot in the y dimension
#ifdef DISPLAYKEY
int keyWidth = KEYWIDTH;	// if a key is requested the width is set
#endif
#ifndef DISPLAYKEY
int keyWidth=0;		// if no key then extra space is not made for it
#endif
int windowBorder = WINBORDER;// variable with border width (for resizing if required)
int windowHeight = WINHEIGHT;// variable with window width (excluding optional key, for resizing if required)
int windowWidth = WINWIDTH + keyWidth;// variable with window height (for resizing if required)
int plotWidth = windowWidth - (2 * windowBorder) - keyWidth;// how wide is the actual plot area
int printlabels = (windowBorder >= 100);
int fullscreen = 0;	// toggles to get rid of menus/labels/axes/key/controls etc.
int gridlines = 0;		// toggles gridlines, starts off

int counter = 0;			// number of times the display loop has been entered
int64_t printpktgone = 0;// if set non zero, this is the time the last Eth packet message was sent, idle function checks for 1s before stopping displaying it
struct timeval startimeus;// for retrieval of the time in us at the start of the simulation
int64_t starttimez;	// storage of persistent times in us
uint buffered_pdata[CHIPSX * CORESX][CHIPSY * CORESY];// this creates a buffer tally for the Ethernet packets (1 ID = one plotted point)
uint spikecount[CHIPSX * CORESX][CHIPSY * CORESY][BUFFERS]; // this is a count of spikes at a received time
uint lastTimer = 0;

//network parameters for the SDP and SpiNNaker protocols

#define MAXBLOCKSIZE		364 			// maximum possible Ethernet payload words for a packet- (SpiNN:1500-20-8-18) (SDP:1500-20-8-26)
#define SPINN_HELLO		0x41			// SpiNNaker raw format uses this as a discovery protocol
#define P2P_SPINN_PACKET 	0x3A   			// P2P SpiNNaker output packets (Stimulus from SpiNNaker to outside world)
#define STIM_IN_SPINN_PACKET 	0x49   			// P2P SpiNNaker input packets (Stimulus from outside world)
#pragma pack(1) 					// stop alignment in structure: word alignment would be nasty here, byte alignment reqd

struct spinnpacket {
	unsigned short version;
	unsigned int cmd_rc;
	unsigned int arg1;
	unsigned int arg2;
	unsigned int arg3;
	unsigned int data[MAXBLOCKSIZE];
};
// a structure that holds SpiNNaker packet data (inside UDP segment)

struct sdp_msg		// SDP message (<=292 bytes)
{
	unsigned char ip_time_out;
	unsigned char pad;
	// sdp_hdr_t
	unsigned char flags;		// SDP flag byte
	unsigned char tag;			// SDP IPtag
	unsigned char dest_port;		// SDP destination port
	unsigned char srce_port;		// SDP source port
	unsigned short dest_addr;		// SDP destination address
	unsigned short srce_addr;		// SDP source address
	// cmd_hdr_t (optional, but tends to be there!)
	unsigned short cmd_rc;		// Command/Return Code
	unsigned short seq;			// seq (new per ST email 27th Oct 2011)
	unsigned int arg1;			// Arg 1
	unsigned int arg2;			// Arg 2
	unsigned int arg3;			// Arg 3
	// user data (optional)
	unsigned int data[MAXBLOCKSIZE];	// User data (256 bytes)
};

typedef struct {
	int64_t filesimtimeoffset;
	short incoming_packet_size;
	unsigned char payload[];
} spinnaker_saved_file_t;

//global variables for SDP packet receiver
int sockfd_input, sockfd;
char portno[6];
struct addrinfo hints_input, hints_output, *servinfo_input, *p_input, *servinfo,
		*p;
struct sockaddr_storage their_addr_input;
int rv_input;
int numbytes_input;
struct sdp_msg * scanptr;
struct spinnpacket * scanptrspinn;
in_addr spinnakerboardip;
int spinnakerboardport;
char spinnakerboardipset = 0;
unsigned char buffer_input[1515]; //buffer for network packets (waaaaaaaaaaay too big, but not a problem here)
//end of variables for sdp spinnaker packet receiver - some could be local really - but with pthread they may need to be more visible

// prototypes for functions below
void error(char *msg);
void init_sdp_listening();
void* input_thread_SDP(void *ptr);
void safelyshut(void);
// end of prototypes

// setup socket for SDP frame receiving on port SDPPORT defined about (usually 17894)
void init_sdp_listening() {
	snprintf(portno, 6, "%d", SDPPORT);

	memset(&hints_input, 0, sizeof(hints_input));
	hints_input.ai_family = AF_INET; // set to AF_INET to force IPv4
	hints_input.ai_socktype = SOCK_DGRAM; // type UDP (socket datagram)
	hints_input.ai_flags = AI_PASSIVE; // use my IP

	if ((rv_input = getaddrinfo(NULL, portno, &hints_input,
			&servinfo_input)) != 0) {
		fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rv_input));
		exit(1);
	}

	if ((sockfd_input = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1) {
		fprintf(stderr, "SDP SpiNNaker listener: socket error");
		exit(1);
	}

	// loop through all the results and bind to the first we can
	for (p_input = servinfo_input; p_input != NULL; p_input =
			p_input->ai_next) {


		if (bind(sockfd_input, p_input->ai_addr, p_input->ai_addrlen) == -1) {
			close(sockfd_input);
			printf("SDP SpiNNaker listener: bind");
			perror("SDP SpiNNaker listener: bind");
			continue;
		}

		break;
	}

	if (p_input == NULL) {
		fprintf(stderr, "SDP listener: failed to bind socket\n");
		printf("SDP listener: failed to bind socket\n");
		exit(-1);
	}

	freeaddrinfo(servinfo_input);

	//printf ("SDP UDP listener setup complete!\n");  	// here ends the UDP listener setup witchcraft
}

void *get_in_addr(struct sockaddr *sa) {
	if (sa->sa_family == AF_INET) {
		return &(((struct sockaddr_in*) sa)->sin_addr);
	}

	return &(((struct sockaddr_in6*) sa)->sin6_addr);
}

void* input_thread_SDP(void *ptr) {
	struct sockaddr_in si_other; // for incoming frames
	socklen_t addr_len_input = sizeof(struct sockaddr_in);
	char sdp_header_len = 26;
	struct timeval stopwatchus;

	//printf("Listening for SDP frames.");

	while (1) { 							// for ever ever, ever ever.
		uint numAdditionalBytes = 0;

		if ((numbytes_input = recvfrom(sockfd_input, (char *) buffer_input,
				sizeof buffer_input, 0, (sockaddr*) &si_other,
				(socklen_t*) &addr_len_input)) == -1) {

			printf("Error: : %s\n", strerror(errno));
			perror((char*) "error recvfrom");
			exit(-1);// will only get here if there's an error getting the input frame off the Ethernet
		}

		scanptr = (sdp_msg*) buffer_input; // pointer to our packet in the buffer from the Ethernet
		scanptrspinn = (spinnpacket*) buffer_input; // pointer to our packet in the buffer from the Ethernet
		numAdditionalBytes = numbytes_input - sdp_header_len;// used for SDP only

		if (spinnakerboardipset == 0
				&& scanptrspinn->cmd_rc != htonl(SPINN_HELLO)) {// if we don't already know the SpiNNaker board IP, and it's not a hello packet (there might be >1 board on the LAN)
			spinnakerboardip = si_other.sin_addr;
			spinnakerboardport = htons(si_other.sin_port);
			spinnakerboardipset++;
			printf("Pkt Received from %s on port: %d\n",
					inet_ntoa(si_other.sin_addr), htons(si_other.sin_port));
		}		// record the IP address of our SpiNNaker board.

		gettimeofday(&stopwatchus, NULL);				// grab current time

#if SIMULATION==RATEPLOTLEGACY
#define key_x(k) (k >> 24)
#define key_y(k) ((k >> 16) & 0xFF)
#define key_p(k) ((k >> 11) & 0xF)
#define nid(k) (k & 0x8FF)

		// The next buffer to fill is the one at the current time
		uint nextTimer = scanptr->arg1;

		// Reset the simulation
		if (nextTimer == 1) {
			lastTimer = 1;
		}

	    // If the time has passed, ignore it
		if (nextTimer < lastTimer) {
			continue;
		}

		uint bufferDiff = nextTimer - lastTimer;
		uint nextBuffer = nextTimer % BUFFERS;
		uint lastBuffer = lastTimer % BUFFERS;
		//fprintf(stderr, "Time = %d, Pos = %d, Last = %d\n", scanptr->arg1, nextBuffer, lastBuffer);

		// If more than the number of buffers has passed, clear the buffers
		if (bufferDiff >= BUFFERS) {
			for (uint i = 0; i < (CHIPSX * CORESX); i++) {
				for (uint j = 0; j < (CHIPSY * CORESY); j++) {
					for (uint k = 0; k < BUFFERS; k++) {
						spikecount[i][j][k] = 0;
					}
					buffered_pdata[i][j] = 0;
				}
			}
		}// else if (nextTimer != lastTimer) {
			// Only do this if this is not the same buffer as last time
		    // otherwise, we can just add in to the buffer

			// Subtract the points from the last time point, and clear the
			// counts for this time point
			/*for (uint i = 0; i < (CHIPSX * CORESX); i++) {
				for (uint j = 0; j < (CHIPSY * CORESY); j++) {
					uint k = (lastBuffer + 1) % BUFFERS;
					while (k != nextBuffer) {
						buffered_pdata[i][j] -= spikecount[i][j][k];
						spikecount[i][j][k] = 0;
						k = (k + 1) % BUFFERS;
					}
					buffered_pdata[i][j] -= spikecount[i][j][nextBuffer];
					spikecount[i][j][nextBuffer] = 0;
				}
			}
			*/
		//}

		// Extract the data for the current time point
		for (uint i = 0; i < numAdditionalBytes / 4; i++) {// for all extra data (assuming regular array of paired words, word1=key, word2=data)
			uint x = key_x(scanptr->data[i]);		// chip x coordinate
			uint y = key_y(scanptr->data[i]);		// chip y coordinate
			uint p = key_p(scanptr->data[i]);       // core of chip (note: 4 bits)

			if ((x >= CHIPSX) || (y >= CHIPSY) || (p >= (CORESX * CORESY))) {
				continue;
			}

			uint px = p % CORESX;
			uint py = p / CORESX;
			//printf("x: %d, y: %d, p:%d, px: %d, py: %d, neurid:%d\n", x, y, p, px, py, neurid); // do some printing for debug

			int xpos = (x * CORESX) + px;
			int ypos = (y * CORESY) + py;

			spikecount[xpos][ypos][nextBuffer] += 1;
			buffered_pdata[xpos][ypos] += 1;
		}

		/*for (uint i = 0; i < (CHIPSX * CORESX); i++) {
			for (uint j = 0; j < (CHIPSY * CORESY); j++) {
				float input = (float) spikecount[i][j][nextBuffer];
				float pastdata = (float) buffered_pdata[i][j];
				input += pastdata * exp(-0.1/3.0);
				buffered_pdata[i][j] = (int) input;
			}
		} */

		lastTimer = nextTimer;
		somethingtoplot=1;// indicate we should refresh the screen as we likely have new data

#endif
	}
	return NULL;
}

void error(char *msg) {
	perror(msg);
	exit(1);
}

void cleardown(void) {
	for (int i = 0; i < xdim; i++) {
		for (int j = 0; j < ydim; j++) {
			buffered_pdata[i][j] = 0;
		}
	}
	highwatermark = HIWATER;// reset for auto-scaling of plot colours, can dynamically alter this value (255.0 = top of the shop)
	lowwatermark = LOWATER;	// reset for auto-scaling of plot colours, can dynamically alter this value (255.0 = top of the shop)

	//printf("Cleared the Slate\n");
}

//-------------------------------------------------------------------------
//  Draws a string at the specified coordinates.
//-------------------------------------------------------------------------
void printgl(float x, float y, void *font_style, char* format, ...) {
	va_list arg_list;
	char str[256];
	int i;

	// font options:  GLUT_BITMAP_8_BY_13 GLUT_BITMAP_9_BY_15 GLUT_BITMAP_TIMES_ROMAN_10 GLUT_BITMAP_HELVETICA_10 GLUT_BITMAP_HELVETICA_12 GLUT_BITMAP_HELVETICA_18 GLUT_BITMAP_TIMES_ROMAN_24

	va_start(arg_list, format);
	vsprintf(str, format, arg_list);
	va_end(arg_list);

	glRasterPos2f(x, y);

	for (i = 0; str[i] != '\0'; i++)
		glutBitmapCharacter(font_style, str[i]);
}

void printglstroke(float x, float y, float size, float rotate, char* format,
		...) {
	va_list arg_list;
	char str[256];
	int i;

	va_start(arg_list, format);
	vsprintf(str, format, arg_list);
	va_end(arg_list);

	glPushMatrix();
	glEnable(GL_BLEND);   // antialias the font
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	glEnable(GL_LINE_SMOOTH);
	glLineWidth(1.5);   // end setup for antialiasing
	glTranslatef(x, y, 0);
	glScalef(size, size, size);
	glRotatef(rotate, 0.0, 0.0, 1.0);
	for (i = 0; str[i] != '\0'; i++)
		glutStrokeCharacter(GLUT_STROKE_ROMAN, str[i]);
	glDisable(GL_LINE_SMOOTH);
	glDisable(GL_BLEND);
	glPopMatrix();
}

float colour_calculator(float inputty, float hiwater, float lowater) {
	float scalingfactor = 0;
	float fillcolour = 1.0;
	float diff = hiwater - lowater;

	if (diff <= 0.0001) {
		fillcolour = 1.0;// if in error, or close to a divide by zero (no intensity plotted)
	} else {
		scalingfactor = 1 / diff;// work out how to scale the input data depending on low and highwater values
		fillcolour = (scalingfactor * (inputty - lowater));	// calculate the colour to plot
	}
	if (fillcolour < 0.0)
		fillcolour = 0.0;
	if (fillcolour > 1.0)
		fillcolour = 1.0;	// must always range between 0 and 1 floating point

	//if (inputty>-66000) printf("Dataz[i]: %f, Hi: %f, Lo: %f, diff: %f,\n  aboveLW:%f  Scaling factor: %f, fillcolour %f\n",inputty,hiwater,lowater,diff,(inputty-lowater),scalingfactor,fillcolour);

	//if (highwatermark>0.0001) fillcolour = 1.0-(inputty/hiwater);  //stop a divide by zero!
	//if (fillcolour !=0) printf("Fillcolour: %f, inputty: %d\n", fillcolour, inputty);
	if (colourused == 1) {
	}

	switch (colourused) {
	case 1: {
#define COLOURSTEPS 6	// 6 different RGB colours, Black, Blue, Cyan, Green, Yellow, Red
		float gamut[COLOURSTEPS][3] = { { 0.0, 0.0, 0.0 }, { 0.0, 0.0, 1.0 }, {
				0.0, 1.0, 1.0 }, { 0.0, 1.0, 0.0 }, { 1.0, 1.0, 0.0 }, { 1.0,
				0.0, 0.0 } };

		int colourindex = (float) fillcolour * (float) (COLOURSTEPS - 1);
		float colouroffset = (float) (colourindex + 1)
				- (fillcolour * (float) (COLOURSTEPS - 1)); // how far away from higher index (range between 0 and 1).
		float R = ((1.0 - colouroffset) * (float) gamut[colourindex + 1][0])
				+ (colouroffset * (float) gamut[colourindex][0]);
		float G = ((1.0 - colouroffset) * (float) gamut[colourindex + 1][1])
				+ (colouroffset * (float) gamut[colourindex][1]);
		float B = ((1.0 - colouroffset) * (float) gamut[colourindex + 1][2])
				+ (colouroffset * (float) gamut[colourindex][2]);
//		printf("Dataz[i]: %f, Hi: %f, Lo: %f, Fillcolour: %f, Index %d\n    Offset %f,  Low %f, Up %f, Tot %f.\n",
//		       inputty,hiwater,lowater,fillcolour,colourindex,
//		          colouroffset, (1.0-colouroffset)*(float)gamut[colourindex+1][1],(colouroffset*(float)gamut[colourindex][1]),R);
//		printf("Offset %f, LowGr %f, UpGr %f, Tot %f.\n",
//		          colouroffset, (1.0-colouroffset)*(float)gamut[colourindex+1][1],(colouroffset*(float)gamut[colourindex][1]),G);
//		printf("R %f,   G %f,   B %f.   Offset: %f\n",R,G,B,colouroffset);
		//spilt into n sections. specify colours for each section. how far away from top of section is it
		//multiply R,G,B difference by this proportion

		glColor4f(R, G, B, 1.0);	  		// colours option
		break;
	}
	case 2:
		glColor4f(fillcolour, fillcolour, fillcolour, 1.0);	// greyscales option
		break;
	case 3:
		glColor4f(fillcolour, 0.0, 0.0, 1.0);	  		// redscales only
		break;
	case 4:
		glColor4f(0.0, fillcolour, 0.0, 1.0);	  		// greenscales option
		break;
	case 5:
		glColor4f(0.0, 0.0, fillcolour, 1.0);	  		// bluescales option
		break;
	case 6: {
#define COLOURSTEPSB 5	//  black, purpleymagenta, red, yellow, white (RGB)
		float gamut[COLOURSTEPSB][3] = { { 0.0, 0.0, 0.0 }, { 1.0, 0.0, 1.0 }, {
				1.0, 0.0, 0.0 }, { 1.0, 1.0, 0.0 }, { 1.0, 1.0, 1.0 } };

		int colourindex = (float) fillcolour * (float) (COLOURSTEPSB - 1);
		float colouroffset = (float) (colourindex + 1)
				- (fillcolour * (float) (COLOURSTEPSB - 1)); // how far away from higher index (range between 0 and 1).
		float R = ((1.0 - colouroffset) * (float) gamut[colourindex + 1][0])
				+ (colouroffset * (float) gamut[colourindex][0]);
		float G = ((1.0 - colouroffset) * (float) gamut[colourindex + 1][1])
				+ (colouroffset * (float) gamut[colourindex][1]);
		float B = ((1.0 - colouroffset) * (float) gamut[colourindex + 1][2])
				+ (colouroffset * (float) gamut[colourindex][2]);

		glColor4f(R, G, B, 1.0);	  		// colours option
		break;
	}
	case 7:
		glColor4f(fillcolour < 0.01 ? 0.0 : 1.0, 0.0, 0.0, 1.0);// everything is red option except v close to 0 (to get rid of flickery colour in line mode) etc.
		break;
	case 8:
		glColor4f(0.0, 0.0, fillcolour < 0.01 ? 0.0 : 1.0, 1.0);// everything is white option except v close to 0 (to get rid of flickery colour in line mode etc.
		break;

	}

	return fillcolour;
}

// display function, called whenever the display window needs redrawing
void display(void) {

	glPointSize(1.0);

	counter++;				// how many frames have we plotted in our history

	glLoadIdentity();
	glutSetWindow(windowToUpdate);	// specifically look at our plotting window
	glLoadIdentity();

	//glutPostRedisplay();

	glClearColor(0.8, 0.8, 0.8, 1.0); 		// background colour - grey surround
	glClear(GL_COLOR_BUFFER_BIT);

	glColor4f(0.0, 0.0, 0.0, 1.0); 						// Black Text for Labels

	if (printlabels && fullscreen == 0) {// titles and labels are only printed if border is big enough

		// Graph Titles
		char stringy2[]="Spike Rates - Live SpiNNaker Plot";
		printgl((windowWidth / 2) - 200, windowHeight - 50,
				GLUT_BITMAP_TIMES_ROMAN_24, stringy2);	// Print Title of Graph

		char stringytime[] = "Timer tick: %d";
		printgl((windowWidth / 2) - 200, windowHeight - 75,
				GLUT_BITMAP_HELVETICA_18, stringytime, lastTimer);

		char stringy4[] = "%d";

		// X Axis
		char stringy1[] = "X Coord";
		printglstroke((windowWidth / 2) - 25, 20, 0.12, 0, stringy1);
		int xlabels = xdim;
		float xspacing = ((float) (plotWidth) / xdim);
		for (int i = 0; i < xlabels; i++) {   					// X-Axis
			printgl(
					(i * xspacing) + windowBorder + ((xspacing - 8) / 2)
							- 3, 60, GLUT_BITMAP_HELVETICA_18, stringy4, i);// Print X Axis Labels at required intervals
		}

		// Y Axis
		char stringy5[] = "Y Coord";
		printglstroke(25, (windowHeight / 2) - 50, 0.12, 90, stringy5);	// Print Y-Axis label for Graph
		int ylabels = ydim;
		float yspacing =
				((float) (windowHeight - (2 * windowBorder)) / ydim);
		for (int i = 0; i < ylabels; i++) {   					// Y-Axis
			printgl(60,
					(i * yspacing) + windowBorder + ((yspacing - 18) / 2)
							+ 2, GLUT_BITMAP_HELVETICA_18, stringy4, i);// Print Y Axis Labels at required intervals
		}

	}   // titles and labels are only printed if border is big enough

	float pdata[xdim][ydim]; // this stores the value of each plotted point data (time == now)
	for (int i = 0; i < xdim; i++) {
		for (int j = 0; j < ydim; j++) {
			pdata[i][j] = (float) buffered_pdata[i][j] / (float) pow(2.0, FIXEDPOINT);// scale data to something sensible for colour gamut
//			printf("Data: %d, POWER: %f  = %f\n", buffered_pdata[i][j],(float)pow(2,FIXEDPOINT), pdata[i][j]);

			if (pdata[i][j] > highwatermark)
				highwatermark = pdata[i][j];// only alter the high water mark when using dynamic scaling & data received
			if (pdata[i][j] < lowwatermark)
				lowwatermark = pdata[i][j];// only alter the low water mark when using dynamic scaling & data received
			if (pdata[i][j] > 65536.0)
				pdata[i][j] = 65536.0;	// check: can't increment above 65536 saturation level TODO remove restriction
			if (pdata[i][j] < -65536.0)
				pdata[i][j] = -65536.0;// check: can't decrement below -65536 saturation level TODO remove restriction
		}
	}  // scale all the values to plottable range

	float xsize = ((float) (plotWidth) / xdim);
	if (xsize < 1.0)
		xsize = 1.0;
	float ysize = ((float) (windowHeight - (2 * windowBorder)) / ydim);

	glColor4f(0.0, 0.0, 0.0, 1.0);
	glBegin(GL_QUADS);
	glVertex2f(windowBorder, windowBorder);  //btm left
	glVertex2f(windowBorder + plotWidth, windowBorder); //btm right
	glVertex2f(windowBorder + plotWidth, windowBorder + windowHeight - (2 * windowBorder));  // top right
	glVertex2f(windowBorder, windowBorder + windowHeight - (2 * windowBorder)); // top left */
	glEnd(); // this plots the basic quad box filled as per colour above

	for (int i = 0; i < xdim; i++) {
		for (int j = 0; j < ydim; j++) {

			colour_calculator(pdata[i][j], highwatermark, lowwatermark);// work out what colour we should plot - sets 'ink' plotting colour

			if (pdata[i][j] > -66000.0) {
				int triangleAmount = 20; //# of triangles used to draw circle

				GLfloat twicePi = 2.0f * M_PI;

				glBegin(GL_TRIANGLE_FAN);
				int x = windowBorder + (i * xsize) + (xsize / 2);
				int y = windowBorder + (j * ysize) + (ysize / 2);

				glVertex2f(x, y); // center of circle
				for (int c = 0; c <= triangleAmount; c++) {
					glVertex2f(
						(x + ((xsize / 2) * cos(c *  twicePi / triangleAmount))),
						(y + ((ysize / 2) * sin(c * twicePi / triangleAmount)))
					);
				}

				/*glBegin(GL_QUADS);

				glVertex2f(windowBorder + (i * xsize),
						windowBorder + (j * ysize));  //btm left
				glVertex2f(windowBorder + ((i + 1) * xsize),
						windowBorder + (j * ysize)); //btm right
				glVertex2f(windowBorder + ((i + 1) * xsize),
						windowBorder + ((j + 1) * ysize));  // top right
				glVertex2f(windowBorder + (i * xsize),
						windowBorder + ((j + 1) * ysize)); // top left */
				glEnd(); // this plots the basic quad box filled as per colour above
			}

			glColor4f(0.0, 0.0, 0.0, 1.0);
		}
	}

	if (gridlines != 0) {	// scrolling modes x scale and labels and gridlines
		uint xsteps = xdim, ysteps = ydim;
		glColor4f(0.8, 0.8, 0.8, 1.0);
		if (xsize > 3.0) {		// if not going to completely obscure the data
			for (uint xcord = 0; xcord <= xsteps; xcord++) {	// vertical grid lines
				//xsize
				glBegin(GL_LINES);
				glVertex2f(windowBorder + (xcord * xsize), windowBorder); //bottom
				glVertex2f(windowBorder + (xcord * xsize),
						windowHeight - windowBorder); 	//top
				glEnd();
			}
		}
		if (ysize > 3.0) {		// if not going to completely obscure the data
			for (uint ycord = 0; ycord <= ysteps; ycord++) {	// horizontal grid lines
				glBegin(GL_LINES);
				glVertex2f(windowBorder, windowBorder + (ycord * ysize)); //left
				glVertex2f(windowWidth - windowBorder - keyWidth,
						windowBorder + (ycord * ysize)); 	//right
				glEnd();
			}
		}
	}

//#endif

#ifdef DISPLAYKEY
	if (fullscreen == 0) {				// only print if not in fullscreen mode
		glColor4f(0.0, 0.0, 0.0, 1.0); 					// Black Text for Labels
		char stringy8[] = "%.2f";
		int keybase = windowBorder + (0.20 * (windowHeight - windowBorder));// bottom of the key
		printgl(windowWidth - 55, windowHeight - (1 * windowBorder) - 5,
				GLUT_BITMAP_HELVETICA_12, stringy8, highwatermark);	// Print HighWaterMark Value
		printgl(windowWidth - 55, keybase - 5, GLUT_BITMAP_HELVETICA_12,
				stringy8, lowwatermark);			// Print LowWaterMark Value
		float interval, difference = highwatermark - lowwatermark;
		for (float i = 10000; i >= 0.1; i /= 10.0)
			if (difference < i) {
				if (difference < (i / 2))
					interval = i / 20.0;
				else
					interval = i / 10.0;
			}
		int multipleprinted = 1;
		float linechunkiness = (float) (windowHeight - (windowBorder + keybase))
				/ (float) (highwatermark - lowwatermark);
		if ((windowHeight - windowBorder - keybase) > 0) {// too small to print
			for (uint i = 0; i < (windowHeight - windowBorder - keybase); i++) {
				float temperaturehere = 1.0;
				if (linechunkiness > 0.0)
					temperaturehere = ((float) i / linechunkiness)
							+ lowwatermark;
				colour_calculator(temperaturehere, highwatermark, lowwatermark);
				glBegin(GL_LINES);
				glVertex2f(windowWidth - 65, i + keybase); // rhs
				glVertex2f(windowWidth - 65 - keyWidth, i + keybase); // lhs
				glEnd();  	//draw_line;
				if ((temperaturehere - lowwatermark)
						>= (interval * multipleprinted)) {
					glColor4f(0.0, 0.0, 0.0, 1.0);
					glLineWidth(4.0);
					glBegin(GL_LINES);
					glVertex2f(windowWidth - 65, i + keybase); // rhs
					glVertex2f(windowWidth - 75, i + keybase); // inside
					glVertex2f(windowWidth - 55 - keyWidth, i + keybase); // inside
					glVertex2f(windowWidth - 65 - keyWidth, i + keybase); // lhs
					glEnd();
					glLineWidth(1.0);
					printgl(windowWidth - 55, i + keybase - 5,
							GLUT_BITMAP_HELVETICA_12, stringy8,
							lowwatermark + (multipleprinted * interval));
					// Print labels for key - font? GLUT_BITMAP_8_BY_13
					multipleprinted++;
				}
				// if need to print a tag - do it
			}

			glColor4f(0.0, 0.0, 0.0, 1.0);
			glLineWidth(2.0);
			glBegin(GL_LINE_LOOP);
			glVertex2f(windowWidth - 65 - keyWidth, keybase); // bottomleft
			glVertex2f(windowWidth - 65, keybase); // bottomright
			glVertex2f(windowWidth - 65, windowHeight - (1 * windowBorder)); // topright
			glVertex2f(windowWidth - 65 - keyWidth,
					windowHeight - (1 * windowBorder)); // topleft
			glEnd();  	//draw_line loop around the key;
			glLineWidth(1.0);
		} // key is only printed if big enough to print
	}
#endif

	glutSwapBuffers(); 			// no flickery gfx
	somethingtoplot = 0;			// indicate we have finished plotting
} // display

// called whenever the display window is resized
void reshape(int width, int height) {
	if (glutGetWindow() == 1) {
		windowWidth = width;
		plotWidth = windowWidth - (2 * windowBorder) - keyWidth;
		if (fullscreen == 1) {
			windowWidth += keyWidth;
			plotWidth = windowWidth - keyWidth;
		}
		if (windowWidth < (2 * windowBorder) + keyWidth) {
			windowWidth = (2 * windowBorder) + keyWidth;// stop the plotting area becoming -ve and crashing
			plotWidth = 0;
		}
		windowHeight = height;
	}
	//printf("Wid: %d, Hei: %d.\n",width,height);
	glViewport(0, 0, (GLsizei) width, (GLsizei) height); // viewport dimensions
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	// an orthographic projection. Should probably look into OpenGL perspective projections for 3D if that's your thing
	glOrtho(0.0, width, 0.0, height, -50.0, 50.0);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	somethingtoplot = 1;		// indicate we will need to refresh the screen

} // reshape

// Called repeatedly, once per OpenGL loop
void idleFunction() {

	int usecperframe = (1000000 / MAXFRAMERATE);  		// us target per frame
	struct timeval stopwatchus;			// declare timing variables
	struct timespec ts;	// used for calculating how long to wait for next frame
	int64_t howlongtowait;			// for timings

	if (plotWidth != windowWidth - (2 * windowBorder) - keyWidth)
		printf(
				"NOT SAME: windowWidth-(2*windowBorder)-keyWidth=%d, plotWidth=%d.\n",
				windowWidth - (2 * windowBorder) - keyWidth, plotWidth);

	gettimeofday(&stopwatchus, NULL);				// grab current time
	howlongtowait = ((int64_t) starttimez
			+ ((int64_t) counter * (int64_t) usecperframe))
			- (((int64_t) stopwatchus.tv_sec * (int64_t) 1000000)
					+ (int64_t) stopwatchus.tv_usec);// how long in us until we need to draw the next frame
	//printf("Now: %lu,   Target: %lu.  Therefore sleeping for %lu us and %dns\n",(starttimez+(counter*usecperframe)),((stopwatchus.tv_sec*1000000) + stopwatchus.tv_usec),howlongtowait,howlongtowait*1000);

	if (howlongtowait > 0) {
		ts.tv_sec = howlongtowait / 1000000;// # seconds (very unlikely to be in the seconds!)
		ts.tv_nsec = (howlongtowait % 1000000) * 1000;	// us * 1000 = nano secs
		nanosleep(&ts, NULL);	// if we are ahead of schedule sleep for a bit
	}

	//if (somethingtoplot != 0) {
		windowToUpdate = win1;					// update the main master window
		display(); // update the display - will be timered inside this function to get desired FPS
	//} else {
	//}// do we actually want to update a bare min number of times - e.g. once per sec?

	for (uint i = 0; i < (CHIPSX * CORESX); i++) {
		for (uint j = 0; j < (CHIPSY * CORESY); j++) {
			buffered_pdata[i][j] = (int)
					(((float) buffered_pdata[i][j]) * exp(-0.1/3.0));
		}
	}
}

void myinit(void) {
	glClearColor(0.0, 0.0, 0.0, 1.0);
	glColor3f(1.0, 1.0, 1.0);
	glShadeModel(GL_SMOOTH); // permits nice shading between plot points for interpolation if required
}

void safelyshut(void) {

	//printf("Safely Shutting down and that. %d\n",fileinput);
	exit(0);				// kill program dead
}

int main(int argc, char **argv) {
#ifdef _WIN32
	WSADATA wsaData;
	WSAStartup(2, &wsaData);
#endif

	cleardown();// reset the plot buffer to something sensible (i.e. 0 to start with)
	gettimeofday(&startimeus, NULL);
	starttimez = (((int64_t) startimeus.tv_sec * (int64_t) 1000000)
			+ (int64_t) startimeus.tv_usec);

	pthread_t p2;// this sets up the thread that can come back to here from type
	init_sdp_listening();//initialization of the port for receiving SDP frames
	pthread_create(&p2, NULL, input_thread_SDP, NULL);// away the SDP network receiver goes

	glutInit(&argc, argv); /* Initialise OpenGL */

	glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB); /* Set the display mode */
	glutInitWindowSize(windowWidth + keyWidth, windowHeight); /* Set the window size */
	glutInitWindowPosition(0, 100); /* Set the window position */
	win1 = glutCreateWindow("Real Time Plot of SpiNNaker Data"); /* Create the window */
	windowToUpdate = win1;
	myinit();
	glutDisplayFunc(display); /* Register the "display" function */
	glutReshapeFunc(reshape); /* Register the "reshape" function */
	glutIdleFunc(idleFunction); /* Register the idle function */

	//glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_CONTINUE_EXECUTION);
	glutCloseFunc(safelyshut); // register what to do when the use kills the window via the frame object

	glutMainLoop(); /* Enter the main OpenGL loop */
	fprintf(stderr, "goodbye");
	fflush(stderr);

	return 0;
}

// -----------------------------------------------------------------------------------------------------
//  Legacy Versioning information
// -----------------------------------------------------------------------------------------------------
//
// v17.2 - 9th Nov. Fix Temp/CPU x/y display orientations, chunked reading files so doesn't run out of memory, times >6mins now in "9m47" format, spike rate option for raster.
// v17.1 - 3rd Nov. Added 90 (D)egree rotate to the transformation menu, fixed X/Y transposition error on bias sends for ratedemo.
// v17.0 - 3rd Nov. Coordinates system redone to better support future simulation and correct some 'hacks' done for heatdemo
// v16.8 - 2nd Nov. fixed issue with multi-chip sims for rate plot (was hard coded for 0,0 previously)
// v16.7 - 1st Nov. long replaced with int64_t for 32/64 bit compatibility of saved files.
// v16.6 - 1st Nov. Added Thermometer and CPU Utilisation simulations, fixed some aspects of rateplot
// v16.5 - 30th Oct. File Controls now on right mouse button rather than in defines.  Note: File Pause just drops data, it does not pause time!
// v16.4 - 29th Oct. Fixed colour bug & simplified colour map section
// v16.3 - 27th Oct. Fixed bug with playback if a pause of >1sec without packets
// v16.2 - 27th Oct. Added option to play back recording at different rates (multiplier at cmd line)
//         eg. "visualiser file.spinn 4"  will play back at 4 speed, or 0.2 (for 1/5th speed)
// v16.1 - 26th Oct. Fixes to load/save routines. Going into SVN now.
// v16.0 - 25th Oct. Added support for Load/Save of files of packet dumps instead of live Ethernet... (add filename as 1st argument to load a .spinn file).
//		For save, uncomment DEFINE and look for dated "packetsYYMMMDD_HHMM.spinn"   Alternative save format NeuroTools (.neuro) - see 2nd define
// v15.3 - 25th Oct. Added support for multi-chip spike rate plots
// v15.2 - 24th Oct. S(q)uare becomes 'b' for borders,  E(x)it becomes (Q)uit.  'Y' 'X' and 'V'ector plot flips added to keys indicated, dynamically raster plot neurids received (and scale to suit, no longer fixed at 100)
// v15.1 - 21st Oct. Added zero (0) and randomise (9) values for heatmap demo
// v15.0 - 20th Oct. EEG option added. (inbetween version numbers are unlucky), little map usable for selection & in all modes now.
// v12.4 - 19th Oct. Added '0' zero option on heatmap to reset all to zero. Fix double entry for Right click to turn off all Raster entries.
// v12.3 - 18th Oct. Bug fix histogram full size, ID of packet receive ignores hellos, startup window 0 error, e(x)it on menu, hide (" > X) controls from 2nd window
// v12.2 - 17th Oct. Added Right Mouse Button support (including special features for rate plots spawning raster plots)
// v12.1 - 17th Oct. Added support for 'r'aster plot option.  Also on RATEPLOT code, pressing 'z' on selected tile will open population raster plot
// v12.0 - 13th Oct. Added support for line plotting (l) - worms for each data value
// v11.1 - 11th Oct. Added sQuare gridlines 'q' support, and green and blue colour options (4,5), add YFLIP define option
// v11.0 - 11th Oct. Added support for SpiNNaker packets and RETINA visualisation application
// v10.1 - 10th Oct. Full screen mode 'f' toggle added (takes away all borders/menus/titles etc).
// v10.0 - 6th Oct.  Changed pause button to ", colour changing to numerics not cursors,  added 'r'aster request functionality to Rate Plot model used with cursors.
// v9.0 -  5th Oct.  Incorporate Spike Rate Plot Option, variable parameters for sdpsend, spike rate plot, keepalives removed per LAP
// v8.1 -  4th Oct.  Added keepalive packets (every 30s) - per LAP/ST - see idleFunction().
// v8.0 -  4th Oct.  Numbers '#' option available for histogram too.  Colour maps now #defines.
// v7.0 -  3rd Oct.  Added Histogram option for plotting - use 't' for tiled. 'h' for histogram and 'i' for interpolated mode
//                     Changed default ratio, changed co-ordinates to 0:7 on both axes, values text changes colour with intensity
// v6.0 -  3rd Oct.  Add in option for plotting of values - toggles with the '#' key, off at start.
// v5.0 -  3rd Oct.  FIX E/W transposition,  Fixed low water plotting bug
// v4.0 -  Sep2011.  Resizable.
//
