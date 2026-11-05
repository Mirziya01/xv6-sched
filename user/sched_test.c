#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/pstat.h"
#include "user/user.h"

static void
work(int n)
{
  volatile int x = 0;
  for (int i = 0; i < n; i++)
    for (int j = 0; j < 1000000; j++) {
      x++;
      x; // to avoid compiler warnings of 'unused var'
    }
}

int
main(int argc, char *argv[])
{
  int nproc = 4;
  int len = 400; // about 20 ticks of CPU when run alone
  
  if (argc > 1) // first arg: number of processes
    nproc = atoi(argv[1]);
  if (argc > 2) // second arg: number of ticks
    len = atoi(argv[2]);
  if (nproc < 1 || nproc > 30) {
    printf("usage: sched_test [nproc 1-30] [length (ticks*20)]\n");
    exit(1);
  }

  int start = uptime();
  for (int i = 0; i < nproc; i++) {
    int pid = fork();
    if (pid < 0) {
      printf("fork failed\n");
      exit(1);
    }
    if (pid == 0) {
      work(len);
      exit(0);
    }
  }

  printf("pid\tarrive\tfirst\tfinish\tcpu\tturn\tresp\twaiting\tswitches\n");
  for (int i = 0; i < nproc; i++) {
    struct pstat st;
    int status;
    int pid = waitpinfo(&status, &st);
    if (pid < 0)
      break;
    int turn = st.finish - st.arrival;
    int resp = st.first_run - st.arrival;
    int waiting = turn - st.total_ticks;
    printf("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n", pid, st.arrival,
           st.first_run, st.finish, st.total_ticks, turn, resp, waiting,
           st.ctx_switches);
  }

  int elapsed = uptime() - start;
  printf("elapsed=%d ticks, throughput=%d jobs/100 ticks\n", elapsed,
         nproc * 100 / elapsed);
  exit(0);
}
