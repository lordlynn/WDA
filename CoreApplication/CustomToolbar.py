########################################################################
#   Title: CustomToolbar.py
#   Author: Zac Lynn
#   Description: This code implements the custom buttons in the user 
#        interface that call the custom analysis functions.
#
########################################################################
from subprocess import PIPE, Popen                                                              # For running analysis functions
from matplotlib.figure import Figure                                                            # Used for embedded plot
from matplotlib.backends.backend_tkagg import (                                                 # Used for custom toolbar
    FigureCanvasTkAgg, NavigationToolbar2Tk)

# Custom toolbar class provides custom analysis functions embedded into plots
class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self, GUI, plotFrame):
        self.GUI = GUI
        self.plotFrame = plotFrame
        
        self.toolitems = [t for t in NavigationToolbar2Tk.toolitems]                            # Add standard buttons
        
        self.toolitems.append(                                                                  # Add buttons for custom functions   
            # Button name, hover hint, icon file name, callback function
            ("fft", "Calculate FFT", "fft", 'fft_callback')
        )
        self.toolitems.append(          
            ("env", "Calculate moving average envelope", "env", 'env_callback')
        )
        self.toolitems.append(          
            ("func1", "Custom function 1", "func1", 'func1_callback')
        )
        self.toolitems.append(          
            ("func2", "Custom function 2", "func2", 'func2_callback')
        )
        self.toolitems.append(          
            ("func3", "Custom function 3", "func3", 'func3_callback')
        )
        self.toolitems.append(          
            ("func4", "Custom function 4", "func4", 'func4_callback')
        )
        self.toolitems.append(          
            ("func5", "custom function 5", "func5", 'func5_callback')
        )

        NavigationToolbar2Tk.__init__(self, plotFrame["canvas"], plotFrame["frame"])


    def start_subProcess(self, script):
        p = Popen(['python', './customFunctions/' + script],                                    # Start a new process and connect pipes for stdin, stdout, and stderr      
                  stdin = PIPE, stdout = PIPE, stderr = PIPE)
        
        TxData = (str(self.GUI.dataCaptureFrequency.get()) + "," +                              # Combine the sampling frequency, figure title, and figure data to send through pipe
                  str(self.plotFrame["ax"].get_title()) + "," + 
                  str(self.plotFrame["data"]))
        

        try:                                                                                    # Send the data to new process, timeout will raise exception
            p.communicate(TxData.encode('utf8'), timeout=1)                                     # Setting a timeout makes this non-blocking, freeing main thread to return
        except:
            pass                                                                                # Do nothing with timeout exception so main thread can continue

        # Analysis threads are resposible for killing themselves, 
        # this happens naturally when code execution ends  
        

    def fft_callback(self):
        self.start_subProcess("fft.py")      
    

    def env_callback(self):
        self.start_subProcess("env.py")


    def func1_callback(self):
        self.start_subProcess("func1.py") 


    def func2_callback(self):
        self.start_subProcess("func2.py")


    def func3_callback(self):
        self.start_subProcess("func3.py")


    def func4_callback(self):
        self.start_subProcess("func4.py")


    def func5_callback(self):
        self.start_subProcess("func5.py")
