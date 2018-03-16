# This file is used to read a given .wav file and return to you an array of
# ffts, where each fft is the result of fft_length samples specified by the
# caller. It leverages scipy for performing the FFT, matplotlib for optional
# debugging of data, and wave for reading wave files.
import matplotlib.pyplot as plt
import numpy
import wave
from math import ceil

numpy.set_printoptions(threshold=numpy.nan)

# struct is used to convert wav file data from bytes to floats.
import struct
import os
import sys

# Wave files store floats in 32 bit values (if they use that precision).
FLOAT_ENCODE = 4

VERBOSE = False

def convert_wav_to_fft(file_name, points_per_fft):
    """ Function used to convert a .wav file into an array of FFTs.

    Args:
        file_name: The path to the .wav file you want frequency information
                    from.
        points_per_fft: The number of samples of the audio file to accumulate
                            into an FFT. A larger points_per_fft results in more
                            of the song being truncated into a single FFT.

    Returns:
        Returns a list of numpy arrays, the ith index of the list corresponds to
        the FFT of the ith group of points_per_fft bytes. Returns None if the
        file does not exist.
    """
    fpath = os.path.abspath(file_name)
    try:
        wav_file = wave.open(fpath, 'r')
    except:
        print("ERROR: {} is not a valid wav file path.\n".format(fpath))
        return None

    print("INFO: Wave File Parameters: {}\n".format(wav_file.getparams()))
    num_channels = wav_file.getnchannels()
    bytes_per_samp = wav_file.getsampwidth()
    num_frames = wav_file.getnframes()
    samp_freq = wav_file.getframerate()

    bytes_per_frame = bytes_per_samp * num_channels

    # Wav files may be multichannelled. We only look at the first channel (mono,
    # by convention) when getting FFT data.
    if (num_channels != 1):
        print("WARNING: {} is not a mono file. ".format(fpath) +
                "Taking first channel only.\n")

    # Note that a frame is like a multichannel sample: each frame has
    # (bytes_per_samp) * number_of_channels bytes.
    # We take the first bytes_per_samp of each frame to limit ourselves to one
    # channel. Note that we pad the end of the sound_data with 0s to make it
    # divisible by the points_per_fft. The piece should be quiet at the end
    # anyway, so this shouldn't skew frequency content.
    data_length = num_frames
    while (data_length % points_per_fft != 0):
        data_length += 1
    sound_data = numpy.zeros(data_length)

    frame_data = wav_file.readframes(num_frames)
    i = 0
    j = 0
    while (i < num_frames):
        frame_ind = i * bytes_per_frame
        if (VERBOSE):
            print("INFO: Frame {} data: {} ".format(i,
                    frame_data[frame_ind:frame_ind + bytes_per_frame]) +
                    "Channel 1: {}\n".format(
                        frame_data[frame_ind:frame_ind+bytes_per_samp]))
        # Convert binary data to numerical values.
        if (bytes_per_samp == FLOAT_ENCODE):
            sound_data[j] = struct.unpack('f',
                                frame_data[frame_ind:frame_ind+bytes_per_samp])
        else:
            sound_data[j] = int.from_bytes(
                    frame_data[frame_ind:frame_ind+bytes_per_samp],
                    byteorder='little', signed=True)
        i += 1
        j += 1

    # These are the time stamps of the sound_data.
    time_values = numpy.arange(0, data_length / samp_freq, 1/samp_freq)

    # Normalize the sound amplitudes to [-1,1] and ensure that they are floats
    # for the FFT. The maximum value of a signed (bytes_per_sample*8)-bit number
    # is 2^(bytes_per_sample*8 - 1)
    sound_data = sound_data / (2.**(bytes_per_samp * 8 - 1))

    # We take an FFT for each points_per_fft samples in the wav file.
    ffts = numpy.zeros(shape=(data_length // points_per_fft,
                                points_per_fft // 2))
    i = 0
    while (i < num_frames):
        fft_samples = sound_data[i:i+points_per_fft]
        freqs = numpy.abs(numpy.fft.fft(fft_samples))

        # Only take the positive frequency content. Note that the FFT will
        # return an array that wraps around its center point. In other words,
        # the first n/2 values are positive frequncies, and the last are
        # negative. See numpy docs for details.
        freqs = freqs[0:ceil((points_per_fft)/2)]

        # Normalize the FFT by its length and double positive frequency values.
        freqs = (freqs / float(points_per_fft)) * 2
        # See numpy docs. For even length FFTs, freqs[points_per_fft/2] is the
        # positive and negative Nyquist frequency, so we shouldn't double it.
        if (num_frames % 2 == 0):
            freqs[-1] = freqs[-1] / 2

        ffts[i // points_per_fft,:] = freqs
        i += points_per_fft

    sample_freqs = numpy.fft.fftfreq(points_per_fft)[0:ceil(points_per_fft//2)]
    sample_freqs *= samp_freq
    if (VERBOSE):
        for i in range(len(ffts)):
            plt.plot(sample_freqs, ffts[i])
        plt.show()

    # array of FFT frames necessary for stream
    return ffts

if __name__ == "__main__":
    if (len(sys.argv) == 2 and sys.argv[1] == '-v'):
        VERBOSE = True
    #convert_wav_to_fft(
    #        'sample_wav_files/Totorro - Home Alone - 08 Tigers & Gorillas.wav',
    #        1024)
    convert_wav_to_fft('sample_wav_files/sound.wav', 44100)
    # convert_wav_to_fft('sample_wav_files/only_time.wav', 1000)
