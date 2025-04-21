#include "dataBuffer.h"

bool dataBuffer::push(sample data) {                                                    // Add new samples to the buffer

    if (isFull) {                                                                       // If the buffer is full
        Serial.println("DATA: Buffer is full");                                         // Unlikely to happen. Would require 45k sample backup 
        return 0;
    }

    buff[head] = data;                                                                  // Add new sample to the buffer  

    head++;                                                                             // Increment head after adding sample
    
    if (head == len) {                                                                  // Wrap back to 0 if buffer is at last index
        head = 0;
    }

    if ((head + 1) % len == tail) {                                                     // Check if head is next to tail
        isFull = true;
    }

    isEmpty = false;                                                                    // If we added a sample, the buffer is not empty                    
    return 1;
}


char* dataBuffer::pop(int numToPop, int* numPopped) {                                   // Try to pop numToPop times, store how many actually got popped in numPopped
    char *str = (char *) malloc(sampleBytes * numToPop);                                // Allocate dynamic array to hold all popped data as byte array
    char tempStr[sampleBytes];                                                          // Used to store each individual sample as byte array
    int tempHead = head;                                                                // Save copy and use this in case head changes
    int strIndex = 0;                                                                   // Saves the index to put each sample in the final byte array

    memset(str, '\0', sampleBytes * numToPop);                                          // Fill byte array with '\0'

    for (int i = 0; i < numToPop; i++) {                                                // Pop i structures or until tail reaches head
        if (isEmpty) {                                                                  // 1.) Make sure there is new data to read
            *numPopped = i;                                                             // If the buffer is empty record how many samples were popped and return
            return str;
        }

        toString(buff[tail], tempStr);                                                  // 2.) Convert a single sample to a byte array
        memcpy(&(str[strIndex]), tempStr, sampleBytes);                                 // Copy single sample into final byte array
        strIndex += sampleBytes;                                                        // Increment final array index for next sample
        tail++;                                                                         // Move the tail so this sample is no longer part of the buffer we care about
        
        if (tail == len) {                                                              // 3.) Check new tail position, rollover to start if we are at end of buffer
            tail = 0;
        }
        if (tempHead == tail) {                                                         // If tail has reached head stop popping samples
            isEmpty = true;                                                             // Set isEmpty true and return on next iteration
        }
    }

    isFull = false;                                                                     // If we read any samples, buffer cannot be full
    *numPopped = numToPop;                                                              // If we didnt return in loop, we popped the requested amount of samples
    return str;                                                                         // Return the byte array **you better make sure you free this :)
}


void dataBuffer::toString(sample data, char* retStr) {                                  // Convert the data to a byte array with type char
    retStr[0] = (data.time & 0xFF00) >> 8;                                              // Always need to add the timestamp
    retStr[1] = (data.time & 0x00FF);

    retStr[2] = (data.ch1 & 0xFF00) >> 8;                                               // Always need the first channel
    retStr[3] = (data.ch1 & 0x00FF);
    
    if (ch > 1) {                                                                       // If multiple channels were used, add those as well
        retStr[4] = (data.ch2 & 0xFF00) >> 8;
        retStr[5] = (data.ch2 & 0x00FF);
    }

    if (ch > 2) {
        retStr[6] = (data.ch3 & 0xFF00) >> 8;
        retStr[7] = (data.ch3 & 0x00FF);
    }
}


void dataBuffer::reset(int channels) {                                                  // Reset the buffer flags and create new dynamic memory
    isFull = false;                                                                     // Reset flags 
    isEmpty = true;
    head = 0;                                                                           // Reset head and tail indices
    tail = 0;
    ch = channels;                                                                      // Update class variable ch with new channel count
    sampleBytes = 2 + (ch * 2);                                                         // Recalculate bytes per sample

    delete[] buff;                                                                      // Deallocate the old buffer

    buff = new sample[len];                                                             // Create the new buffer
}
