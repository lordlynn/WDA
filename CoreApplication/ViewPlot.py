import numpy as np
import matplotlib.pyplot as plt
              
filename = "./test.csv"
arr = []
with open(filename, "r") as fp:
    while (fp.readable()):
        line = fp.readline()
        
        if (len(line) == 0):
            break

        line = line.strip("\n")
        line = line.split(",")
        arr.append(line)

data = {}
for key in arr[0]:
    if (key != ''):
        data[key] = {"time": [], "CH1": []}

numChannels = int(len(arr[1]) / len(data.keys())) - 1

for key in data.keys():
    for i in range(numChannels):
        data[key]["CH" + str(i+1)] = []


for line in range(2, len(arr)):                     # Iterate through lines of the file
    sensorNumber = 0
    for key in data.keys():                         # Iterate across each row based on number of sensors and number of channels per sensor 
        for i in range(numChannels+1):
            if (i == 0):
                data[key]["time"].append(arr[line][sensorNumber * (numChannels+1) + i])
            else:
                data[key]["CH" + str(i)].append(float(arr[line][sensorNumber * (numChannels+1) + i]) / 1023.0 * 3.3)
        
        sensorNumber += 1
    # print(line)
        
for sense in data:
    t = [float(i) for i in data[sense]["time"]]
    for i in range(1, len(data[sense])):
        plt.figure()
        plt.plot(t, data[sense]["CH" + str(i)])
        plt.ylabel("Voltage (v)")
        plt.xlabel("Time (s)")
        plt.title(sense + " : " + "CH" + str(i))
        # plt.ylim((-0.2, 3.7))

plt.show()  
 
pass
