################################################################################
#   Title: CoreApplication.py
#   Author: Zac Lynn
#   Description: This code implements the user interface required for 
#           the wireless EMG system. 
#
#   Note: For this program to start succesfully the Broker must 
#           already be running.
#
#   Notes: GUI
################################################################################
import tkinter as tk                                                                            # Import tkinter to make the GUI
import tkinter.scrolledtext as st                                                               # Import scrolled text area for the text output
from tkinter import ttk                                                                         # Used for the spinboxes for entering config
from tkinter import Frame, Button, DISABLED                                                     # Import basic gui elements: Frame, Button

from matplotlib.figure import Figure                                                            # Used to create the plots
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg                                 # Used to embed the plots in the GUI
import matplotlib.animation as animation                                                        # Used to continuously update the plots

import CustomToolbar                                                                            # Custom class that adds functions to embedded plots
import MQTT                                                                                     # Custom class to handle wireless communications
import time


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
        self.mqtt = MQTT.MQTT("Laptop", brokerIP='192.168.1.2', top=self)                       # Set IP to 0 or ommit in arguments to connect to localhost

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

    # TODO: Put this in a different class so the core application is not ui setup
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
        self.dataCaptureFrequency.set(1000)
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

        # Create the Frames in the control panel
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
        
        # Create and positions elements in Lower Frame
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

        # Allow all items to scale with parent frame
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

        # Position frame in window
        self.rightFrame.grid(row = 0, column = 1, sticky = "NWSE")

        
    # This function is called periodically from FuncAnimation
    def animate(self, i, xs, ys, ax, line):
        
        line.set_data(xs, ys)                                                                   # Plot the x,y pairs

        if (len(xs) > 1):                                                                       # If data was added, extend the x-axis veiw to show all data
            ax.set_xlim(left=xs[0], right=xs[-1])

        return line,


    def addPlots(self):
        self.rightFrame.configure(bg = "black")
        for frame in self.plotFrames:
            frame["frame"].destroy()

        self.plotFrames = []
        
        for ch in range(self.numChannels):                                                      # Iterate through number of channels (1-3)
            for devNum in range(self.numDevices):                                               # iterate through connected devices (1-2)
                temp = {"frame": Frame(self.rightFrame)}                                        # Create a dictionary to hold objects required for plotting

                # Creating embedded matplotlib figures in a dictionary
                temp["fig"] = Figure(figsize = (6, 2.33), tight_layout = True)                  # Create the figure
                temp["ax"] = temp["fig"].add_subplot(1, 1, 1)                                   # Set the figure up as a subplot for animator function to work well
                temp["line"], = temp["ax"].plot([])                                             # Initialize the data as empty to intialize plot
                temp["canvas"] = FigureCanvasTkAgg(temp["fig"], master = temp["frame"])         # Create TK canvas to embbed the plot inside of
                temp["data"] = []                                                               # Will store the data to be plotted
                temp["xAxis"] = []                                                              

                # Set up the plot to call animate() periodically to draw the plot in real time
                temp["animator"] = animation.FuncAnimation(temp["fig"],                         # Figure to plot in
                                                           self.animate,                        # Animate function
                                                           fargs = (temp["xAxis"],              # X-data
                                                                    temp["data"],               # Y-data
                                                                    temp["ax"],                 # Used to update xAxis view
                                                                    temp["line"]),              # Used to actually update plot
                                                            interval=250,                       # Update every 250 ms
                                                            cache_frame_data=False)             # Each frame is only shown once and not saved, dont need cache       
                # Finish setting up blank plot
                temp["frame"].grid(row = ch, column = devNum, padx = 3,                         # Set the plot position in the canvas and allow it to stetch with window
                                   pady = 3, sticky = "NWSE")

                self.rightFrame.columnconfigure(devNum, weight = 1)                             # The plots are in a grid. Make them all equal in size within grid layout
                self.rightFrame.rowconfigure(ch, weight = 1)

                # Configure the plot with labels and limits for axes
                temp["ax"].set_ylim(bottom = -0.25, top = 3.6)                                  # Set the ylim based on possible voltage values (0-3.3v)
                temp["ax"].set_xlabel("Time (s)")                                               # Add x label
                temp["ax"].set_ylabel("Voltage (v)")                                            # Add y label
                temp["ax"].set_title(str(self.sensorNames[devNum]) + " CH " + str(ch+1))        # Set title using sensor and channel number

                temp["canvas"].draw()                                                           # Draw the canvas to make the plot appear
                temp["canvas"].get_tk_widget().pack(expand=True, fill="both")                   # Elements within the embedded plot must use pack()

                toolbar = CustomToolbar.CustomToolbar(self, temp)                               # Initialize the custom toolbar for each plot
                toolbar.update()                                                                
                temp["canvas"].get_tk_widget().pack()                                           # add the toolbar to the plot            
                temp["mask"] = (devNum, ch)
                self.plotFrames.append(temp)                                                    # Add dictionary to list of plots                                  
            

    def setDataCaptureFlag(self, flag):                                                         # Called when GUI start and stop buttons are pressed 
        if (flag and self.captureData):                                                         # If the flag is already set to the desired state do nothing
            return
        if (flag == 0 and self.captureData == 0):
            return
        
        self.captureData = flag                                                                 # If the state needs to be changed, set it

        if (flag):                                                                              # If data capture needs to start
            self.startDataCapture()
        else:                                                                                   # If the stop button was pushed
            self.stopDataCapture()
            

    def startDataCapture(self): 
        self.numDevices = 0
        self.sensorNames = []
        startTime = []

        ######### Use the RTC time reported by devices to calculate the start time #########
        for device in list(self.mqtt.devices.keys()):                                           # Iterate through devices
            if (self.mqtt.devices[device] == 0):                                                # If the deivce is not connected skip over    
                continue

            # start time = (RTC time) + (time since reading RTC) + offset               
            startTime.append(int(self.mqtt.deviceTime[device][0] +                              # Use a start time that is offset seconds in the future 
                            (time.time() - self.mqtt.deviceTime[device][1]) + 
                            self.mqtt.FORWARD_TIME_OFFSET))
            
            self.numDevices += 1                                                                # Keep track of connected devices for setting up embedded plots
            self.sensorNames.append(device)

        if (self.numDevices == 0):                                                              # Check to make sure there is at leas 1 connected device              
            self.serialOutput.insert("end", "No devices are connected\n") 
            self.serialOutput.yview('end')  
            self.captureData = 0
            return                                                                              # Dont continue if no devices are connected
            
        # Range of start times is the range of RTC times. Network 
        # latency is not accounted for so just make sure they are within a few seconds
        # If time synchronization was performed they are with 2-5 ms
        if (max(startTime) - min(startTime) > self.mqtt.FORWARD_TIME_OFFSET):                   # Check the RTC time synchronization
            self.serialOutput.insert("end", "Timing is OFF. Please synch RTCs\n") 
            self.serialOutput.yview('end')  
            self.captureData = 0
            return                                                                              # Dont start the data capture if RTCs are off

        # Save these to variables so chnaging them during test doesnt cause crash
        self.dataLen = int(self.dataCaptureTime.get())                                          
        self.dataFreq = int(self.dataCaptureFrequency.get())                                    
        self.numChannels = int(self.inputChannels.get())

        ######## If time synchronization is good, setup plots and send start signal ########
        self.addPlots()                                                                         # Setup embedded plots in GUI

        for device in list(self.mqtt.devices.keys()):                                           # Send configuration messages to all connected sensors to start sampling                               
            if (self.mqtt.devices[device] == 0):                                                # If the deivce is not connected skip over
                continue
            
            self.mqtt.sendConfiguration(self.dataLen, 
                                        self.dataFreq, 
                                        self.numChannels,
                                        device,
                                        max(startTime))     
        
        self.startButton["state"] = DISABLED                                                    # Disable start button until ready to run another test
        self.dataCaptureLabel.config(bg = "green")                                              # Set data capture label to green
    

    def stopDataCapture(self):
        for device in list(self.mqtt.devices.keys()):                                           # Iterate through devices
            self.mqtt.configWasSet[device] = False                                              # Ends data capture
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