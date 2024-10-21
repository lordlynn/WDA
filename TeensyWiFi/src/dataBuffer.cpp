/***********************************************************************
 * Title: dataBuffer.cpp
 * Author: Zac Lynn
 * 
 * Description: This class implements a circular buffer of structs that
 *      Holds the sensor readings before they have been sent over MQTT.
 **********************************************************************/
#include "dataBuffer.h"

bool dataBuffer::push(sample data) {

    if (isFull) {                                                                       // If the buffer is full
        Serial.println("DATA: Buffer is full");
        return 0;
    }

    buff[head] = data;                                                                  // Combine 10-bit data and 4 bit channel  

    head++;
    
    if (head == len) {                                                                  // Wrap back to 0 if buffer is at last index
        head = 0;
    }

    if ((head + 1) % len == tail) {                                                     // Check if head has reached tail
        isFull = 1;
    }

    isEmpty = false;
    return 1;
}


char* dataBuffer::pop(int numToPop, int* numPopped) {
    char *str = (char *) malloc(sampleBytes * numToPop);                                // (2 bytes per ch + 4 bytes per timestamp) * samples 
    memset(str, '\0', sampleBytes * numToPop);                                          // Fill with '\0'

    char tempStr[sampleBytes];                                 
    int tempHead = head;                                                                // Save copy and use this in case head changes
    int strIndex = 0;

    for (int i = 0; i < numToPop; i++) {                                                // Pop i structures or until tail reaches head
        if (isEmpty) {                                                                  // 1.) Make sure tail is valid
            *numPopped = i;

            return str;
        }

        toString(buff[tail], tempStr);                                                  // 2.) Add byte to str
        memcpy(&(str[strIndex]), tempStr, sampleBytes);
        strIndex += sampleBytes;
        tail++;
        
        if (tail == len) {                                                              // 3.) check new tail position
            tail = 0;
        }
        if (tempHead == tail) {                                                         // If tail has reached head
            isEmpty = true;
        }
    }

    isFull = false;
    *numPopped = numToPop;
    return str;
}


void dataBuffer::toString(sample data, char* retStr) {                                  // Convert the data to a byte array with type char
    retStr[0] = (data.time & 0xFF00) >> 8;
    retStr[1] = (data.time & 0x00FF);

    retStr[2] = (data.ch1 & 0xFF00) >> 8;
    retStr[3] = (data.ch1 & 0x00FF);
    
    if (ch > 1) {
        retStr[4] = (data.ch2 & 0xFF00) >> 8;
        retStr[5] = (data.ch2 & 0x00FF);
    }

    if (ch > 2) {
        retStr[6] = (data.ch3 & 0xFF00) >> 8;
        retStr[7] = (data.ch3 & 0x00FF);
    }
}


void dataBuffer::reset(int channels) {                                                  // Reset the buffer flags and create new dynamic memory
    isFull = false;
    isEmpty = true;
    head = 0;
    tail = 0;
    ch = channels;
    sampleBytes = 2 + (ch * 2);

    delete[] buff;

    buff = new sample[len];

}
