/*
This example program makes use of the simple
sound library to generate a sine wave and write the
output to sound.wav.
For complete documentation on the library, see:
http://www.nd.edu/~dthain/courses/cse20211/fall2013/wavfile
Go ahead and modify this program for your own purposes.
*/


#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <errno.h>

#include "wavfile.h"

const int NUM_SAMPLES = (WAVFILE_SAMPLES_PER_SECOND);

int main()
{
	short waveform[NUM_SAMPLES*8];
	double frequency = 440.0;
	int volume = 32000;
	int length = NUM_SAMPLES;
	int i;
    int j;
    int k;
    int count=0;
    for(k=0; k< 1;k++){

        frequency=440.0;
    for(j=0; j < 4; j++) {
        for(i=0;i<length;i++) {
            double t = (double) i / WAVFILE_SAMPLES_PER_SECOND;
            waveform[count++] = volume*sin(frequency*t*2*M_PI);
        }
    }
    frequency=493.883;
    for(j=0; j < 4; j++) {
        for(i=0;i<length;i++) {
            double t = (double) i / WAVFILE_SAMPLES_PER_SECOND;
            waveform[count++] = volume*sin(frequency*t*2*M_PI);
        }
    }
    }
//	for(i=length/2;i<length;i++) {
//		double t = (double) i / WAVFILE_SAMPLES_PER_SECOND;
//		waveform[i] = volume*sin(2*frequency*t*2*M_PI);
//	}

	FILE * f = wavfile_open("sound.wav");
	if(!f) {
		printf("couldn't open sound.wav for writing: %s",strerror(errno));
		return 1;
	}

	wavfile_write(f,waveform,length*8);
	wavfile_close(f);

	return 0;
}
