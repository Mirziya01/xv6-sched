#ifndef _PSTAT_H_
#define _PSTAT_H_

struct pstat {
  int pid;
  int level;
  int ticks_at_level;
  int total_ticks;
  int arrival;
  int first_run;
  int finish;
  int ctx_switches;
};

#endif
