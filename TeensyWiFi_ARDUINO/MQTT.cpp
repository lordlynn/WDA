#include "MQTT.h"


void MQTT::initMQTT() {
  int errorFlag;
  std::string str;                                                                      // Use c++ string to use += instead of strcat. Slighly easier to read

  // This loop is not great because it is hard to read... string tokenization :/
  do {
    errorFlag = 0;                                                                      // If this stays as 0 then setup worked 
    
    // AT+MQTTSET="","","
    str = "AT+MQTTSET=\"\",\"\",\"";                                                    // Configure clientside MQTT
    str += DEVICE_ID;                                                                   // - Device ID
    str += "\",60";                                                                     // - Device Timeout
    // Final command = AT+MQTTSET="","","DEVICE_ID", 60

    sendATCommand((char *) (str.c_str()), str.length());    
    if (checkForOK()) { 
      Serial.println("MQTT ID has been set");
    }
    else {
      Serial.println("Failed to set MQTT ID");
      errorFlag = 1;
      resetWizFi();                                                                     // Reset the WizFi board to prepare for next attempt at setup
      continue;                                                                         // If it fails dont try to run the rest of the init
    }

    str ="AT+MQTTTOPIC=\"";                                                             // Set publish and subscribe topics
    str += DEVICE_ID;                                                                   // We will publish data to the base topic
    str += "/";
    str += "\",\"";
    str += DEVICE_ID;                                                                   // We will read data from the CONFIG topic
    str += "/CONFIG/";
    str += "\"";   
    // Final Command: AT+MQTTTOPIC="DEVICE_ID/","DEVICE_ID/CONFIG/"

    sendATCommand((char *) (str.c_str()), str.length());                                // Convert C++ str to C str
    if (checkForOK()) { 
      Serial.println("Publish and Subscribe topics have been set");
    }
    else {
      Serial.println("Failed to set the publish and subscribe topics");
      errorFlag = 1;
      resetWizFi();                                                                     // Reset the WizFi board to prepare for next attempt at setup
      continue;                                                                         // If it fails dont try to run the rest of the init
    }

    str = "AT+MQTTCON=0,\"";                                                            // Set Broker IP and Port
    str += BROKER_IP;                                                                   // - Broker IP
    str += "\",";
    str += BROKER_PORT;                                                                 // - Broker Port
    // Final Command: AT+MQTTCON=0,"BROKER_IP",BROKER_PORT

    sendATCommand((char *) (str.c_str()), str.length());                        
    if (checkForOK()) { 
      Serial.println("Successfully connected to broker");
    }
    else {
      Serial.println("Failed to connect to broker");
      errorFlag = 1;
      resetWizFi();                                                                     // Reset the WizFi board to prepare for next attempt at setup
    }
    
  } while (errorFlag);                                                                  // Keep trying to setup the WizFi until it is successful 

  Serial.println("Connected To Broker...");
}


