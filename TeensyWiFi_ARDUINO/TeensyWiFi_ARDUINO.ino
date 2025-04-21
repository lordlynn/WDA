/***************************************************************************
 * Title: Main.cpp
 * Author: Zac Lynn
 * 
 * Description: This program uses the ADC and UART to record EMG data
 *    From Myoware2.0 sensors and report it wirelessly using the 
 *    WizFi360.
 **************************************************************************/        
#include <Arduino.h>
#include "MQTT.h"
#include "dataBuffer.h"
#include <TimeLib.h>

/***************************************************************** 
 * Max char limit = 2048 bytes and data len must be divisible by 2  
 *  timestamp - 2 bytes
 *  data      - 2 bytes
 *  total bytes = (2 + Channels * 3) * SAMPLES
 *  Max = 2048 / (2 + Channels * 3) = 256
 * Play it safe, use 250, we are guaranteed to be under char limit
 ****************************************************************/
#define SAMPLES 250 

/*****************************************************************
 * Data buffer memory is the size of the array of structures.
 * Try to fill ~90% of free RAM with buffer. This is probably overkill
 * Ex: Free 412kB -> buffer size = 412kB * 0.9 / 8 bytes = 46350
 * Play it safe and round down to 45k. ~360kB for buffer.
 ****************************************************************/
dataBuffer buffer = dataBuffer(45000, 3);
MQTT mqtt;                                                                              // Setup MQTT object. No constructer, but we will read some class variables
IntervalTimer dataCaptureInt;                                                           // Used to interrupt every sample period to record individual samples
IntervalTimer endCaptureInt;                                                            // Used to interrupt at end of test to stop sampling
uint8_t ch[] = {14, 15, 17};                                                            // Pin numbers to use for CH1-CH3
struct sample dataToPush;                                                               // Holds the current sample we want to push to buffer
uint16_t relativeTime = 0;                                                              // Holds relative time, number of interrupts that have occurred

void sendDataToServer();                                                                // Pops data from buffer and sends to core application
void sendEndOfTest();                                                                   // Send the end of test message to core application
void startSampling();                                                                   // Blocks until start message, then enables interrupts
void takeSample();                                                                      // ISR used to record individual samples
void endSampling();                                                                     // ISR used to end data capture
void GPIO_IRQ(void);                                                                    // ISR used to syncronize RTC time


void setup() {
  Serial.begin(1000000);                                                                // Serial for communicating with PC for debugging purposes
  Serial1.begin(1500000);                                                               // Serial1 for communicating with WizFi360

  Serial.println("INIT");

  mqtt.initMQTT();                                                                      // Connect to broker, subscribe to topics

  Serial.println("Pinging server...");            
  mqtt.pingServer();                                                                    // Send ping to confirm connection with core application
  mqtt.sendTime();                                                                      // Once connected to core application, send RTC time

  pinMode(4, INPUT_PULLUP);                                                             // Input pin for RTC
  attachInterrupt(4, GPIO_IRQ, FALLING);                                                // Interrupt when there is a falling edge detected for RTC

  Serial.println("Waiting for start signal...");
  
  startSampling();                                                                      // This will block until config is received
}


void loop() {
  if (mqtt.isEnabled) {                                                                 // -- If data capture should be running
    sendDataToServer();                                                                 // Try to pop samples off buffer and send
  }
  else {                                                                                // -- If data capture has ended
    Serial.printf("Sample Count = %d\n", mqtt.count);                                   

    while (buffer.isEmpty == false) {                                                   // Read and send buffer until empty
      sendDataToServer();  
    }

    Serial.printf("TEST ENDED\n");
    sendEndOfTest();                                                                    // Send "END" to core application

    Serial.println("Pinging server...");                                                // Start process over again
    mqtt.pingServer();                                                                  // Confrim there is still a connection to core application
    mqtt.sendTime();                                                                    // Send our RTC time
    
    Serial.println("Waiting for start signal...");
    startSampling();                                                                    // Block until config is received
  }
}


void GPIO_IRQ(void) {
  Teensy3Clock.set(0);                                                                  // Set the RTC time to 0
  Serial.println("RTC has been reset...");
  detachInterrupt(4);                                                                   // Detach interrupt after it runs once to prevent switch bounce from running this multiple times
}


void sendDataToServer() {
  int numPopped = 0;
  char *strPtr;

  strPtr = buffer.pop(SAMPLES, &numPopped);                                             // Take samples out of buffer 

  mqtt.publishStr(strPtr, numPopped * buffer.sampleBytes);                              // Send data to core application
  
  free(strPtr);                                                                         // Free dynamic memory so we don't leak

  if (buffer.sampleBytes * numPopped < 400) {                                           // If we just sent less than 400 bytes
    delay(100);                                                                         // Delay a little since transfer is more efficient with more data
    /*************************************************************
     * Sample Frequency can be 1kHz to 2kHz
     * Bytes per sample can be 4 to 8
     * We want a minimum 400 bytes of data with 1 ch @ 1kHz
     * So we should delay for:
     * 400 bytes / 4 bytes * (1 / 1kHz) = 100ms
     *
     * Worst case is 3 channels @ 2kHz:
     * 100ms * 2kHz * 8 bytes = 1600 bytes
     *
     * Both values are less than max transfer of 2k so wont back 
     * up the bufer by delaying.
     ************************************************************/
  }
}


void sendEndOfTest() {
  char end[] = "END";
  mqtt.publishStr(end, 3);
  relativeTime = 0;                                                                     // Reset sample counter
}


void startSampling() {
  mqtt.waitForStart();

  Serial.printf("Time: %d\n", mqtt.startTime);
  buffer.reset(mqtt.numChannels);                                                       // Reset buffer with new ch number
                                       
  while (Teensy3Clock.get() <= mqtt.startTime);                                         // Delay until start time

  dataCaptureInt.begin(takeSample, mqtt.samplePeriod);                                  // Start Data capture interrupts
  endCaptureInt.begin(endSampling, mqtt.testLen);
}


void endSampling() {                                                                    // Runs when data capture time has expired
  dataCaptureInt.end();                                                                 // Stop interrupts
  endCaptureInt.end();   
  mqtt.isEnabled = 0;
}


void takeSample() {
  dataToPush.time = relativeTime++;                                                     // Increment time

  dataToPush.ch1 = analogRead(ch[0]);                                                   // Always reach CH 1

  if (mqtt.numChannels > 1)                                                             // Check if need to read CH 2
    dataToPush.ch2 = analogRead(ch[1]);

  if (mqtt.numChannels > 2)                                                             // Check if need to read CH 3
  dataToPush.ch3 = analogRead(ch[2]);
    
  mqtt.count += mqtt.numChannels;                                                       // Add the number of channels to total sample recorded (USED FOR DEBUGGING)

  buffer.push(dataToPush);                                                              // Add new data to the buffer
}