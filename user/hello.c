#include "kernel/types.h"
#include "user/user.h"

int main(void) {
  printf("Hello from xv6! uptime ticks: %d\n", uptime());
  exit(0);
}
