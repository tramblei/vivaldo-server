import matplotlib.pyplot as plt

high_fname = "fft_high.vals"
low_fname = "fft_low.vals"
average_frames = "ffts.txt"
high_vals = []
low_vals = []
freqs = []

with open(average_frames) as lf:
    vals = []
    count = 0
    for line in lf:
        vals_string = line.split(',')
        
        for i in range(len( vals_string)):
            if vals_string[i] == '\n':
                continue
            if count == 0:
                vals.append(int(vals_string[i]))
                freqs.append(44000 / 1024 * i)
            else:
                vals[i] += int(vals_string[i])

        break
        count += 1
    
    plt.plot(freqs[0:(len(vals) // 2)],\
                vals[0:(len(vals) // 2)], 'r+-')
    plt.show()

#
#with open(high_fname) as hf, open(low_fname) as lf:
#    hlines = hf.read().split(',')
#    llines = lf.read().split(',')
#    #__import__('pdb').set_trace()
#    i = 0
#    for i in range(len(hlines)):
#        high_vals.append(int(hlines[i]))
#        low_vals.append(int(llines[i]))
#        freqs.append(44000 / 1024 * i)
#    plt.plot(freqs[0:(len(hlines) // 2)],\
#                high_vals[0:(len(hlines) // 2)], 'r+-',\
#                freqs[0:(len(hlines) // 2)],\
#                low_vals[0:(len(hlines) // 2)], 'bH-')
#    plt.show()
