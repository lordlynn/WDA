########################################################################
#   Title: MQTT.py
#   Author: Zac Lynn
#   Description: This code implements the MQTT communications required
#        for the wireless EMG system. 
#
########################################################################
from paho.mqtt import client as mqtt_client
from tkinter import NORMAL
import socket
import time
import csv
import numpy as np


class MQTT:
    broker = None                                                                               # Set the default IP address. Will be overwritten unless system fails to find its own IP
    port = None                                                                                 # Which port to use for MQTT (1883)
    client = None
    clientID = None                                                                             # Client ID seen by MQTT broker
    waitingForStart = {"sensor1": False, "sensor2": False}                                      # Flag used when waiting for the system to send "START" / "FAIL"
    configWasSet = {"sensor1": False, "sensor2": False}                                         # True if the micro recieved the config succesfuly, false else
    samples = {}                                                                                # Holds the samples received from sensors
    inputChannels = 0                                                                           # Stores number of channels being recorded
    sampleBytes = 4                                                                             # Stores the number of bytes each sample is
    devices = {"sensor1": 0, "sensor2": 0}                                                      # Holds sensor name as key and connection status as value
    deviceTime = {"sensor1": [0, 0], "sensor2": [0, 0]}                                         # Stores the local time of the sensors, If times are very different then no time synch was done
    FORWARD_TIME_OFFSET = 4                                                                     # Amount fo time to wait before test starts, must be greater than maximum latency

    def __init__(self, clientID, brokerIP=0, port=1883, top=None):
        self.top = top                                                                          # Holds a reference to the core apllication
        
        # Set member variables
        if (brokerIP == 0):                                                                     # If the Broker IP is not set, use localhost IP
            self.getLocalIP()
        else:
            self.broker = brokerIP

        self.port = port                                                                        # Set broker port
        self.clientID = clientID                                                                # The ID we provide to the broker

        self.client = self.connect_mqtt()                                                       # Create MQTT object and connect
        
        # Add subscriptions
        topic = "#"
        result = self.client.subscribe(topic)                                                   # Subscribe to all topics
        status = result[0]

        if status == 0:
            print(f"Subscribed to `{topic}` ")
        else:
            print(f"INITIALIZATION ERROR:\tFailed to subscribe to {topic}")

        # Set callback function for message reception. This function prototype is given in Paho MQTT documentation
        self.client.on_message = self.on_message


    def getLocalIP(self):
        # Solution is a little weird but seems to work and socket library is multi-platform.
        # https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.broker = s.getsockname()[0]
        except Exception as e:
            print("Failed to get local IP with error: " + str(e))
                
        finally:
            s.close()

    
    def connect_mqtt(self):
        def on_connect(client, userData, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!\n")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.clientID)
        
        client.on_connect = on_connect
        try:
            client.connect(self.broker, self.port)
        except Exception as err:
            print("INITIALIZATION ERROR:\t" + str(err))
        return client


    def on_message(self, client, userData, message):
        if ("CONFIG" in message.topic):
            return                                                                              # Ignore messages sent by this device
        
        sensor = message.topic.split("/")                                                       # Gets the name of sensor that sent message
        sensor = sensor[0]

        keys = list(self.devices.keys())

        data = []

        try:                                                                                    # If the time message was not sent decoding will raise excpetion
            if ("TIME" == message.payload[0:4].decode('utf-8')):
                t = ((message.payload[7] << 24) | (message.payload[6] << 16) |                  # Extract a unit32_t 
                     (message.payload[5] << 8)  | (message.payload[4]))
                
                self.top.startButton["state"] = NORMAL                                          # Allow start button to be pressed again
                
                self.deviceTime[sensor][0] = t
                self.deviceTime[sensor][1] = time.time()                                        # Save the time we read RTC time at
        except:
            pass

        try:                                                                                    # If this fails no valid data was recieved
            msg = message.payload.decode('utf-8')
        except:
            msg = ""

        if ("ping" in msg or "pong" in msg):                                                    # If a ping or pong was received, send a ping back
            self.sendPayload(sensor, "ping")

            if (keys[0] in sensor):                                                             # If sensor 1 responded set it as connected
                self.top.device1Status.config(text="+")
                self.devices[keys[0]] = 1
            if (keys[1] in sensor):                                                             # If sensor 2 respinded set it as connected
                self.top.device2Status.config(text="+")
                self.devices[keys[1]] = 1

        if (self.waitingForStart[sensor]):                                                      # If waiting for start, check messages for "START" / "FAIL"
            if ("START" in msg):
                self.waitingForStart[sensor] = False
                self.configWasSet[sensor] = True
                self.top.serialOutput.insert("end", "Received the start signal from " +
                                             sensor + "\n") 
                self.top.serialOutput.yview('end')                                              # Autoscroll

            elif ("FAIL" in msg):
                self.waitingForStart[sensor] = False
                self.configWasSet[sensor] = False
                self.top.serialOutput.insert("end", "Received the failure signal from " + 
                                             sensor + "\n") 
                self.top.serialOutput.yview('end')  
                self.top.setDataCaptureFlag(0)
            else:
                self.top.serialOutput.insert("end", "Waiting for response..." + 
                                             sensor + "\n") 
                self.top.serialOutput.yview('end')  
        
        elif (self.configWasSet[sensor]):                                                       # If data capture is in progress
            if ("END" in msg):                                                                  # If end of data capture was reached
                if (keys[0] in sensor):
                    self.top.device1Status.config(text="-")
                    self.devices[keys[0]] = 0
                if (keys[1] in sensor):
                    self.top.device2Status.config(text="-")
                    self.devices[keys[1]] = 0

                self.top.serialOutput.insert("end", "Data Capture from " + 
                                             sensor + " ended\n") 
                self.top.serialOutput.yview('end') 

                # if (self.devices[keys[0]] == 0 or self.devices[keys[0]] == 0):
                #     return

                self.configWasSet[sensor] = False
                      
                for plot in self.top.plotFrames:                                                # Stop all animators so plots can be manipulated manually  
                    plot["animator"].pause()
                
                self.top.captureData = False
                 
                self.writeToFile()
                self.top.dataCaptureLabel.config(bg = "red")
                
                return
        
            # extract timestamp and data values
            for i in range(0, len(message.payload)-1, self.sampleBytes):
                sample = self.unpack(message.payload[i:i+self.sampleBytes])
                data.append(sample)                                                             # "data" variable is passed to plotter function

                self.samples[sensor]["time"].append(sample[0])                                  # self.samples stores data being saved to .csv file

                self.samples[sensor][1].append(sample[1])
                if (self.inputChannels > 1):
                    self.samples[sensor][2].append(sample[2])
                if (self.inputChannels > 2):
                    self.samples[sensor][3].append(sample[3])   

            self.plotData(data, sensor)


    def unpack(self, bytes):
        unpacked = [ bytes[0] << 8 | bytes[1], bytes[2] << 8 | bytes[3] ]                       # Always need to decode timestamp and first channel. Both are 16 bits

        if (self.inputChannels > 1):                                                            # If 2 or 3 channels were used, unpack that data too
            unpacked.append(bytes[4] << 8 | bytes[5])

        if (self.inputChannels > 2):
            unpacked.append(bytes[6] << 8 | bytes[7])

        return unpacked


    def sendPayload(self, deviceID, msg):                                                       # Publish a message to broker
        topic = deviceID + "/CONFIG/"

        result = self.client.publish(topic , msg, qos=2, retain=False)
            
        # result: [0, 1]
        status = result[0]
        if status == 0:
            # print("Sent payload to topic: " + topic)
            pass
        else:
            print(f"Failed to send message to topic: " + topic)


    def sendConfiguration(self, trialTime, fs, inputChannels, deviceID, startTime):             # Send configuration message to start data sampling
        self.samples = {}

        for key in self.top.sensorNames:                                                        # Iterate through connected sensors
            self.samples[key] = {}
            self.samples[key]["time"] = []
            for i in range(int(inputChannels)):                                                 # Add a key and empty list for each channels
                self.samples[key][i+1] = []

        config  = str(trialTime)                                                                # Time in seconds
        config += "," + str(fs)                                                                 # Sample frequency
        config += "," + str(inputChannels)                                                      # Number of input channels
        
        config += "," + str(startTime)                                                          # Send start time which is just device time with a few seconds added
        
        print(deviceID + "\t" + config)
        self.sendPayload(deviceID, config)                                                      # Write configuration to micro
        for key in list(self.devices.keys()):
            self.waitingForStart[key] = True                                                    # Flag that tells on_message() to look for "START"/"FAIL"

        self.inputChannels = int(inputChannels)
        self.sampleBytes = 2 + (self.inputChannels * 2)


    def writeToFile(self):
        filename = self.top.outputFilenameEntry.get() + ".csv"
        # time.sleep(1)
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file)
            
            row = []
            for sensor in self.top.sensorNames:
                row.append(sensor)                                                              # Make header with sensor name
                for ch in self.samples[sensor]:                                                 # Append empty line for each channel
                    if (str(ch) in "time"):
                        continue
                    row.append("")
            
            writer.writerow(row)
            
            row = []
            num = 0
            for sensor in self.top.sensorNames:
                row.append("Time")                                                              # Make header with sensor time and channel names
                num = 1
                for ch in self.samples[sensor]:                                                 # Append channel name
                    if (str(ch) in "time"):
                        continue
                    row.append("CH" + str(num))
                    num += 1
            
            writer.writerow(row)
            
            # This is ridiculous... why did I do list comprehension. It works though
            length = min(len(inner_array) for sensor_data in self.samples.values() 
                         for inner_array in sensor_data.values() if isinstance(inner_array, list))

            fs = int(self.top.dataCaptureFrequency.get())
            for sensor in self.top.sensorNames:
                self.samples[sensor]["time"] = [i / fs for i in range(0, length)]

            for sample in range(length):
                row = []
                for sensor in self.top.sensorNames:
                    for ch in self.samples[sensor]:                                             # CH can be the channel number or "time" key
                        row.append(self.samples[sensor][ch][sample])
                writer.writerow(row)
                

    def plotData(self, data, sensor):                                                           # Plot data in embedded plots
        index = 0                                                                               # Holds a calculated index that is used multiple times
        sensorNum = 0
        samplePeriod = 1.0 / int(self.top.dataCaptureFrequency.get()) 
        
        for key in list(self.devices.keys()):
            sensorNum += self.devices[key]                                                      # Increment for every connected sensor
            if key in sensor:
                break
        
        chs = [i for i in range(int(self.top.inputChannels.get()))]
        for sample in data:

            if (len(sample) < 2):                                                               # If the line did not have two parts
                continue
            
            for ch in chs:

                # Gotta be an easier more efficient way, this works though
                for i in range(len(self.top.plotFrames)):
                    if (self.top.plotFrames[i]["mask"] == (sensorNum-1, ch)):
                        index = i
                        break
                
                voltage = sample[ch+1] / 1023.0 * 3.3
                self.top.plotFrames[index]["data"].append(voltage)
                
                if (len(self.top.plotFrames[index]["xAxis"]) == 0):
                    self.top.plotFrames[index]["xAxis"].append(0.0)
                else:
                    self.top.plotFrames[index]["xAxis"].append((self.top.plotFrames[index]["xAxis"][-1]+samplePeriod))

                if (voltage > 3.3):
                    print("BAD VOLTAGE PLOTTING\nValue: " + str(voltage))

        if (self.configWasSet[sensor] == False):                                                # If the data capture has finished, stop the animator
            time.sleep(0.3)
            for plot in self.top.plotFrames:
                plot["animator"].pause()