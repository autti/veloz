// CAN Layer functions
// -----------------------------------------------------------------------------------------------
#include "DueCANLayer.h"
extern byte canInit(byte cPort, long lBaudRate, int nTxMailboxes);
extern byte canTx(byte cPort, long lMsgID, bool bExtendedFormat, byte* cData, byte cDataLen);
extern byte canRx(byte cPort, long* lMsgID, bool* bExtendedFormat, byte* cData, byte* cDataLen);

// Timer functions
// -----------------------------------------------------------------------------------------------
#include "TimerControl.h"
extern void TimerInit(void);
extern void TimerControl(void);
extern void TimerStart(struct Timer* pTimer, int nCount);
extern void TimerReset(struct Timer* pTimer);
extern struct Timer pTimer[];

// CAN Bus Data Mapping
// -----------------------------------------------------------------------------------------------
struct Mapping
{
  byte cReceivingPort;             // 0/1
  long lReceivingMsgID;
  long lTransmittedMsgID;
};

struct Mapping CAN_DataMapping[] = {
  // cReceivingPort, lReceivingMsgID, lTransmittedMsgID
     0,              0x180,           0x280,
     0,              0x300,           0x200,
     0,              0x200,           0x201,
     1,              0x280,           0x180,
     1,              0x200,           0x300,
     1,              0x201,           0x200,
     255,            0x000,           0x000   // End of Table
};

int nMappingEntries = 0;   // Will be determined in setup()

// Internal functions
// -----------------------------------------------------------------------------------------------
void LEDControl(void);

// Module variables
// -----------------------------------------------------------------------------------------------
int TimerActivity_CAN0 = 0;
int TimerActivity_CAN1 = 0;

int LED1 = 14;
int LED2 = 15;

int nTxMailboxes = 3; // Equal portion between transmission and reception

void setup()
{
  // Set the serial interface baud rate
  Serial.begin(115200);

  // Initialzie the timer control; also resets all timers
  TimerInit();

  // Determine simulation entries
  nMappingEntries = 0;
  while(1)
  {
    if(CAN_DataMapping[nMappingEntries].cReceivingPort == 0 
    || CAN_DataMapping[nMappingEntries].cReceivingPort == 1)
      nMappingEntries++;
    else
      break;
  }

  // Initialize the outputs for the LEDs
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  
  // Initialize both CAN controllers
  if(canInit(0, CAN_BPS_500K, nTxMailboxes) == CAN_OK)
    Serial.print("CAN0: Initialized Successfully.\n\r");
  else
    Serial.print("CAN0: Initialization Failed.\n\r");
  
  if(canInit(1, CAN_BPS_500K, nTxMailboxes) == CAN_OK)
    Serial.print("CAN1: Initialized Successfully.\n\r");
  else
    Serial.print("CAN1: Initialization Failed.\n\r");
  
}// end setup

void loop()
{
  // Declarations
  byte cPort, cTxPort;
  long lMsgID;
  bool bExtendedFormat;
  byte cData[8];
  byte cDataLen;
  String canMessage="";
  
  // Start timer for LED indicators
  TimerStart(&pTimerLEDs, TIMER_RATE_LED_BLINK);

  while(1)  // Endless loop
  {
    // Control LED status according to CAN traffic
    LEDControl();

    // Check for received CAN messages
    for(cPort = 0; cPort <= 1; cPort++)
    {
      if(canRx(cPort, &lMsgID, &bExtendedFormat, &cData[0], &cDataLen) == CAN_OK)
      {
        // concatenate string for can message
        // concatenation of message is too slow for 2 can ports
        if(cPort == 1){
        canMessage="";
        canMessage.concat("can@");
        canMessage.concat(cPort);
        canMessage.concat("@");
        canMessage.concat(lMsgID);
        canMessage.concat("@");
        canMessage.concat(cData[0]);
        canMessage.concat("#");
        canMessage.concat(cData[1]);
        canMessage.concat("#");
        canMessage.concat(cData[2]);
        canMessage.concat("#");
        canMessage.concat(cData[3]);
        canMessage.concat("#");
        canMessage.concat(cData[4]);
        canMessage.concat("#");
        canMessage.concat(cData[5]);
        canMessage.concat("#");
        canMessage.concat(cData[6]);
        canMessage.concat("#");
        canMessage.concat(cData[7]);
        Serial.println(canMessage);
        }

        // Scan through the mapping list
        
        //for(int nIndex = 0; nIndex < nMappingEntries; nIndex++)
        //{
          // filter can messages using ID
          //if(cPort == CAN_DataMapping[nIndex].cReceivingPort
          //&& lMsgID == CAN_DataMapping[nIndex].lReceivingMsgID)
          //{
          //  cTxPort = 0;
          //  if(cPort == 0) cTxPort = 1;
              
            //if(canTx(cTxPort, CAN_DataMapping[nIndex].lTransmittedMsgID, bExtendedFormat, &cData[0], cDataLen) == CAN_ERROR)
            //if(canTx(cTxPort, CAN_DataMapping[nIndex].lReceivingMsgID, bExtendedFormat, &cData[0], cDataLen) == CAN_ERROR)
            //  Serial.println("Transmision Error.");
            
         // }// end if
          
        //}// end for
        cTxPort = 0;
        if(cPort == 0) cTxPort = 1;
        if(canTx(cTxPort, lMsgID, bExtendedFormat, &cData[0], cDataLen) == CAN_ERROR)
          Serial.println("Transmision Error.");
      }// end if

    }// end for
    
  }// end while

}// end loop

// ------------------------------------------------------------------------
// LED Data Traffic
// ------------------------------------------------------------------------
// Note: CAN0 --> LED1
//       CAN1 --> LED2
//
void LEDControl(void)
{
    if(pTimerLEDs.bExpired == true)
    {
      // Restart the timer
      TimerStart(&pTimerLEDs, TIMER_RATE_LED_BLINK);

      // Check for activity on CAN0
      if(TimerActivity_CAN0 > 0)
      {
        TimerActivity_CAN0--;
        digitalWrite(LED1, HIGH);
      }// end if
      else
        digitalWrite(LED1, LOW);

      // Check for activity on CAN1
      if(TimerActivity_CAN1 > 0)
      {
        TimerActivity_CAN1--;
        digitalWrite(LED2, HIGH);
      }// end if
      else
        digitalWrite(LED2, LOW);

    }// end if

}// end LEDControl

