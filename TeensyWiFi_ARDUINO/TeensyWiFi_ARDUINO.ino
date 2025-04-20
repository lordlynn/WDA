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
 * Data buffer memory usage is the size of the array of structures
 * try to fill ~90% of RAM with buffer. This is probably overkill
 * Ex: Free 412kB -> buffer size = 412kB * 0.9 / 8 bytes = 46350
 * Play it safe and round down to 45k.
 ****************************************************************/
dataBuffer buffer = dataBuffer(45000, 3);

MQTT mqtt;
IntervalTimer dataCaptureInt;                                                           // Interrupt every sample period to record data
IntervalTimer endCaptureInt;                                                            // Interrupt at end of test to stop sampling
uint8_t ch[] = {14, 15, 17};                                                            // pin numbers to use for CH1-CH3
struct sample dataToPush;
uint16_t relativeTime = 0;                                                              // Holds relative time, number of interrupts that have occurred


void sendDataToServer();
void sendEndOfTest();
void startSampling();
void takeSample();
void endSampling();
void GPIO_IRQ(void);


void setup() {
  Serial.begin(1000000);                                                                // Serial for communicating with PC for debugging purposes
  Serial1.begin(1500000);                                                               // Serial1 for communicating with WizFi360

  Serial.println("INIT");

  mqtt.initMQTT();                                                                      // Connect to wifi, connect to broker, subscribe to topics

  Serial.println("Pinging server...");
  mqtt.pingServer();                                                                    
  mqtt.sendTime();                                                                      // Send RTC time

  pinMode(4, INPUT_PULLUP);                                                             // Input pin for RTC
  attachInterrupt(digitalPinToInterrupt(4), GPIO_IRQ, FALLING);                         // Interrupt when there is a falling edge detected for RTC

  Serial.println("Waiting for start signal...");
  
  startSampling();
}


void loop() {

  if (mqtt.isEnabled) {                                                                 // If data capture should be running
    sendDataToServer();
  }
  else {                                                                                // If data capture has ended
    Serial.printf("Sample Count = %d\n", mqtt.count);

    while (buffer.isEmpty == false) {                                                   // Read and send buffer until empty
      sendDataToServer();  
    }

    Serial.printf("TEST ENDED\n");
    sendEndOfTest();                                                                    // Send "END"

    Serial.println("Pinging server...");                                                // Start process over again
    mqtt.pingServer();
    mqtt.sendTime(); 
    
    Serial.println("Waiting for start signal...");
    startSampling();
  }
}


void GPIO_IRQ(void) {
  Teensy3Clock.set(0);                                                                  // Set the RTC time to 0
  Serial.println("RTC has been reset...");
  detachInterrupt(digitalPinToInterrupt(4));                                            // Detach interrupt after it runs once to prevent bouncing switch from running this multiple times
}


void sendDataToServer() {
  int numPopped = 0;
  char *strPtr;

  strPtr = buffer.pop(SAMPLES, &numPopped);

  mqtt.publishStr(strPtr, numPopped * buffer.sampleBytes);

  free(strPtr);

  if (buffer.sampleBytes * numPopped < 400) {                                          
    delay(25);                                                                          // If the buffer is mostly empty, delay a slight amount. Transfer is more efficient with more samples  
  }
}


void sendEndOfTest() {
  char end[] = "END";
  mqtt.publishStr(end, 3);
  relativeTime = 0;                                                                     // Reset Time Counter
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
    
  mqtt.count += mqtt.numChannels;                                                       // Add the number of channels to total sample recorded

  buffer.push(dataToPush);                                                              // Add new data to the buffer
}