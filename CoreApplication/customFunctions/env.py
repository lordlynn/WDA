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
# Use frequency to make time series 
# Use parent figure title to name the new figure displaying the envelope
# Use data to calculate moving average envelope

# Zero mean the data
data = np.subtract(data, np.mean(data))

# Rectify the data
data = np.absolute(data)

env = []
timeSeries = []

# Create a 250ms window
N = int(0.250 * frequency)

for i in range(0, len(data), N):
    if (i+N > len(data)):
        break
    else:
        env.append(np.mean(data[i:i+N]))

    # calculate time
    timeSeries.append((1/frequency) * i)



# Create a new plot to display the results
plt.figure()
plt.plot(timeSeries, env)
plt.xlabel("Time (s)")
plt.ylabel("MAV")
plt.title("Envelope: " + title)
plt.ylim([-0.1, 1.75])


# Block and display the figure until closed
plt.show()