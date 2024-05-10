# Write your code here :-)
import board
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction, Pull
import time
import pwmio
import os
import sdioio
import storage

#Setup the SD card inserted into the STM32 Feather board
sd = sdioio.SDCard(
    clock=board.SDIO_CLOCK,
    command=board.SDIO_COMMAND,
    data=board.SDIO_DATA,
    frequency=25000000)

#Mount the storage device and denote the file structure as /sd
vfs = storage.VfsFat(sd)
storage.mount(vfs, '/sd')

#FUNCTION: takes an analog read and converts it to termperature using the
#wheatstone bridge formula
#INPUT: pin to read (pin object)
#OUTPUT: Temperature in degrees C (double)
def get_voltage(pin):
    v = (pin.value * 3.3) / 65536
    g = 3.3
    r1 = 3700
    r4 = 3700
    r2 = 200
    r3 = ( ( g*r1*r2 + g*r4*r1 + v*r1*r4) / (v*r2 - g*r2 - g*r4) )
    temperature = 0.002754*r3 + 43.064
    return temperature

#FUNCTION: Uses PWM to apply control to the Peltier modules
#INPUT: Pin being controlled (pin object), signal (% time on, double)
#OUTPUT: None
def applyHeatControl(pin, signal):
    #Cycle time for the whole PWM cycle is 1 second
    cycle_time = 3.00
    #Signal should be a value between 0 and 1, denotes the
    #percent of the PWM signal that should be on
    on_time = signal*cycle_time

    #Turn on the pin, wait the required time
    pin.value = True
    time.sleep(on_time)
    #Then turn the pin off and wait to complete the cycle time
    pin.value = False
    time.sleep(cycle_time-on_time)


# Initialize a default set temp
set_temp = 30
max_temp = 50
previous_time = time.time()
start_time = time.time()

# Initialize variables for storing instananeous error and accumulated steady state error
error = 0
integral = 0
derivative = 0
control_signal = 0

# Initialize PID values for the controls
kP = 1
kI = 0.1
kD = 0.1

# We need a pin to control the relay board
# All Peltier modules will be doing the same thing, so we only need on pin
en_1_peltier = DigitalInOut(board.D10)

en_1_peltier.direction = Direction.OUTPUT

# Temperature sensors (2, one for peltier, one for water output)
peltier_sensor = AnalogIn(board.A1)
water_sensor = AnalogIn(board.A2)

previous_temp = get_voltage(water_sensor)

time.sleep(1)
# Main Loop
#Open a text document to store temperature data in
with open("/sd/temp.txt", "w") as fp:
    #Run until we reach 5400 seconds (an hour and a half), this is the length of test
    while (previous_time-start_time) < 9000:
        #Print just so I can keep track of how close we are to finishing the test
        print((previous_time-start_time))
        #Take the current time
        now = time.time()
        time_change = int(now - previous_time)
        # Take temp reading from water
        water_temp = get_voltage(water_sensor)
        # Take temp reading from Peltier
        peltier_temp = get_voltage(peltier_sensor)

        #Write the water temperature to the temp file, this is what we're
        #concerned with for testing
        fp.write(str(water_temp))
        fp.write(", ")
        fp.write(str(peltier_temp))
        fp.write(",\r\n")

        print(water_temp)
        print(peltier_temp)

        control_signal = 0.04
        print(control_signal)
        previous_time = now
        # Apply controls to the motor controller
        if peltier_temp < 50:
            applyHeatControl(en_1_peltier, control_signal)
