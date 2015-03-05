/*
 *  	simulate.h
 *
 *		pseudo-random number generators
 *
 *  	Created by Michael Hopkins in February 2014
 *
 *  
 */

#ifndef SPINN_SIMULATE
#define SPINN_SIMULATE

#include <stdint.h>
#include <stdfix.h>


/***************************************************

	Uniform RNGs
	
	These all return well-distributed unsigned 32-bit ints that 
	have been tested rigorously on the DIEHARD, dieharder and TestU01
	test suites. The Marsaglia KISS generators are slightly faster
	and the 64-bit one uses the theoretically superior multiplicative
	algorithm.  The WELL1024a has a cycle length of (2^1024)-1
	
	Two versions are available.  A simple version which
	has a global hidden seed which does not need to be set, and a custom
	version which allows seeds to be set by the user to either 
	
		1 - promote independence or 
		2 - guarantee identical behaviour 
		
	..across multiple random number streams.
	
	These generators can all be used with the non-uniform RNGs below
	

****************************************************/
//////////////////////////////
// The simple generators
//////////////////////////////

/* 
	Implementation of a Marsaglia 32-bit KISS generator which uses no multiply instructions
	
   209.9 nanosecs (i.e. 42 ticks) per call
   
   Only available in simple form.  Very good for single stream of PRNs.
   
*/ 
uint32_t mars_kiss32( void );


/* 
	Implementation of Marsaglia JKISS RNG uses 64-bit value and 2x multiplies
	
	219.9 nanosecs (i.e. 44 ticks) per call on ARM with gcc 4.8.1
	
	The best general purpose trade-off between speed, equidistribution and cycle length.
	
	Also available in custom seed form.
	
*/ 
uint32_t mars_kiss64_simp( void );


/*
   WELL 1024a long cycle generator (2^1024 - 1) from L'Ecuyer & Panneton
   
   Better equi-distribution and warm-up performance than Mersenne Twister, and faster
   
   294.9 nanosecs (i.e. 59 ticks) per call
   
*/
// The initialiser function that MUST BE CALLED ONCE before WELLRNG1024a() is used
// global WELL1024a seed is randomised each time it is called
void init_WELL1024a_simp( void );


// the generator itself
uint32_t WELL1024a_simp( void );



//////////////////////////////
// The custom-seed generators
//////////////////////////////


// seed type for the Marsaglia KISS 64 RNG
typedef uint32_t mars_kiss64_seed_t[4];

// MUST USE THIS before working with proposed seed
void		validate_mars_kiss64_seed( mars_kiss64_seed_t seed ); 

// the Marsaglia KISS 64 RNG with custom seed
uint32_t mars_kiss64_seed( mars_kiss64_seed_t seed );



// seed type for the L'Ecuyer WELL 1024a RNG
// 33rd element is the static variable used in simple version
typedef 	uint32_t WELL1024a_seed_t[33];

// MUST USE THIS before working with proposed seed
void		validate_WELL1024a_seed( WELL1024a_seed_t seed ); 

// the WELL 1024a RNG with custom seed
uint32_t WELL1024a_seed( WELL1024a_seed_t seed );



/***************************************************

	Non-uniform RNGs
	
	Being added to all the time, and updated for better speed as 
	fixed-point transcendentals and optimised multiplies become available


****************************************************/
/*
	Interface to a generic uniform random number generator is defined as follows

		- for a simple type call as ( rng_type, NULL, .. )
		- for a seeded type call as ( rng_type, seed_vector, .. )

	This will generate some argument type warnings when used with simple URNGs
	but avoids a lot of code duplication and allows use of any Uniform RNG with 
	any Non-Uniform variates which is valuable flexibility.
	
*/
typedef uint32_t (*uniform_rng)( uint32_t* );


/*
 * Von Neuman's Exponential distribution generator
 */
accum	exponential_dist_variate( uniform_rng uni_rng, uint32_t* seed_arg );


// Returns standard Gaussian deviate 
// translation of NR in C version of Box-Muller
accum gaussian_dist_variate( uniform_rng uni_rng, uint32_t* seed_arg );


// Returns Poisson variate using Knuth's method
// O(n) for returned value so don't use for large lambda
uint32_t poisson_dist_variate( uniform_rng uni_rng, uint32_t* seed_arg, accum lambda );


// Use this version for Poisson with pre-calculated exp( -lambda ) for speed gain
uint32_t poisson_dist_variate_exp_minus_lambda( uniform_rng uni_rng, uint32_t* seed_arg, 
																 unsigned long fract exp_minus_lambda );


#endif 	// include guard
