#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pstat.h"
#include "user/user.h"

int
main(int argc, char *argv[])
{
  struct pstat st;
  int n = 100;
  volatile int x = 0;

  if (argc > 1)
    n = atoi(argv[1]);

  for (int i = 0; i < n; i++)
    for (int j = 0; j < 1000000; j++)
      x++;

  getpinfo(getpid(), &st);
  printf("pid=%d total=%d first_run=%d switches=%d\n",
         st.pid, st.total_ticks, st.first_run, st.ctx_switches);
  exit(0);
}
