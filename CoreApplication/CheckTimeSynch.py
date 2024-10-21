import numpy as np
import matplotlib.pyplot as plt

# filename = "./DataFilesICareAbout/TestTimeSynch_3CH_40Hz.csv"
filename = "./TimeSynchTest_3CH.csv"
arr = []
numChannels = None
data = None

def readData():
    global arr, data, numChannels
    with open(filename, "r") as fp:                                                         # Read the data file into an array
        while (fp.readable()):
            line = fp.readline()
            
            if (len(line) == 0):
                break

            line = line.strip("\n")
            line = line.split(",")
            arr.append(line)

    data = {"sensor1": None, "sensor2": None}
    data["sensor1"] = {}
    data["sensor2"] = {}
    for key in arr[1]:
        data["sensor1"][str(key)] = []                                                                 # This dictionary will hold the data
        data["sensor2"][str(key)] = []

    numChannels = int(len(arr[1]) / len(data.keys())) - 1

    for line in range(2, len(arr)):                                                         # Iterate through lines of the file
        sensorNumber = 0
        for key in data.keys():                                                             # Iterate across each row based on number of sensors and number of channels per sensor 
            for i in range(numChannels+1):
                if (i == 0):
                    data[key]["Time"].append(
                        float(arr[line][sensorNumber * (numChannels+1) + i]))
                else:
                    data[key]["CH" + str(i)].append(
                        float(arr[line][sensorNumber * (numChannels+1) + i]) / 1023.0 * 3.3)
            
            sensorNumber += 1
    
def calculateTimeSynch():                                                                   # Check the time synch by finding when quare waves are out of phase
    sampleOffset = 0
    offsetSum = 0
    numOffsets = 0
    
    for t in range(len(arr)-2):
        temp = [data[key]["CH1"][t] for key in data.keys()]                                 # Put the values from sensor1 and sensor2 at time t into a list

        if (max(temp) - min(temp) > 1.5):                                                   # If there is a difference greater than 1.5 volts, the sensor times are not synched
            sampleOffset += 1    
        else:
            offsetSum += sampleOffset
            numOffsets += 1 if sampleOffset > 1 else 0
            sampleOffset = 0

    samplePeriod = data["sensor1"]["Time"][1]
    timeOffset = int((offsetSum / numOffsets) * samplePeriod * 1000)
    print("Average time offset (ms): " + str(timeOffset))

def plotData():                                                                             # Visually check time synch
    
    count = 1
    plt.figure()

    for i in range(numChannels):
        lgnd = []
        for key in data.keys():                                                                 # Iterate across each row based on number of sensors and number of channels per sensor 
            plt.subplot(numChannels, 1, count)
            plt.plot(data[key]["Time"], data[key]["CH" + str(i+1)])

            

        plt.ylabel('Voltage (v)')
        plt.ylim((-0.2, 3.7))
        plt.xlim(xView)

        if (count == 1):
            # plt.legend(lgnd) 
            plt.title("Input Signals")

        if (count == numChannels):
            plt.xlabel('Time (s)')

        count += 1

    

    plt.figure()

    for i in range(1, numChannels+1): 
        diff = np.abs(np.subtract(data["sensor1"]["CH" + str(i)], data["sensor2"]["CH" + str(i)]))
        
        plt.subplot(numChannels, 1, i)    
        plt.plot(data[key]["Time"], diff)
        plt.ylabel('Difference (v)')
        

        plt.ylim((-0.2, 3.7))
        plt.xlim(xView)

        if (i == 1):
            plt.title("Absolute Difference Between Signals")

        if (i == numChannels):
            plt.xlabel('Time (s)')

    plt.show()
# original (0.195, 0.245)
# 3CH
xView = (1.00, 1.05)
readData()
calculateTimeSynch()
plotData()
