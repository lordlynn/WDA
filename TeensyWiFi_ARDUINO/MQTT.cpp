/***********************************************************************
 * Title: MQTT.cpp
 * Author: Zac Lynn
 * 
 * Description: This program interfaces with the WizFi360 to setup and
 *    use MQTT to send and receive data.
 **********************************************************************/
#include "MQTT.h"


void MQTT::sendTime(void) {                                                             // Send current RTC time
  char time[8] = "TIME";

  uint32_t t = rtc.secs();
  
  memcpy(time+4, (const void *) &t, 4);

  publishStr(time, 8);
}


void MQTT::waitForStart() {                                                             // Wait for configuration message
  char buff[60];
  char *topic;
  char *data;
  int configFlag = 0;
  char pong[] = "pong";

  while (configFlag == 0) {                                                             // Loop until configuration read successfully 
    readResponse(buff, 60);  

    if (buff[0] == '\0')
      continue;
    
    /* Messaged received over MQTT will be printed on serial connection in the 
     *    format: "Sub_topic -> Message".
     */
    topic = strtok(buff, "->");                                                         // Get portion before '->'
    if (topic == NULL)
      continue; 

    data = strtok(NULL, "->");                                                          // Get portion after '->'
    if (data == NULL) 
      continue;

    if (strncmp(data, " pong", 5) == 0) {                                               // Check if pong was received
      publishStr(pong, 4);                                                              // Return pong and current RTC time
      sendTime();
    }

    data = strtok(data, ",");                                                           // Parse the configuration variables from data string
    if (data == NULL) 
      continue;

    captureLen = atoi(data);

    data = strtok(NULL, ",");
    if (data == NULL) 
      continue;

    sampleFrequency = atoi(data);

    data = strtok(NULL, ",");
    if (data == NULL) 
      continue;

    numChannels = atoi(data);


    data = strtok(NULL, ",");
    if (data == NULL) 
      continue;

    startTime = atoi(data);

    if (sampleFrequency < 1000 || sampleFrequency > MAX_SAMPLE_FREQ) {                  // Check if configuration values are within the expected ranges
      configFlag = 0;
    }
    else if (captureLen < 1 || captureLen > MAX_LEN) {
      configFlag = 0;
    }
    else if (numChannels < 1 || numChannels > MAX_CHANNELS) {
      configFlag = 0;
    }
    else {
      configFlag = 1;
    }
    
    if (configFlag == 0) {                                                              // Publish START or FAIL if configuration was good or bad
      char fail[] = "FAIL";
      publishStr(fail, 4);
      continue;
    }

    char start[] = "START";
    publishStr(start, 5);
    isEnabled = 1;
    samplePeriod = (1.0 / sampleFrequency) * 1000 * 1000;                               // Convert frequency to period in microseconds
    testLen = captureLen * 1000 * 1000;                                                 // Convert seconds to us
    count = 0;
  }
}


void MQTT::pingServer() {
  char ping[] = "ping";
  char buff[60];
  char *topic;
  char *data;

  while (1) {
    delay(1000);                                                                        // Dont spam ping requests

    publishStr(ping, 4);                                                                // Send Ping to server
    delay(250);

    readResponse(buff, 60);  

    if (buff[0] == '\0')
      continue;
    
    /* Messaged received over MQTT will be printed on serial connection in the 
     *    format: "Sub_topic -> Message".
     */

    topic = strtok(buff, "->");                                                         // Get portion before '->'
    if (topic == NULL)
      continue; 

    data = strtok(NULL, "->");                                                          // Get portion after '->'
    if (data == NULL)
        continue;

    if (strncmp(data, " ping", 5) == 0) {
      break;                                                                            // If server pings back, exit function
    }
  }
  
  sendTime();                                                                           // After successfully pinging, send the current RTC time
}


