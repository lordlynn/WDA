from subprocess import PIPE, Popen   
import numpy as np
import matplotlib.pyplot as plt

frequency = None
title = None
data = None
t = None

def create_test_data():
    global frequency, title, data, t
    frequency = 2000
    title = "Test Data"

    t = [(i * (1/frequency)) for i in range(10000)]
    t = np.array(t)

    # Create example data of 10Hz and 35Hz sin waves
    data = np.sin(t * (2 * 3.14159) * 10) * 0.75 
    data = data + np.sin(t * (2 * 3.14159) * 35) * 0.5

    # Bias signal so that it it is centered at 1.65v
    data = data + 1.65 
    data = data.tolist()


def start_subProcess(script):
    p = Popen(['python', './customFunctions/' + script],                                     # Start a new process and connect pipes for stdin, stdout, and stderr      
                stdin = PIPE, stdout = PIPE, stderr = PIPE)
    
    TxData = (str(frequency) + "," +                                                       # Combine the sampling frequency, figure title, and figure data to send through pipe
                str(title) + "," + 
                str(data))

    try:                                                                                    # Send the data to new process, timeout will raise exception
        p.communicate(TxData.encode('utf8'), timeout=1)                                     # Setting a timeout makes this non-blocking, freeing main thread to return
    except:
        pass                                                                                # Do nothing with timeout exception so main thread can continue

    # Analysis threads are resposible for killing themselves, 
    # this happens naturally when code execution ends

create_test_data()
start_subProcess("fft.py")


# Plot example data
plt.figure()
plt.plot(t, data)
plt.ylabel("Voltage (v)")
plt.xlabel("Time (s)")
plt.title(title)
plt.ylim((-0.2, 3.7))

plt.show()