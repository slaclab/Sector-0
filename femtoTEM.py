#femtoTEM.py --> script used to control the TEM laser locker built for the Flint/Carbide beam shaping laser system in Sector 0.
#Needs to take in the time difference from the SR620 Time Interval Counter, as well as the requested time shift of the User, then decide how to move the devices in the locker
#Needs access to move the TEM QIOffset & ScanOffset to apply I/Q modulation on the TEM system, and also move TPR Trigfgers to delay the Carbide pulses
#TEM adjusts are for fine timing control, with the I/Q modulation allowing for ~1ps resolution steps
#TPR Trigger delays will be used for coarse timing and, eventually, bucket jump correction
##############################################################################################################################################################################

#Import all the libraries needed here
#####################################

import time
import math
import random
import sys
import watchdog
from pylab import *
import epics




#Create variables for each TEM PVs we need to use:
##################################################

QIOffset  = 'QIOffset_PV'
QIActive = 'QIActive_PV'
QIGain = 'QIGain_PV'
ScanEnable = 'ScanEnable_PV'
ScanOffset = 'ScanOffset_PV'
RegOutA = ''
RegOutB = ''
RegOnOff = ''
ErrorScale = ''
RegOnOffA = ''
RegOnOffB = ''
RegOutputOffsetA = ''
RegOutputOffsetB = ''
RegPgainA = ''
RegIgainA = ''
RegDgainA = ''
RegPgainB = ''
RegIgainB = ''
RegDgainB = ''
LockedA = ''
LockedB = ''




#Create variables for SR620 PVs we need:
########################################

current_time = ''
requested_time = ''
time_min = ''
time_max = ''
time_jitter = ''
counter_jitter_high = ''


#Create variables for TPR:
##########################

TPR_1 = ''
TPR_2 = ''
TPR_3 = ''


#Need to add functions to pull and write to various PVs:
########################################################

def get(name): #Pulls current value of PV and updates current variable to match
    try:
        epics.caget(name,timeout=10.0)
        
    except:
        print(f'Unable to read PV: {name}')
        return None

def put(name,val): #Takes current value of variable and writes it to the PV
    try:
        epics.caput(name,val, timeout=10.0)
        print (f'Wrote value {val} to PV: {name}.')
    except:
        print (f'Unable to write value {val} to PV: {name}.')

def read(name): #simple function to read the current value of a PV without updating variable in script
    try:
        epics.cainfo(name)
    except:
        print(f'Unable to read PV: {name}')
        return None


#Need buffer for reading data from SR620: (need to declare buffer size later in code)
#########################################

class CircularBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = [None] * size
        self.head = 0
        self.tail = 0
        self.count = 0

    def is_empty(self):
        return self.count == 0

    def is_full(self):
        return self.count == self.size

    def enqueue(self, item):
        if self.is_full():
            # If the buffer is full, overwrite the oldest element
            self.head = (self.head + 1) % self.size

        self.buffer[self.tail] = item
        self.tail = (self.tail + 1) % self.size
        self.count = min(self.count + 1, self.size)

    def dequeue(self):
        if self.is_empty():
            raise IndexError("Cannot dequeue from an empty buffer")

        item = self.buffer[self.head]
        self.head = (self.head + 1) % self.size
        self.count -= 1
        return item

    def peek(self):
        if self.is_empty():
            raise IndexError("Cannot peek into an empty buffer")

        return self.buffer[self.head]




#Time manipulation functions: Getting current time & jitter from SR620, taking in requested user time, moving TPR or TEM to change time, checking again, etc.
#############################################################################################################################################################

#Class for handling the SR620 Time Interval Counter
#Reads the time and time jitter data
#There's a 1e9 scale factor in here before outputting the time
###############################################################

class time_interval_counter: 
    
    def __init__(self):
        #create circular buffers for adding time & jitter meaurements from SR620
        self.time_buffer = CircularBuffer(11) #create buffer of size 11 for time
        self.jitter_buffer = CircularBuffer(11) #create buffer of size 11 for jitter
        self.time_buffer.enqueue(self.caget('current_time')) #add first element to buffer for time
        self.time_buffer.enqueue(self.caget('time_jitter')) #add first element to buffer for jitter
        
        #scale factor might be needed
        self.scale = 1e9
    
    def get_time(self):
        #Get all our time & jitter variables set up
        jit_high = self.caget('counter_jitter_high')
        jit = self.caget('time_jitter')
        time = self.caget('current_time')
        time_high = self.caget('time_max')
        time_low = self.caget('time_min')
        
        #Do some logic checks
        if time == self.time_buffer.peek():
            print('No new time data to add')
            return None
        if time > time_high or time < time_low:
            print('Time data out of range')
            return None
        if jit > jit_high:
            print('Jitter is too high')
            return None
        
        #Start adding elements now
        self.time_buffer.enqueue(time)
        self.jitter_buffer.enqueue(jit)
        
        return time*self.scale



#For taking in User requested time, figuring out the delta_time and moving TPR or TEM accordingly


























