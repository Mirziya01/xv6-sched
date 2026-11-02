#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pstat.h"
#include "user/user.h"

int
main(void)
{
  struct pstat st;

  if (getpinfo(getpid(), &st) < 0) {
    printf("getpinfo failed\n");
    exit(1);
  }
  printf("pid=%d level=%d ticks_at_level=%d total=%d\n",
         st.pid, st.level, st.ticks_at_level, st.total_ticks);
  printf("arrival=%d first_run=%d finish=%d switches=%d\n",
         st.arrival, st.first_run, st.finish, st.ctx_switches);
  exit(0);
}
