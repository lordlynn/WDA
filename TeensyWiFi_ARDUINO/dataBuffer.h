#include "Arduino.h"
#include <string.h>

struct sample {                                                                         // Struture of a sample. Data buffer iss buffer of this type
    uint16_t time;
    uint16_t ch1;
    uint16_t ch2;
    uint16_t ch3;
};

class dataBuffer {
    public:
        dataBuffer (int size, int channels) {
            buff = new sample[size];
            head = 0;
            tail = 0;
            len = size;
            ch = channels;
            sampleBytes = 2 + (ch * 2);
        }       

        void reset(int channels);
        bool push(sample data);
        char* pop(int numToPop, int* numPopped);

        bool isFull = false;
        bool isEmpty = true;
        int sampleBytes;                                                                // How many bytes is each sample. used for making the data str


    private:
        void toString(sample data, char* retStr);

        int len;
        int head;
        int tail;
        struct sample *buff;
        int ch;

        
};
