// -----------------------------------------------------------------------------------------------
// ARDUINO DUE - Timer Control Functions
// -----------------------------------------------------------------------------------------------
// Copyright (c) 2016 Copperhill Technologies Corporation.  All right reserved.

#include <Arduino.h>
#include "TimerControl.h"

// Function declarations
void TimerInit(void);
void TimerControl(void);
void startTimer(Tc *tc, uint32_t channel, IRQn_Type irq, uint32_t frequency);
void TimerStart(struct Timer* pTimer, int nCount);
void TimerReset(struct Timer* pTimer);

// Timer structure
struct Timer pTimer[TIMERS];

// ------------------------------------------------------------------------
// Initialize the Timer Control
// ------------------------------------------------------------------------
void TimerInit(void)
{
  // Initialize the timer arrays
  for(int nIndex = 0; nIndex < TIMERS; nIndex++)
  {
    pTimer[nIndex].nCount = 0;
    pTimer[nIndex].bStart = false;
    pTimer[nIndex].bExpired = false;

  }// end for

  // Set up the timer interrupt
  startTimer(TC1, 0, TC3_IRQn, TIMERFREQUENCY); //TC1 channel 0, the IRQ for that channel and the desired frequency

}// end TimerInit

// ------------------------------------------------------------------------
// Timer Control (Interrupt Service Routine)
// ------------------------------------------------------------------------
void TimerControl(void)
{
  // Declarations
  int nIndex;

  // Check all timers
  for(nIndex = 0; nIndex < TIMERS; nIndex++)
  {
    if(pTimer[nIndex].bStart == true && pTimer[nIndex].bExpired == false)
      if(--pTimer[nIndex].nCount == 0)
        pTimer[nIndex].bExpired = true;

  }// end for

}// end TimerControl

// ------------------------------------------------------------------------
// Timer Start
// ------------------------------------------------------------------------
void TimerStart(struct Timer* pTimer, int nCount)
 {
   pTimer->nCount = nCount;
   pTimer->bStart = true;
   pTimer->bExpired = false;

 }// end TimerStart

// ------------------------------------------------------------------------
// Timer Reset
// ------------------------------------------------------------------------
void TimerReset(struct Timer* pTimer)
{
  pTimer->nCount = 0;
  pTimer->bStart = false;
  pTimer->bExpired = false;

}// end TimerReset

// ------------------------------------------------------------------------
// Timer Interrupt Setup for Arduino Due
// ------------------------------------------------------------------------
// Reference: http://forum.arduino.cc/index.php?topic=130423.0

void TC3_Handler(void)
{
  TC_GetStatus(TC1, 0);
  TimerControl();
}

void startTimer(Tc *tc, uint32_t channel, IRQn_Type irq, uint32_t frequency)
{
  pmc_set_writeprotect(false);
  pmc_enable_periph_clk((uint32_t)irq);
  TC_Configure(tc, channel, TC_CMR_WAVE | TC_CMR_WAVSEL_UP_RC | TC_CMR_TCCLKS_TIMER_CLOCK4);  
  uint32_t rc = VARIANT_MCK/128/frequency; //128 because we selected TIMER_CLOCK4 above
  TC_SetRA(tc, channel, rc/2); //50% high, 50% low
  TC_SetRC(tc, channel, rc);
  TC_Start(tc, channel);
  tc->TC_CHANNEL[channel].TC_IER=TC_IER_CPCS;
  tc->TC_CHANNEL[channel].TC_IDR=~TC_IER_CPCS;
  NVIC_EnableIRQ(irq);
}