void MQTT::initMQTT() {
  int errorFlag;
  std::string str;

  // This function is not great because it is hard to read
  do {
    errorFlag = 0;

    str = "AT+MQTTSET=\"\",\"\",\"";                                                    // Configure clientside MQTT
    str += DEVICE_ID;                                                                   // - Device ID
    str += "\",60";                                                                     // - Device Timeout

    sendATCommand((char *) (str.c_str()), str.length());    
    if (checkForOK()) { 
      Serial.println("MQTT ID has been set");
    }
    else {
      Serial.println("Failed to set MQTT ID");
      errorFlag = 1;
    }

    str ="AT+MQTTTOPIC=\"";                                                             // Set publish and subscribe topics
    str += DEVICE_ID;                                                                   // - Publish Topic
    str += "/";
    str += "\",\"";
    str += DEVICE_ID;                                                                   // - Subscribe Topic
    str += "/CONFIG/";
    str += "\"";   

    sendATCommand((char *) (str.c_str()), str.length());    
    if (checkForOK()) { 
      Serial.println("Publish and Subscribe topics have been set");
    }
    else {
      Serial.println("Failed to set the publish and subscribe topics");
      errorFlag = 1;
    }

    str = "AT+MQTTCON=0,\"";                                                            // Set Broker IP and Port
    str += BROKER_IP;                                                                   // - Broker IP
    str += "\",";
    str += BROKER_PORT;                                                                 // - Broker Port

    sendATCommand((char *) (str.c_str()), str.length());                        
    if (checkForOK()) { 
      Serial.println("Successfully connected to broker");
    }
    else {
      Serial.println("Failed to connect to broker");
      errorFlag = 1;
    }

    if (errorFlag) {                                                                    // If any of the steps failed try again
      Serial.println("INIT FAILED\t-\tTrying again...\n");
      str = "AT+RST";                                                                   // Reset WizFi360 in case it completed partial setup
      sendATCommand((char *) (str.c_str()), str.length()); 
      delay(3000);                                                                      
    }
    
  } while (errorFlag); 

  Serial.println("Connected To Broker...");
}


void MQTT::publishStr(char* str, int length) {
  if (length > 2034) {
    Serial.printf("Length is too big: %d\n", length);
    length = 2034; // NOT GOOD IF THIS HAPPENS - WILL RANDOMLY ASSIGN END OF DATA WITHOUT DATA ALIGNMENT
  }

  char strToSend[2048] = {'\0'};                                                        // Caller is required to keep the str parameter under 2034 charaters
        
  strcat(strToSend, "AT+MQTTPUBSEND=");
  sprintf(&(strToSend[15]), "%d", length);
      

  sendATCommand(strToSend, strlen(strToSend));
  if (!checkForOK()) {
    Serial.printf("Didnt get OK setup\n");
  }

  sendATCommand(str, length);

  if (!checkForOK()) {
    Serial.printf("Didnt get OK data\n");
  }
  
}


void MQTT::sendATCommand(char *cmd, int length) {
  Serial1.write(cmd, length);
  Serial1.flush();                                                                      // Write command (can be larger than 64-byte buffer)
  Serial1.clear();                                                                      // Clear buffer to open up room for Rx

  Serial1.write("\r\n");                                                                // Write terminating characters to command
  Serial1.flush();                                                                      // Write command (can be larger than 64-byte buffer)
  Serial1.clear();                                                                      // Clear buffer to open up room for Rx
}


int MQTT::checkForOK() {
  char buff[64];
  int attempts = 75;

  while (1) {
      readResponse(buff, 64);

      if (strcmp(buff, "ERROR\r") == 0) {
        delay(5);
        return 0;
      }

      if (strcmp(buff, "OK\r") == 0)
        return 1; 

      if (strcmp(buff, "OK") == 0)
        return 1; 

      if (strcmp(buff, "O") == 0)
        return 1; 
      
      if (strcmp(buff, "O\r") == 0)
        return 1; 

      delay(4);

      if (attempts-- <= 0)                                                              // After n attempts exit infinite loop
        return 0;
  }
}


void MQTT::readResponse(char buff[], int len) {
  int ind = 0;

  memset(buff, '\0', len);                                                              // Make sure input buffer is clear before starting
  
  while (Serial1.available()) {                                                         // Read serial1 data into buffer
    buff[ind++] = Serial1.read();

    if (buff[ind-1] == '\r')
      break;
    
    else if (buff[ind-1] == '\n')
      ind--;

    else if (ind == len-1)
      break;
    
    delayMicroseconds(750);
  }

  buff[ind] = '\0';
}