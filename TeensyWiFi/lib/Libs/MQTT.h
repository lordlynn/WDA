#include "Arduino.h"
#include <string>
#include "RTC.h"

#define BROKER_IP "192.168.1.2"                                                         // Broker IP - Broker should be static IP at 192.168.1.2
#define BROKER_PORT "1883"

#define DEVICE_ID "sensor1"

#define MAX_SAMPLE_FREQ 2000
#define MAX_LEN         30
#define MAX_CHANNELS    3

extern RTC rtc;                                                                         // Get rtc object from main so that current RTC time can be sent

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
        int checkForOK();    
        void sendATCommand(char *cmd, int length);
        void readResponse(char buff[], int len);


};
