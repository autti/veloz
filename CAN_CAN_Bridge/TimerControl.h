#ifndef _TIMERCONTROL_
#define _DUECANLAYER_

struct Timer
{
  int  nCount;
  bool bStart;
  bool bExpired;
};

#define TIMERFREQUENCY                      1000    // Time = 1 sec / TIMERFREQUENCY
#define ACTIVITY_PULSE                      5       // Activity LED pulse duration ms
#define TIMER_RATE_LED_BLINK                1

#define TIMERS                              1       // Number of timers
#define pTimerLEDs                          pTimer[0]

#endif
