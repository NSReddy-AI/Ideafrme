/* Application-owned ABI wrapper; LodePNG is compiled unmodified alongside it.
 * No WASI or host functions. Only static RGBA8/RGB8 noninterlaced PNG is admitted.
 */
#include <stdint.h>
#include <stdlib.h>
#include "lodepng.h"
#define INPUT_MAX (8u*1024u*1024u)
#define PIXELS_MAX (2048u*2048u)
static unsigned char input[INPUT_MAX];
static unsigned char *pixels;
static unsigned width, height;
static uint32_t be32(const unsigned char *p) {
  return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];
}
static int tag(const unsigned char *p,const char *s) {
  return p[0]==s[0]&&p[1]==s[1]&&p[2]==s[2]&&p[3]==s[3];
}
unsigned input_ptr(void) { return (unsigned)(uintptr_t)input; }
unsigned pixels_ptr(void) { return (unsigned)(uintptr_t)pixels; }
unsigned image_width(void) { return width; }
unsigned image_height(void) { return height; }
unsigned decode_png(unsigned size) {
  static const unsigned char sig[8]={137,80,78,71,13,10,26,10};
  if(size<45||size>INPUT_MAX)return 1001;
  for(unsigned i=0;i<8;i++)if(input[i]!=sig[i])return 1002;
  unsigned pos=8,ids=0,ended=0;
  while(pos<size) {
    if(size-pos<12)return 1003;
    unsigned n=be32(input+pos); const unsigned char *t=input+pos+4;
    if(n>size-pos-12)return 1004;
    if(lodepng_crc32(t,n+4)!=be32(input+pos+8+n))return 1005;
    if(pos==8) {
      if(!tag(t,"IHDR")||n!=13)return 1006;
      width=be32(t+4);height=be32(t+8);
      if(!width||!height||width>2048||height>2048||width>PIXELS_MAX/height)return 1007;
      if(t[12]!=8||(t[13]!=2&&t[13]!=6)||t[14]||t[15]||t[16])return 1008;
    } else if(tag(t,"IDAT")) {if(ended)return 1009;ids++;}
    else if(tag(t,"IEND")) {if(n||!ids||pos+12!=size)return 1010;ended=1;}
    else return 1011; /* Metadata, APNG, palette, active/unknown chunks refused. */
    pos+=n+12;
  }
  if(!ended)return 1012;
  LodePNGState state;lodepng_state_init(&state);
  state.decoder.zlibsettings.max_output_size=(size_t)height*(1u+width*4u);
  unsigned w=0,h=0;unsigned e=lodepng_decode(&pixels,&w,&h,&state,input,size);
  lodepng_state_cleanup(&state);
  if(e)return e;
  if(w!=width||h!=height)return 1013;
  return 0;
}
/* Explicit tests exercise the same fuel and linear-memory ceiling. Never exposed
 * through the application decoder API. No extra modules/imports are accepted. */
unsigned test_memory_limit(void) {return __builtin_wasm_memory_grow(0,4097);}
unsigned test_fuel(void) {volatile unsigned n=0;for(;;)n++;}
__attribute__((noinline)) unsigned test_stack(unsigned n) {
  volatile unsigned a[128];a[0]=n;
  return n ? test_stack(n-1)+a[0] : a[0];
}
