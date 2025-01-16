# PROJECT SUMMARY - WDA (Wireless Data Acquisition)

This WDA system has two main components that facilitate the wireless data acquisition. First is the embedded portion that records data and wirelessly reports that data over WiFi. Second is the PC portion, which records the data sent over WiFi and operates a MQTT broker in order to facilitate the data transfer.

The embedded portion of the project utilizes a Teensy4.1 microcontroller in order to record data and run the main program. The WizFi360 board was paired with the Teensy4.1 in order to send the data over MQTT to the core application.

Any computer capable of running Python3 applications and an MQTT broker simultaneously will be sufficient for the PC portion of the system. 

Any WiFi router can be used as the middleman between the embedded and PC systems. The only requirements are that you are able to use static IP addresses. The IP address for the broker must be set statically, so that the embedded devices can be programmed with the correct IP. The default is 192.168.1.2.

# Core application
The core application is the code that will run on a laptop. In order for this program to work you must first start the MQTT broker.

# Teensy WiFi Arduino
The embedded code is under the TeensyWiFi_ARDUINO folder. This is set up for use with Arduino IDE.

** The TeensyWiFi folder is a slightly older version of the code which is set up for use with VSCode and PlatformIO