void MQTT::waitForStart() {                                                             // Wait for configuration message
  char buff[64];
  char *topic;
  char *data;
  int configFlag = 0;
  char pong[] = "pong";
  char start[] = "START";
  char fail[] = "FAIL";

  while (configFlag == 0) {                                                             // Loop until configuration read successfully 
    readResponse(buff, 64);                                                             // Try to read a message from core application

    if (buff[0] == '\0')                                                                // If no message was read, try again
      continue;
    
    /*************************************************************
     * Messaged received over MQTT will be printed on serial  
     * connection in the format: "Sub_topic -> Message"
     ************************************************************/
    topic = strtok(buff, "->");                                                         // Get portion before '->'
    if (topic == NULL)                                                                  // Check if the pointer is null, meaning "->" was not found
      continue;                                                                         

    data = strtok(NULL, "->");                                                          // Get portion after '->'
    if (data == NULL)                                                                   // Check if the pointer is null, meaning nothing was after "->" 
      continue;

    if (strncmp(data, " ping", 5) == 0) {                                               // Check if ping was received. Do this here so that we reconnect/connect during config stage
      publishStr(pong, 4);                                                              // Return pong and current RTC time
      sendTime();                                                                       
    }

    /*************************************************************
     * The config message from core application is in the form:
     * "Test time, sample frequency, num channels, RTC start time"
     ************************************************************/
    data = strtok(data, ",");                                                           // Get the portion before first comma (test time)
    if (data == NULL)                                                                   // Check all pointer for NULL to prevent crash and make sure data was received
      continue;

    captureLen = atoi(data);                                                            // Conver the ASCII str to integer value

    data = strtok(NULL, ",");                                                           // Get the portion after the first comma (sample frequency)
    if (data == NULL) 
      continue;

    sampleFrequency = atoi(data);

    data = strtok(NULL, ",");                                                           // Get the portion after the second comma (num channels)
    if (data == NULL) 
      continue;

    numChannels = atoi(data);

    data = strtok(NULL, ",");                                                           // Get the portion after the third comma (RTC start time)
    if (data == NULL) 
      continue;

    startTime = atoi(data);


    if (sampleFrequency < 1000 || sampleFrequency > MAX_SAMPLE_FREQ) {                  // Check that all configuration values are within the expected ranges
      configFlag = 0;                                                                   // If the values are invalid set flag to 0 
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
    
    if (configFlag == 0) {                                                              // If the config values were invalid send "FAIL" and rerun loop
      publishStr(fail, 4);                                                               
      continue;
    }

    publishStr(start, 5);                                                               // If the config values were good send "START" signal
    samplePeriod = (1.0 / sampleFrequency) * 1000 * 1000;                               // Convert frequency to period in microseconds
    testLen = captureLen * 1000 * 1000;                                                 // Convert seconds to us
    count = 0;                                                                          // Reset the sample count before a new test
    isEnabled = 1;                                                                      // Flag used by main to tell if data capture should start
  }
}


void MQTT::pingServer() {
  char ping[] = "ping";
  char buff[64];
  char *topic;
  char *data;

  while (1) {
    delay(1000);                                                                        // Dont spam ping requests. This is setup stage so delaying is fine

    publishStr(ping, 4);                                                                // Send Ping to server
    delay(250);                                                                         // Wait 250ms to give time for core application to respond

    readResponse(buff, 64);                                                             // Try to read a response from core application

    if (buff[0] == '\0')                                                                // If no message was received, send ping again
      continue;
    
    /*************************************************************
     * Messaged received over MQTT will be printed on serial  
     * connection in the format: "Sub_topic -> Message"
     ************************************************************/
    topic = strtok(buff, "->");                                                         // Get portion before "->"
    if (topic == NULL)                                                                  // Check if the pointer is null, meaning "->" was not found
      continue; 

    data = strtok(NULL, "->");                                                          // Get portion after "->"

    if (data == NULL)                                                                   // Check if the pointer is null, meaning nothing was after "->"
        continue;

    if (strncmp(data, " pong", 5) == 0) {                                               // Check if we got the pong response
      break;                                                                            // If server pong back, exit function
    }
  }
  
  sendTime();                                                                           // After successfully pinging, send the current RTC time
}


void MQTT::sendTime(void) {                                                             // Send current RTC time
  char time[8] = "TIME";                                                                // Header "TIME" in message indicates we are sending our RTC time                                                  
  uint32_t t = Teensy3Clock.get();                                                      // Get RTC value in seconds
  
  memcpy(&(time[4]), (const void *) &t, 4);                                             // Write the binary of the time value after header                   

  publishStr(time, 8);
}


void MQTT::resetWizFi() {
  std::string str;
  Serial.println("INIT FAILED\t-\tTrying again...\n");
  str = "AT+RST";                                                                       // Reset WizFi360 in case it completed partial setup
  sendATCommand((char *) (str.c_str()), str.length()); 
  delay(3000);                                                                          // Give enough time for board to reset and connect to WiFi
}


void MQTT::publishStr(char* str, int length) {
  char strToSend[2048] = {'\0'};                                                        // Caller is required to keep the str parameter under 2048 charaters

  if (length > 2048) {
    // NOT GOOD IF THIS HAPPENS - WILL RANDOMLY ASSIGN END OF DATA WITHOUT ALIGNMENT
    // This should never happen. Buffer pop is setup to return at most 2000 bytes
    Serial.printf("Length is too big: %d\n", length);
    length = 2048; 
  }

  strcat(strToSend, "AT+MQTTPUBSEND=");                                                 // Add the AT command for sending bulk MQTT data
  sprintf(&(strToSend[15]), "%d", length);                                              // After the '=' add the number of characters to be sent
    
  sendATCommand(strToSend, strlen(strToSend));                                          // Send the AT command

  if (!checkForOK()) {                                                                  // Check for response
    Serial.printf("Didnt get OK setup\n");
  }

  sendATCommand(str, length);                                                           // After sending the command it expects the data buffer to send through MQTT

  if (!checkForOK()) {
    Serial.printf("Didnt get OK data\n");
  }
  
}


void MQTT::sendATCommand(char *cmd, int length) {
  Serial1.write(cmd, length);
  Serial1.flush();                                                                      // Wait for all of the data in the buffer to transmit

  Serial1.write("\r\n");                                                                // Write terminating characters to command
  Serial1.flush();                                                                      // Wait for all of the data in the buffer to transmit
}


int MQTT::checkForOK() {
  char buff[64];
  int attempts = 75;                                                                    

  while (1) {
      readResponse(buff, 64);                                                           // Check for a response to the AT command from the WizFi360

      if (strcmp(buff, "ERROR\r") == 0) {
        return 0;
      }

      /*********************************************************** 
       * For some reason there are a lot of issues with getting  
       * the full "OK\r". In tests done with manually sending AT  
       * Commands the same issue is present. Maybe an issue with  
       * the WizFi360. To fix this, just check all of these  
       * variations that I've seen while experimenting.
       **********************************************************/
      if (strcmp(buff, "OK\r") == 0)
        return 1; 

      if (strcmp(buff, "OK") == 0)
        return 1; 

      if (strcmp(buff, "O") == 0)
        return 1; 
      
      if (strcmp(buff, "O\r") == 0)                                                     // The \r should really only ever come after 'K'. Issue with WizFi360 itself?
        return 1; 

      delay(5);                                                                         // If no message was received delay for short time. Found experimentally. Too fast misses message, too slow is inefficient

      if (attempts-- <= 0)                                                              // After n attempts exit infinite loop 
        return 0;
  }
}


void MQTT::readResponse(char buff[], int len) {
  int ind = 0;

  memset(buff, '\0', len);                                                              // Make sure input buffer is clear before starting
  
  while (Serial1.available()) {                                                         // Read serial data from WizFi360
    buff[ind++] = Serial1.read();                                                       // Reach 1 char at a time and advance index

    if (buff[ind-1] == '\r')                                                            // Ending of message is \r\n, use \r to find the end
      break;
    
    else if (buff[ind-1] == '\n')                                                       // Ignore \n may be the end of message or in the middle so just ommit
      ind--;

    else if (ind == len-1)                                                              // If we are at the end of the buffer, shouldnt happen
      break;
    
    /*************************************************************
     * We dont know how long the message is so delay long enough
     * for any future characters to be sent.
     *
     * Using a 1.5M baud rate so:
     *
     *    1.5e6 baud / 8 bits = byte rate = 187.5k bytes / second
     *    period for 1 byte to be sent: 1/187.5k = 5.333us
     *    Delay rounded up to 10us to be safe. 
     *    (Should also work with 1M baud)
     ************************************************************/
    delayMicroseconds(10);                                                              // Delay a short period in case the WizFi is in the process of sending more characters
  }

  buff[ind] = '\0';                                                                     // Only required in certain cases because of memset. (Ex: \n is last char and then breaks need to add null)
}