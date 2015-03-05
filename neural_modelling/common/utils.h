
#include <stdint.h>

static inline uint32_t __hi (uint64_t x) { return ((uint32_t)(x >> 32)); }
static inline uint32_t __lo (uint64_t x) { return (__hi(x << 32));       }

// The following treats the 64-bit number as if it were 
// a 32-bit integer and a 32-bit fraction, rounding the fractional
// part.

static inline uint64_t round64 (uint64_t x)
{
  uint64_t r = (uint64_t)(__hi (x));

  if (__lo (x) >= INT32_MAX)
    r++;

  return (r);
}

// in the following we treat "y" as if it is an unsigned long fract

static inline uint64_t scale64 (uint64_t x, uint32_t y)
{
  uint64_t r;

  r = round64 ((uint64_t)(__lo (x)) * (uint64_t)(y));

  r += (uint64_t)(__hi (x)) * (uint64_t)(y);

  return (r);
}

// in the following we treat "y" as if it is an unsigned long fract

static inline uint32_t scale32 (uint32_t x, uint32_t y)
{ return ((uint32_t)(round64 ((uint64_t)(x) * (uint64_t)(y)))); }
