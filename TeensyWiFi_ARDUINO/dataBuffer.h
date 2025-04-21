/***************************************************************************
 * Title: dataBuffer.cpp
 * Author: Zac Lynn
 * 
 * Description: This class implements a circular buffer of structs that
 *      holds the sensor readings before they have been sent over MQTT.
 **************************************************************************/
#include "Arduino.h"
#include <string.h>

/*****************************************************************
 * Declared outside of class so that it has global scope. It can
 * easily be used in any file that includes the header without
 * needing to go through the class object.
 *  
 * The buffer uses the the same structure with space for 3 
 * channels no matter how many are used. It is inefficient, but 
 * there is enough memory and it makes the code simpler. 
 ****************************************************************/
struct sample {                                                                         // Struture of a data sample. Data buffer is a buffer of this type
  uint16_t time;
  uint16_t ch1;
  uint16_t ch2;
  uint16_t ch3;
};


class dataBuffer {
    public:
        dataBuffer (int size, int channels) {
            buff = new sample[size];                                                    // Create an array of sample struct with the given number of elements
            head = 0;                                                                   // Reset head and tail indices 
            tail = 0;
            len = size;                                                                 // Save buffer size
            ch = channels;                                                              // Set the number of channels actually being used
            sampleBytes = 2 + (ch * 2);                                                 // Set the number of bytes used per sample (timestamp + data channels)
        }       

        void reset(int channels);                                                       // Delete the array and recreate it
        bool push(sample data);                                                         // Add samples to buffer
        char* pop(int numToPop, int* numPopped);                                        // Remove samples and convert struct to byte array

        bool isFull = false;
        bool isEmpty = true;
        int sampleBytes;                                                                // How many bytes is each sample. used for making the data str
        

    private:
        void toString(sample data, char* retStr);                                       // Convert a single sample to a byte array

        int len;                                                                        // Hold length in samples of the buffer
        int head;                                                                       // Store head of buffer
        int tail;                                                                       // Store the tail of the buffer
        struct sample *buff;                                                            // Hold pointer to the allocated buffer
        int ch;                                                                         // Store number of channels used
};

