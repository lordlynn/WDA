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




# Create a new plot to display the results
plt.figure()
plt.plot(data)
plt.xlabel("X-axis")
plt.ylabel("Y-axis")
plt.title("Custom Function 1: " + title)

# Block and display the figure until closed
plt.show()