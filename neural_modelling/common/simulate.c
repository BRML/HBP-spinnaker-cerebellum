

#include "simulate.h"

#include "stdfix-full-iso.h"
#include "stdfix-exp.h"

//#include "sark.h"

#include "math.h" 

/*
	
	By Michael Hopkins, Manchester University
	
	For all of these, to get a high resolution fixed-point number in (0,1) that uses the entire 
	generator space use ulrbits() around return value to give a 32-bit unsigned long fract
	
	Also other options to get a 16-bit unsigned fract by taking 16 MSBs of result and urbits()
	
	If floating point available then multiply by 2.32830643653869628906e-10
	
	spin1_rand() takes 134.9 nanosecs (i.e. 27 ticks) per call
	
*/
/*
   WELL 1024a long cycle generator (2^1024 - 1) from L'Ecuyer & Panneton
   
   Better equi-distribution and warm-up performance than Mersenne Twister, and faster
   
   294.9 nanosecs (i.e. 59 ticks) per call
   
*/
#define R 32

// NB the global state vector for WELL1024a_simp() is defined here as a file static
static uint32_t STATE[R];

#define W 32
#define M1 3
#define M2 24
#define M3 10

#define MAT0POS(t,v) (v^(v>>t))
#define MAT0NEG(t,v) (v^(v<<(-(t))))
#define Identity(v) (v)

#define V0            STATE[state_i                   ]
#define VM1           STATE[(state_i+M1) & 0x0000001fU]
#define VM2           STATE[(state_i+M2) & 0x0000001fU]
#define VM3           STATE[(state_i+M3) & 0x0000001fU]
#define VRm1          STATE[(state_i+31) & 0x0000001fU]
#define newV0         STATE[(state_i+31) & 0x0000001fU]
#define newV1         STATE[state_i                   ]


// the initialiser function that MUST BE CALLED before WELL1024a_simp() is used
void init_WELL1024a_simp( void )
{
	//   state_i = 0;
	for ( int j = 0; j < R; j++ ) {
		STATE[j] = mars_kiss64_simp();  // init state vector with good generator
// io_printf( IO_STD, " %u , ", STATE[j] );	
		}
// io_printf( IO_STD, "\n");	
}


// the WELL generator itself
uint32_t WELL1024a_simp( void )
{
	static uint32_t state_i = 0;
	uint32_t 			z0, z1, z2;
	
	z0    = VRm1;
	z1    = Identity(V0)       ^ MAT0POS (8, VM1);
	z2    = MAT0NEG (-19, VM2) ^ MAT0NEG(-14,VM3);
	newV1 = z1                 ^ z2; 
	newV0 = MAT0NEG (-11,z0)   ^ MAT0NEG(-7,z1)    ^ MAT0NEG(-13,z2);
	state_i = (state_i + 31) & 0x0000001fU;
	
  	return STATE[state_i];
}


// MUST USE THIS before working with proposed seed for the first time
void		validate_WELL1024a_seed( WELL1024a_seed_t seed )
{
	seed[33] = 0;
}

#define state_i STATE[33] // need to store original static variable as extra element of seed 

// the WELL generator for custom seed - STATE in function argument replaces file static version
uint32_t WELL1024a_seed( WELL1024a_seed_t STATE )
{
//	static uint32_t 	state_i = 0;  // now stored in 33rd element of seed
	uint32_t 			z0, z1, z2;
	
	z0    = VRm1;
	z1    = Identity(V0)       ^ MAT0POS (8, VM1);
	z2    = MAT0NEG (-19, VM2) ^ MAT0NEG(-14,VM3);
	newV1 = z1                 ^ z2; 
	newV0 = MAT0NEG (-11,z0)   ^ MAT0NEG(-7,z1)    ^ MAT0NEG(-13,z2);
	state_i = (state_i + 31) & 0x0000001fU;
	
  	return STATE[state_i];
}

#undef state_i

#undef W 
#undef R 
#undef M1 
#undef M2 
#undef M3 

#undef MAT0POS 
#undef MAT0NEG 
#undef Identity 

#undef V0       
#undef VM1     
#undef VM2     
#undef VM3       
#undef VRm1      
#undef newV0    
#undef newV1   

// end of L'Ecuyer WELL1024a definition



/* 
	Implementation of a Marsaglia 32-bit KISS generator which uses no multiply instructions
	
   209.9 nanosecs (i.e. 42 ticks) per call
   
*/ 
uint32_t mars_kiss32( void )
{
	static uint32_t x = 123456789, y = 234567891, z = 345678912, w = 456789123, c = 0; /* Seed variables */ 
	int32_t t; 

	y ^= ( y << 5 ); y ^= ( y >> 7 ); y ^= ( y << 22 ); 
	t = z + w + c; 
	z = w; 
	c = t < 0; 
	w =  t & 2147483647; 
	x += 1411392427; 

	return (uint32_t) x + y + w; 
}


