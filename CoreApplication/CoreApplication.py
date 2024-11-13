########################################################################
#   Title: CoreApplication.py
#   Author: Zac Lynn
#   Description: This code implements the user interface required for 
#           the wireless EMG system. 
#
#   Note: For this program to start succesfully the Broker must 
#           already be running.
########################################################################
import tkinter as tk
import tkinter.scrolledtext as st
from tkinter import *
from tkinter import ttk
import matplotlib.animation as animation
import time

from matplotlib.figure import Figure                                                            # Used for embedded plot
from matplotlib.backends.backend_tkagg import (                                                 # Used for custom toolbar
    FigureCanvasTkAgg, NavigationToolbar2Tk)

import MQTT
import CustomToolbar

class CoreApplication():                                             
    captureData = False                                                                         # Flag to tell if data should be saved to file or not
    window = None                                                                               # Holds reference to the application window
    mqtt = None                                                                                 # Stores MQTT class instance
    plotFrames = []                                                                             # Holds data and necessary objects for the embedded plots
    numDevices = 0                                                                              # Number of connected devices
    sensorNames = []                                                                            # Holds the name of the connected sensor at start of data capture, mainlu used by MQTT class
    bgColor = "blue4"                                                                           # TKinter color to use for window background

    dataLen = None
    dataFreq = None
    numChannels = None

    def __init__(self):
        self.mqtt = MQTT.MQTT("Laptop", brokerIP=0, top=self)                                   # Set IP to 0 or ommit in arguments to connect to localhost

        self.window = tk.Tk()                                                                   # Create applicatio window
        self.window.title("EMG Data Capture")
        self.window.config(bg=self.bgColor)
        self.window.minsize(1000, 500)                                                          # Prevent user from making window to small to focus

        self.setupLeftFrame()                                                                   # Setup controls and serial readout
        self.setupRightFrame()                                                                  # Setup plot area

        self.window.rowconfigure(0, weight = 1, minsize=500)                                    # Configure layout of window
        self.window.columnconfigure(0, weight = 1, minsize=450)
        self.window.columnconfigure(1, weight = 1, minsize=550)
        
        self.mqtt.client.loop_start()                                                           # Begin MQTT looping to automatically poll broker                            
        self.window.mainloop()                                                                  # Open and run main window

    def setupLeftFrame(self): 
        leftFrameColor = "grey"
        
        self.leftFrame = Frame(self.window, bg = self.bgColor)
        self.lowerFrame = Frame(self.leftFrame, bg=leftFrameColor)
        self.middleFrame = Frame(self.leftFrame, bg=leftFrameColor)
        self.output = Frame(self.leftFrame)

        # ----------------- Lower Frame -----------------
        # Sample frequency 
        dataCaptureFrequencyLabel = tk.Label(self.lowerFrame, 
                                             text = "Data Capture Frequency (Hz): ", 
                                             bg=leftFrameColor)

        self.dataCaptureFrequency = tk.StringVar()
        self.dataCaptureFrequency.set(2000)
        dataCaptureFrequencySpinBox = ttk.Spinbox(self.lowerFrame, from_ = 1000, to = 2000, 
                                                  justify="center", increment=50, wrap=True,
                                                  textvariable = self.dataCaptureFrequency)
        
        # Number of Channels 
        inputChannelsLabel = tk.Label(self.lowerFrame, text = "Input Channels: ", 
                                      bg=leftFrameColor)
        self.inputChannels = tk.StringVar()
        self.inputChannels.set(1)
        inputChannelsSpinBox = ttk.Spinbox(self.lowerFrame, from_ = 1, to = 3, 
                                           justify="center", increment = 1, wrap=True,
                                           textvariable = self.inputChannels)

        # Test Length
        dataCaptureTimeLabel = tk.Label(self.lowerFrame, text = "Data Capture Length (s): ", 
                                        bg = leftFrameColor)

        self.dataCaptureTime = tk.StringVar()
        self.dataCaptureTime.set(5)
        dataCaptureTimeSpinBox = ttk.Spinbox(self.lowerFrame, from_ = 1, to = 30, 
                                             justify="center", increment=1, wrap=True,
                                             textvariable = self.dataCaptureTime)
    
        self.outputFilenameEntryLabel = tk.Label(self.lowerFrame, 
                                                 text = "Output file name: ", 
                                                 bg = leftFrameColor)
        self.outputFilenameEntry = tk.Entry(self.lowerFrame)
        self.outputFilenameEntry.insert("end", "test")

        self.stopButton = tk.Button(self.lowerFrame, text = "Stop Data Capture", 
                                    command=lambda: self.setDataCaptureFlag(0))
        
        self.startButton = tk.Button(self.lowerFrame, text = "Start Data Capture", 
                                     command=lambda: self.setDataCaptureFlag(1))
        self.dataCaptureLabel = tk.Label(self.lowerFrame, text = "   ", bg="red")

        # ----------------- Middle Frame -----------------
        # Display connected devices
        self.connectedDevicesLabel = tk.Label(self.middleFrame, 
                                              text = "Connected Devices: ")
        
        self.device1Label = tk.Label(self.middleFrame, text = "Sensor1:")
        self.device1Status = tk.Label(self.middleFrame, text = "-")
        
        self.device2Label = tk.Label(self.middleFrame, text = "Sensor2:")
        self.device2Status = tk.Label(self.middleFrame, text = "-")

        self.connectDevicesBtn = Button(self.middleFrame, text = "Connect to sensors", 
                                        command=lambda: self.connectSensors())

        # ----------------- Serial Output Frame -----------------
        # Setting up Serial output
        self.serialMonitorLabel = tk.Label(self.output, text = "Serial Output ")

        # Creating scrolled text area
        self.serialOutput = st.ScrolledText(self.output, width = 1, height = 1, 
                                            font = ("Times New Roman", 13))

        # Frames
        self.leftFrame.grid(row = 0, column = 0, padx = 10, pady = 5, sticky = "NWSE")
        self.output.grid(row = 0, column = 0, padx = 10, pady = 5, sticky = "NWSE")
        self.middleFrame.grid(row = 1, column = 0, padx = 10, pady = 5, sticky = "NWSE")
        self.lowerFrame.grid(row = 2, column = 0, padx = 10, pady = 5, sticky = "NWSE")
        
        self.leftFrame.rowconfigure(0, weight = 6)
        self.leftFrame.rowconfigure(1, weight = 1)
        self.leftFrame.rowconfigure(2, weight = 1)

        self.leftFrame.columnconfigure(0, weight = 1)
        self.leftFrame.columnconfigure(1, weight = 1)
        self.leftFrame.columnconfigure(2, weight = 1)
        
        # Lower Frame
        self.outputFilenameEntryLabel.grid(row = 0, column = 0, padx = 10, pady = 5, 
                                           sticky = "NWSE")
        self.outputFilenameEntry.grid(row = 0, column = 1, columnspan = 2, padx = 20, 
                                      pady = 5, sticky = "NWSE")

        dataCaptureFrequencyLabel.grid(row = 1, column = 0, padx = 5, pady = 5, 
                                       sticky = "NWSE")
        dataCaptureFrequencySpinBox.grid(row = 1, column = 1, columnspan=2, padx = 20, 
                                         pady = 5, sticky = "NWSE")

        dataCaptureTimeLabel.grid(row = 2, column = 0, padx = 5, pady = 5, 
                                  sticky = "NWSE")
        dataCaptureTimeSpinBox.grid(row = 2, column = 1, columnspan = 2, padx = 20, 
                                    pady = 5, sticky = "NWSE")

        inputChannelsLabel.grid(row = 3, column = 0, padx = 5, pady = 5, 
                                sticky = "NWSE")
        inputChannelsSpinBox.grid(row = 3, column = 1, columnspan = 2, padx = 20,  
                                  sticky = "NWSE")

        self.startButton.grid(row = 4, column = 0, padx = 20, pady = 5, 
                              sticky = "NWSE")
        self.stopButton.grid(row = 4, column = 1, padx = 10, pady = 5, 
                             sticky = "NWSE")
        self.dataCaptureLabel.grid(row = 4, column = 2, padx = 5, pady = 5, 
                                   sticky = "NWSE")

        # Allow all items to scale with parent
        self.lowerFrame.columnconfigure(0, weight = 1)
        self.lowerFrame.columnconfigure(1, weight = 1)
        self.lowerFrame.columnconfigure(2, weight = 1)

        self.lowerFrame.rowconfigure(0, weight = 1)
        self.lowerFrame.rowconfigure(1, weight = 1)
        self.lowerFrame.rowconfigure(2, weight = 1)
        self.lowerFrame.rowconfigure(3, weight = 1)
        self.lowerFrame.rowconfigure(4, weight = 1)
        
        # Adding elements to devices list
        self.connectedDevicesLabel.grid(row = 0, column = 0, sticky = "NWSE")
        self.connectDevicesBtn.grid(row = 1, column = 0, sticky = "NWSE")

        self.device1Label.grid(row = 0, column = 1, sticky = "NWSE")
        self.device1Status.grid(row = 0, column = 2, sticky = "NWSE")

        self.device2Label.grid(row = 1, column = 1, sticky = "NWSE")
        self.device2Status.grid(row = 1, column = 2, sticky = "NWSE")
        
        # Allow text output but not label to grow with parent
        self.middleFrame.rowconfigure(0, weight = 1)
        self.middleFrame.rowconfigure(1, weight = 1)
        self.middleFrame.columnconfigure(0, weight = 1)
        self.middleFrame.columnconfigure(1, weight = 1)
        self.middleFrame.columnconfigure(2, weight = 1)

        # Adding elements to output
        self.serialMonitorLabel.grid(row = 0, column = 0, sticky = "NWSE")
        self.serialOutput.grid(row = 1, column = 0, sticky = "NWSE")

        # Allow text output but not label to grow with parent
        self.output.rowconfigure(0, weight=0)
        self.output.rowconfigure(1, weight = 1)
        self.output.columnconfigure(0, weight = 1)

        
    def setupRightFrame(self):
        self.rightFrame = Frame(self.window, bg = self.bgColor)

        # Adding frames to window
        self.rightFrame.grid(row = 0, column = 1, sticky = "NWSE")

        
    # This function is called periodically from FuncAnimation
    def animate(self, i, xs, ys, ax, line):
        
        line.set_data(xs, ys)
        if (len(xs) > 1):
            ax.set_xlim(left=xs[0], right=xs[-1])

        return line,


    def addPlots(self):
        self.rightFrame.configure(bg = "black")
        for frame in self.plotFrames:
            frame["frame"].destroy()

        self.plotFrames = []
        
        for ch in range(int(self.inputChannels.get(), base = 10)):                              # Iterate through number of channels (1-3)
            for devNum in range(self.numDevices):                                               # iterate through connected devices (1-2)
                temp = {"frame": Frame(self.rightFrame)}                                        # Create a dictionary to hold objects required for plotting

                # Creating embedded matplotlib figure
                temp["fig"] = Figure(figsize = (6, 2.33), tight_layout = True)
                temp["ax"] = temp["fig"].add_subplot(1, 1, 1)
                temp["line"], = temp["ax"].plot([])
                temp["canvas"] = FigureCanvasTkAgg(temp["fig"], master = temp["frame"])
                temp["data"] = []                                                               # Will store the data to be plotted
                temp["xAxis"] = []                                                              

                # Set up the plot to call animate() periodically to draw the plot in real time
                temp["animator"] = animation.FuncAnimation(temp["fig"], self.animate, 
                                                           fargs = (temp["xAxis"], 
                                                                    temp["data"], 
                                                                    temp["ax"], 
                                                                    temp["line"]), 
                                                            interval=250)

                # Finish setting up blank plot
                temp["frame"].grid(row = ch, column = devNum, padx = 3, 
                                   pady = 3, sticky = "NWSE")

                self.rightFrame.columnconfigure(devNum, weight = 1)
                self.rightFrame.rowconfigure(ch, weight = 1)

                # Configure the plot with labels and limits for axes
                temp["ax"].set_ylim(bottom = -0.25, top = 3.6)
                temp["ax"].set_xlabel("Time (s)")                                               # Add x label
                temp["ax"].set_ylabel("Voltage (v)")                                            # Add y label
                temp["ax"].set_title(str(self.sensorNames[devNum]) + " CH " + str(ch+1))        # Set title using sensor and channel number

                temp["canvas"] = FigureCanvasTkAgg(temp["fig"], master=temp["frame"])           # A tk.DrawingArea
                temp["canvas"].draw()                                                           # Draw the area to make the plot appear
                temp["canvas"].get_tk_widget().pack(expand=True, fill="both")                   # Elements within the embedded plot use pack() not grid()

                toolbar = CustomToolbar.CustomToolbar(self, temp)                               # Initialize the custom toolbar
                toolbar.update()                        
                temp["canvas"].get_tk_widget().pack()                                           # add the toolbar to the plot            
                temp["mask"] = (devNum, ch)
                self.plotFrames.append(temp)                                                    # Add dictionary to list of plots                                  
            
        
    def setDataCaptureFlag(self, flag):                                                         # Callback for start and stop button to set flags
        if (flag and self.captureData):                                                         # If the flag is already set to the desired state return
            return
        if (flag == 0 and self.captureData == 0):
            return
        
        self.captureData = flag                                                                 # If the state needs to be chnaged, set it

        if (flag):                                                                              # If data capture needs to start
            startTime = []
            for device in list(self.mqtt.devices.keys()):                                       # Iterate through devices
                if (self.mqtt.devices[device]):                                                 # If the device is still connected    
                    # start time = (RTC time) + (time since reading RTC) + offset               
                    startTime.append(int(self.mqtt.deviceTime[device][0] +                      # Use a start time that is offset seconds in the future 
                                        (time.time() - self.mqtt.deviceTime[device][1]) + 
                                         self.mqtt.FORWARD_TIME_OFFSET))

            # Range of start times is same as range of RTC times. Network 
            # latency is not accounted for so just make sure they are within a few seconds
            if (max(startTime) - min(startTime) > self.mqtt.FORWARD_TIME_OFFSET / 2):
                self.serialOutput.insert("end", "Timing is OFF. Please synch RTCs\n") 
                self.serialOutput.yview('end')  
                self.captureData = 0
                return     

            self.numDevices = 0
            self.sensorNames = []
            for device in list(self.mqtt.devices.keys()):                                       # If the time synchronization was good find connected sensors                                
                if (self.mqtt.devices[device]):
                    self.numDevices += 1
                    self.sensorNames.append(device)

            self.addPlots()                                                                     # Setup embedded plots in GUI, captureData flag is set after plots are made

            for device in list(self.mqtt.devices.keys()):                                       # Send configuration messages to all connected sensors to start sampling                               
                if (self.mqtt.devices[device]):
                    self.dataLen = int(self.dataCaptureTime.get())
                    self.dataFreq = int(self.dataCaptureFrequency.get())
                    self.numChannels = int(self.inputChannels.get())
                    
                    self.mqtt.sendConfiguration(self.dataLen, 
                                                self.dataFreq, 
                                                self.numChannels,
                                                device,
                                                max(startTime))     
            
            self.startButton["state"] = DISABLED                                                # Disable start button until ready to run another test
            self.dataCaptureLabel.config(bg = "green")                                          # Set data capture label to green

        else:                                                                                   # If the stop button was pushed
            for device in list(self.mqtt.devices.keys()):                                       # Iterate through devices
                self.mqtt.configWasSet[device] = False                                          # Ends data capture
            self.dataCaptureLabel.config(bg = "red")                                            # Set data capture label to red 
            self.mqtt.writeToFile()                                                             # Write data to file
            
            
    def connectSensors(self):
        self.mqtt.sendPayload("sensor1", "pong")                                                # Send a "pong" to both sensors
        self.mqtt.sendPayload("sensor2", "pong")

        self.device1Status.config(text="-")                                                     # Update the GUI to show as disconnected
        self.device2Status.config(text="-")

        for device in list(self.mqtt.devices.keys()):                                           # Update flags to be disconnected
            self.mqtt.devices[device] = 0 

        # If devices are connected they will respond and their flags will be set 

        
SM = CoreApplication()