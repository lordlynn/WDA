import numpy as np
import matplotlib.pyplot as plt

# ---------------- Getting input from core application ---------------- 
# Read data from core application throigh stdin pipe
data = input()

# Turn string into list
data = data.split(',')

# Extract the sample frequency and parent figure title
frequency = float(data[0])
title = data[1]

# Remove frequency and title from list
data = data[2:]

# Remove brackets if any and convert string to float
data = [float(d.strip("[]")) for d in data]



# -------------------- CUSTOM FUNCTION STARTS HERE --------------------
# Use frequency to get fft frequency axis
# Use parent figure title to name the new figure displaying fft
# Use data to calculate fft

nfft = len(data)

# Zero mean the data
data = data - np.mean(data)

fft = np.fft.fft(data, nfft)

# Magnitude of fft 
fft = np.abs(fft)

# Frequency in cycles/d, so d = sample period
freq = np.fft.fftfreq(nfft, d=(1.0/int(frequency)))

# Arrays are from min->max->mirror so remove mirror and zoom in on 0-500Hz
fft = fft[0:nfft//4]
freq = freq[0:nfft//4]


# Create a new plot to display the results
plt.figure()
plt.plot(freq, fft)
plt.xlabel("Frequency (Hz)")
plt.ylabel("Relative Magnitude")
plt.title("FFT: " + title)

# Block and display the figure until closed
plt.show()