/* 
	Implementation of Marsaglia JKISS RNG uses 64-bit value and 2x multiplies
	
	219.9 nanosecs (i.e. 44 ticks) per call
	
*/ 
uint32_t mars_kiss64_simp( void )
{
	static uint32_t x = 123456789, y = 987654321, z = 43219876, c = 6543217; /* Seed variables */ 
	uint64_t t; 

	x = 314527869 * x + 1234567; 
	y ^= y << 5; y ^= y >> 7; y ^= y << 22; 
	t = 4294584393ULL * z + c; 
	c = t >> 32; 
	z = t; 

	return (uint32_t) x + y + z; 
}


#define x seed[0]
#define y seed[1]
#define z seed[2]
#define c seed[3]
/* 
	Custom seed version of above - need to create & validate 128 bit seed before use
*/ 
uint32_t mars_kiss64_seed( mars_kiss64_seed_t seed )
{
	uint64_t t; 

	x = 314527869 * x + 1234567; 
	y ^= y << 5; y ^= y >> 7; y ^= y << 22; 
	t = 4294584393ULL * z + c; 
	c = t >> 32; 
	z = t; 

	return (uint32_t) x + y + z; 
}
#undef x
#undef y
#undef z
#undef c


// validate seed for Marsaglia KISS 64 before it is first used
void		validate_mars_kiss64_seed( mars_kiss64_seed_t seed )
{
 	if( seed[1] == 0 ) seed[1] = 13031301;  	// y (<- seed[2]) can't be zero so set to arbitrary non-zero if so
 	
 	seed[3] = seed[3] % 698769068 + 1;			// avoid z=c=0 and make < 698769069
}


/***************************************************

	Non-uniform RNGs
	
	Being added to all the time, and updated for better speed as 
	fixed-point transcendentals and optimised multiplies become available


****************************************************/
/*
 * 	Von Neumann's exponential distribution generator
 * 
 * 	from Ripley p.230 and adapted for our types
 * 
 * 	Mean number of U(0,1) per call = 5.2
 * 
 * 	I have been lazy and copied the GOTOs, sorry!
 */
accum exponential_dist_variate( uniform_rng uni_rng, uint32_t* seed_arg  )
{
	accum 		A = 0.0k;
	uint32_t	U, U0, USTAR;

outer:	
	U = uni_rng( seed_arg ); 		
	U0 = U;

inner:
	USTAR = uni_rng( seed_arg );  
	if ( U < USTAR ) return  A + (accum) ulrbits( U0 );  // accum + (accum)[ unsigned long fract <= uint32_t ]

	U = uni_rng( seed_arg ); 
	if ( U < USTAR ) goto inner;	
	
	A += 1.0k;
	goto outer;	
}



// Returns standard gaussian deviate - my translation of NR in C
// 2 for the price of one (kind of)
accum gaussian_dist_variate( uniform_rng uni_rng, uint32_t* seed_arg )
{
	static 			bool set = false;
	static float 	gset;
	float 			fac, rsq, v1, v2;

	if  ( !set ) {
		do {

			v1 = ( uni_rng( seed_arg ) / 2147483648.0f ) - 1.0f;   // U(0,1) * 2 - 1
			v2 = ( uni_rng( seed_arg ) / 2147483648.0f ) - 1.0f;
			
			rsq = v1*v1 + v2*v2;
			
			} while ( rsq >= 1.0f || rsq == 0.0f );

		fac = sqrtf( -2.0f * logf( rsq ) / rsq );
		
		gset = v1 * fac;
		set = true;
		return (accum) v2 * fac;
		} 
	else {

		set = false;
		return (accum) gset;

		}
}


// Returns Poisson variate using Knuth's method
// O(n) for returned value so don't use for large lambda
uint32_t poisson_dist_variate( uniform_rng uni_rng, uint32_t* seed_arg, accum lambda )
{
	unsigned long fract exp_minus_lambda = (unsigned long fract) expk( -lambda );
	
	return poisson_dist_variate_exp_minus_lambda( uni_rng, seed_arg, exp_minus_lambda );
}


// when one can pre-calculate exp( -lambda ) once, use this version to save time
uint32_t poisson_dist_variate_exp_minus_lambda( uniform_rng uni_rng, uint32_t* seed_arg, 
																 unsigned long fract exp_minus_lambda )
{
	uint32_t 				k = 0, unif;
	unsigned long fract 	p = 1.0ulr, u;
	
	do {
		
		k++;
		
		unif = uni_rng( seed_arg );  	// unif is uint32_t
		
		u = ulrbits( unif );				// u is unsigned long fract
		
		p *= u;
		
		} while ( p > exp_minus_lambda );
		
	return k - 1;
}

