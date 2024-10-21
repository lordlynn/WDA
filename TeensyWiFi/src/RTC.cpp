/***********************************************************************
 * Title: RTC.cpp
 * Author: Zac Lynn
 * 
 * Description: This class impements functions to use the Teensy4.1 RTC.
 * 
 * Adapted from: https://github.com/manitou48/teensy4/blob/master/rtc.ino
 **********************************************************************/
#include "RTC.h"

void RTC::init() {
  CCM_CCGR2 |= CCM_CCGR2_IOMUXC_SNVS(CCM_CCGR_ON);
  SNVS_LPGPR = SNVS_DEFAULT_PGD_VALUE;
  SNVS_LPSR = SNVS_LPSR_PGD_MASK;

  SNVS_LPCR |= 1;                                                                       // Start RTC
  while (!(SNVS_LPCR & 1));
}


void RTC::rtc_set_time(uint32_t secs) {

  SNVS_LPCR &= ~1;                                                                      // Stop RTC
  while (SNVS_LPCR & 1);
  SNVS_LPSRTCMR = (uint32_t)(secs >> 17U);                                              // Set RTC value
  SNVS_LPSRTCLR = (uint32_t)(secs << 15U);
  SNVS_LPCR |= 1;                                                                       // Start RTC
  while (!(SNVS_LPCR & 1));
}


uint32_t RTC::miliSec() {
  uint32_t miliSeconds = 0;
  uint32_t tmp = 0;

  /* Do consecutive reads until value is correct.
   * Datasheet specifies this and says it should
   * take at most 3 reads to get the correct time.
   */
  do
  {
    miliSeconds = tmp;
    tmp = (SNVS_LPSRTCLR & 0xFFFF);
  } while (tmp != miliSeconds);

  miliSeconds = (miliSeconds * 1000.0) / 32768.0;                                       // Convert from clock cycles to miliseconds
   
  return (miliSeconds >= 1000) ? (miliSeconds - 1000) : miliSeconds;                    // Lower 16-bit can count up to 2000ms                            
}


uint32_t RTC::secs() {
  uint32_t seconds = 0;
  uint32_t tmp = 0;

  do
  {
    seconds = tmp;
    tmp = (SNVS_LPSRTCMR << 17U) | (SNVS_LPSRTCLR >> 15U);
  } while (tmp != seconds);

  return seconds;
}