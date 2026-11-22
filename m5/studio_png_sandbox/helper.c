/* Trusted minimal Wasmtime embedding. Receives PNG on stdin, returns header+RGBA.
 * No linker, WASI context, host imports, callbacks, network or scratch file APIs.
 */
#include <wasmtime.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <sys/resource.h>
#include <mach/mach.h>
#define GUEST_MAX (64u*1024u*1024u)
#define INPUT_MAX (8u*1024u*1024u)
#define MODULE_MAX (2u*1024u*1024u)
static unsigned char input[INPUT_MAX+1], module_bytes[MODULE_MAX+1];
static void fail(const char *reason) { fprintf(stderr,"PNG_HELPER_REFUSED:%s\n",reason);exit(2); }
static void checked(wasmtime_error_t *e,wasm_trap_t *t) {
  if(e){wasm_name_t msg;wasmtime_error_message(e,&msg);fprintf(stderr,"%.*s\n",(int)(msg.size<512?msg.size:512),msg.data);wasm_name_delete(&msg);wasmtime_error_delete(e);fail("runtime-error");}
  if(t){wasm_name_t msg;wasm_trap_message(t,&msg);fprintf(stderr,"%.*s\n",(int)(msg.size<512?msg.size:512),msg.data);wasm_name_delete(&msg);wasm_trap_delete(t);fail("wasm-trap");}
}
static void limit(int which,rlim_t n) {struct rlimit l={n,n};if(setrlimit(which,&l))fail("rlimit");}
static unsigned threads(void) {
  thread_act_array_t list;mach_msg_type_number_t n=0;
  if(task_threads(mach_task_self(),&list,&n)!=KERN_SUCCESS)fail("thread-accounting");
  for(unsigned i=0;i<n;i++)mach_port_deallocate(mach_task_self(),list[i]);
  vm_deallocate(mach_task_self(),(vm_address_t)list,n*sizeof(thread_t));return n;
}
static wasmtime_extern_t lookup(wasmtime_context_t *c,wasmtime_instance_t *i,const char *n) {
  wasmtime_extern_t e;if(!wasmtime_instance_export_get(c,i,n,strlen(n),&e))fail("missing-export");return e;
}
static uint32_t call(wasmtime_context_t *c,wasmtime_instance_t *i,const char *n,int argc,uint32_t x) {
  wasmtime_extern_t e=lookup(c,i,n);if(e.kind!=WASMTIME_EXTERN_FUNC)fail("function-type");
  wasmtime_val_t a={.kind=WASMTIME_I32,.of.i32=(int32_t)x},r;wasm_trap_t *t=NULL;
  wasmtime_error_t *err=wasmtime_func_call(c,&e.of.func,&a,argc,&r,1,&t);checked(err,t);
  if(r.kind!=WASMTIME_I32)fail("result-type");return (uint32_t)r.of.i32;
}
int main(int argc,char **argv) {
  if(argc!=3)fail("arguments");
  limit(RLIMIT_CPU,15);limit(RLIMIT_FSIZE,0);limit(RLIMIT_CORE,0);limit(RLIMIT_NOFILE,16);limit(RLIMIT_STACK,8u*1024u*1024u);
  alarm(15);
  FILE *f=fopen(argv[1],"rb");if(!f)fail("module-open");size_t m=fread(module_bytes,1,sizeof(module_bytes),f);fclose(f);
  if(!m||m>MODULE_MAX)fail("module-size");
  wasm_config_t *cfg=wasm_config_new();
  wasmtime_config_consume_fuel_set(cfg,true);
  wasmtime_config_max_wasm_stack_set(cfg,512u*1024u);
  wasmtime_config_parallel_compilation_set(cfg,false);
  /* Avoid Wasmtime's default Mach exception-handler service thread. */
  wasmtime_config_macos_use_mach_ports_set(cfg,false);
  wasmtime_config_concurrency_support_set(cfg,false);
  wasmtime_config_wasm_threads_set(cfg,false);
  wasmtime_config_shared_memory_set(cfg,false);
  wasmtime_config_wasm_multi_memory_set(cfg,false);
  wasmtime_config_wasm_memory64_set(cfg,false);
  wasmtime_config_wasm_component_model_set(cfg,false);
  wasmtime_config_wasm_gc_set(cfg,false);
  wasmtime_config_wasm_function_references_set(cfg,false);
  wasmtime_config_gc_support_set(cfg,false);
  wasmtime_config_memory_reservation_set(cfg,GUEST_MAX);
  wasmtime_config_memory_reservation_for_growth_set(cfg,0);
  wasm_engine_t *engine=wasm_engine_new_with_config(cfg);if(!engine)fail("engine");
  wasmtime_module_t *mod=NULL;checked(wasmtime_module_new(engine,module_bytes,m,&mod),NULL);
  wasm_importtype_vec_t imports;wasmtime_module_imports(mod,&imports);size_t count=imports.size;wasm_importtype_vec_delete(&imports);
  if(count)fail("imports-forbidden");
  wasmtime_store_t *store=wasmtime_store_new(engine,NULL,NULL);
  wasmtime_store_limiter(store,GUEST_MAX,64,1,1,1);
  wasmtime_context_t *ctx=wasmtime_store_context(store);
  checked(wasmtime_context_set_fuel(ctx,5000000000ULL),NULL);
  wasmtime_instance_t instance;wasm_trap_t *trap=NULL;
  wasmtime_error_t *err=wasmtime_instance_new(ctx,mod,NULL,0,&instance,&trap);checked(err,trap);
  if(threads()!=1)fail("unexpected-runtime-threads");
  if(!strcmp(argv[2],"probe-memory")) {
    unsigned result=call(ctx,&instance,"test_memory_limit",0,0);
    if(result!=UINT32_MAX)fail("memory-limit-not-enforced");
    puts("MEMORY_GROW_REFUSED");return 0;
  }
  if(!strcmp(argv[2],"probe-fuel")) {call(ctx,&instance,"test_fuel",0,0);fail("fuel-not-enforced");}
  if(!strcmp(argv[2],"probe-stack")) {call(ctx,&instance,"test_stack",1,1000000);fail("stack-not-enforced");}
  if(strcmp(argv[2],"decode"))fail("mode");
  size_t n=fread(input,1,sizeof(input),stdin);if(n>INPUT_MAX||ferror(stdin))fail("input-size");
  uint32_t p=call(ctx,&instance,"input_ptr",0,0);
  wasmtime_extern_t e=lookup(ctx,&instance,"memory");if(e.kind!=WASMTIME_EXTERN_MEMORY)fail("memory-type");
  size_t memsize=wasmtime_memory_data_size(ctx,&e.of.memory);
  if(p>memsize||n>memsize-p)fail("input-bounds");
  memcpy(wasmtime_memory_data(ctx,&e.of.memory)+p,input,n);
  if(call(ctx,&instance,"decode_png",1,(uint32_t)n))fail("png-rejected");
  uint32_t w=call(ctx,&instance,"image_width",0,0),h=call(ctx,&instance,"image_height",0,0),out=call(ctx,&instance,"pixels_ptr",0,0);
  if(!w||!h||w>2048||h>2048)fail("dimensions");
  size_t bytes=(size_t)w*h*4;memsize=wasmtime_memory_data_size(ctx,&e.of.memory);
  if(bytes>16u*1024u*1024u||out>memsize||bytes>memsize-out||memsize>GUEST_MAX)fail("output-bounds");
  if(threads()!=1)fail("unexpected-runtime-threads");
  struct rusage ru;if(getrusage(RUSAGE_SELF,&ru))fail("memory-accounting");
  /* ru_maxrss is bytes on Darwin. This is a measured refusal ceiling, NOT a
   * kernel RSS quota. Treat whole RSS as overhead: deliberately conservative. */
  if(ru.ru_maxrss>128u*1024u*1024u)fail("runtime-overhead-ceiling");
  fprintf(stdout,"PNG_RGBA_V1 %u %u %zu %ld %u\n",w,h,memsize,ru.ru_maxrss,threads());
  if(fwrite(wasmtime_memory_data(ctx,&e.of.memory)+out,1,bytes,stdout)!=bytes||fflush(stdout))fail("output-write");
  wasmtime_store_delete(store);wasmtime_module_delete(mod);wasm_engine_delete(engine);return 0;
}
