#include <string.h>

void setup() {
  Serial.begin(115200);
  Serial1.begin(115200);

  Serial.println("INIT");

  initMQTT();
}

char buff[60];

void loop() {
  // sendATCommand((char*)("AT"));

  // // Serial.println("AT+MQTTSET=\"\",\"\",\"10.0.0.11\",1883");

  // delay(50);

  // readResponse(buff, 60);
  // Serial.print(buff);
  delay(7000);
  Serial.println("Loop");
  // put your main code here, to run repeatedly:

}

void initMQTT() {
  char buff[60];
  int lineCount;

  // sendATCommand((char *) ("AT+MQTTSET=\"\",\"\",\"10.0.0.11\",1883"));
  sendATCommand((char *) ("AT"));
  do {
    readResponse(buff, 60);
    Serial.print("Buffer: ");
    Serial.println(buff);
    Serial.println(strcmp(buff, "OK\r"), DEC);
  
    delay(1000);
  } while (strcmp(buff, "OK\r") != 0);

  Serial.print("Success");
  delay(10000);
  return;
}


void sendATCommand(char cmd[]) {
  int i;

  Serial1.println(cmd);
  
  // Find length of command
  for (i = 0; i < 60; i++) {
    if (cmd[i] == '\0')
      break;
  }

  Serial1.clear();  

}

void readResponse(char buff[], int len) {
  int ind = 0;
  int lineCount = 0;
  char tempBuff[len] = {'\0'};

  // Make sure input buffer is clear before starting
  memset(buff, '\0', len);
  
  // Read serial1 data into buffer
  while (Serial1.available()) {
    buff[ind++] = Serial1.read();
    if (buff[ind-1] == '\r')
      break;
    else if (buff[ind-1] == '\n') {
      ind--;
    }
    // Serial.println(buff[ind-1], HEX);
  }

  buff[ind] = '\0';

  // ind = 0;
  // // Print the buffer to serial connection
  // for (int i = 0; i < len; i++) {
  //   // WizFi uses \r\n as end of line, here \n is used as delimeter between reponses
  //   if (buff[i] == '\r') {
  //     tempBuff[ind++] = '\0';
  //     lineCount++;          
  //   }
  //   else if (buff[i] == '\n' || buff[i] == '\0'){
  //     continue;  
  //   }
  //   else {
  //     tempBuff[ind++] = buff[i];
  //   }
  // }

  // // Finishing building reponse str
  // tempBuff[ind] = '\0';

  // // Copy temporary string into buffer
  // strcpy(buff, tempBuff);
  
  // return lineCount;
}
