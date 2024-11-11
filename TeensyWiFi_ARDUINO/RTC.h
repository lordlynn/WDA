#include "imxrt.h"
#include <Arduino.h>
#include <time.h>
#pragma once

#define SNVS_DEFAULT_PGD_VALUE (0x41736166U)
#define SNVS_LPSR_PGD_MASK     (0x8U)


class RTC {
  public:
    void init();
    void rtc_set_time(uint32_t secs);
    
    uint32_t miliSec();
    uint32_t secs();

  private:
    
};