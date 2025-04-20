/***************************************************************************
 * Title: MQTT.cpp
 * Author: Zac Lynn
 * 
 * Description: This program interfaces with the WizFi360 to setup and
 *    use MQTT to send and receive data.
 **************************************************************************/
#include "Arduino.h"
#include <string>
#include <TimeLib.h>

#define BROKER_IP "192.168.1.2"                                                         // Broker IP - Broker should be static IP at 192.168.1.2
#define BROKER_PORT "1883"                                                              // MQTT default port is 1883

#define DEVICE_ID "sensor1"

#define MAX_SAMPLE_FREQ 2000
#define MAX_LEN         30
#define MAX_CHANNELS    3

class MQTT {
    public:
        uint32_t startTime;
        int captureLen;
        int sampleFrequency;
        int numChannels;
        int isEnabled;                                                                  // If true data capture is running, else false
        uint32_t samplePeriod;                                                          // Sample period in microseconds
        uint32_t testLen;                                                               // Test length in microseconds
        uint32_t count;                                                                 // Number of samples taken

        void initMQTT();
        void publishStr(char* str, int length);
        void waitForStart();
        void pingServer();
        void sendTime();

    private:
        void resetWizFi();
        int checkForOK();    
        void sendATCommand(char *cmd, int length);
        void readResponse(char buff[], int len);


};
