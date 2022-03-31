# -*- coding: utf-8 -*-
"""
Created on Mon May 17 15:47:10 2021

@author: THz-FCS
"""

import serial
import pyvisa as visa              #Had to import from pyvisa to get it to work in new workstation
import time
from datetime import datetime

#frequencycounter
rm = visa.ResourceManager()
rm.list_resources()
inst = rm.open_resource('GPIB0::3::INSTR')

#synth
synth = rm.open_resource('GPIB0::21::INSTR')

#SIM900
ser = serial.Serial('COM4', 9600, timeout = 3)
time.sleep(0.001)

def getrepratePU():
    inst.write("FU1")
    with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
        masterdata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    x = a.find("F")
    masterfreq = float(a[x+4:x+14])*10**7
    # print(masterfreq)
    return masterfreq

def getrepratePR():
    inst.write("FU3")
    with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
        masterdata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    x = a.find("F")
    masterfreq = float(a[x+4:x+14])*10**7
    # print(masterfreq)
    return masterfreq

def totarget(target, HzpV):
    repratern = getrepratePU()
    diff = target - repratern
    diffinV = -diff/HzpV  
   
    ser.write(str.encode('MOUT? \n'))
    time.sleep(0.001)
    a = str(ser.readline())
    manv = float(a[2:8])
    newmanv = manv + diffinV
    
    if abs(newmanv) < 5:
        ser.write(str.encode('MOUT ' +str("%.3f" % round(newmanv, 3)) + ' \n'))
    else:
        print('ERROR: newmanv out of range')

def totarget2(target):
    totarget(target, 500)
    while abs(target-getrepratePU()) > 10:
        print('totarget2')
        totarget(target, 500)
    else:
        print('reached target ' + str(target))
        
def totargetPR(target, HzpV):
    repratern = getrepratePR()
    diff = target - repratern
    diffinV = -diff/HzpV  
   
    ser.write(str.encode('MOUT? \n'))
    time.sleep(0.001)
    a = str(ser.readline())
    manv = float(a[2:8])
    newmanv = manv - diffinV
    
    if abs(newmanv) < 5:
        ser.write(str.encode('MOUT ' +str("%.3f" % round(newmanv, 3)) + ' \n'))
    else:
        print('ERROR: newmanv out of range')
        
def totarget2PR(target2):
    totargetPR(target2, 800)
    while abs(target2-getrepratePR()) > 5:
        print('totarget2PR')
        totargetPR(target2, 800)
    else:
        print('PR reached target ' + str(target2))
        
def setfreqsynth(synthfreq):
    synthfreq = int(synthfreq * 12)
    synth = rm.open_resource('GPIB0::21::INSTR')
    Command = 'FREQ '+str(synthfreq)+' Hz\n'
    synth.write(Command)
    
def totargetstart(target):
    #setfreqsynth
    setfreqsynth(target)
    
    #pump lock
    ser.write(str.encode('CONN 1, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    totarget2(target)
    ser.write(str.encode('AMAN 1 \n'))
    ser.write(str.encode('xyz\n'))
    time.sleep(0.001)
    #totarget2 takes about a second, even though totarget takes < 0.5 s....
   
    #probe tofreq
    ser.write(str.encode('CONN 3, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    newtarget = int(target-100)
    totarget2PR(newtarget)
    ser.write(str.encode('xyz\n'))
    
    #engage PID fast
    ser.write(str.encode('CONN 5, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 1 \n'))
    ser.write(str.encode('xyz\n'))
    
    #engage PID slow
    ser.write(str.encode('CONN 3, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 1 \n'))
    ser.write(str.encode('xyz\n'))
    
def scanto(newfreq):
    ser.write(str.encode('CONN 1, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    setfreqsynth(newfreq)
    totarget2(newfreq)
    ser.write(str.encode('AMAN 1 \n'))
    ser.write(str.encode('xyz\n'))
    
    
def shtdwn():
    ser.write(str.encode('CONN 1, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.write(str.encode('CONN 3, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.write(str.encode('CONN 5, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.close()



holdstr = []

totargetstart(79217900)

str1 = 'started '+str(datetime.now()) 
holdstr.append(str1)

holdstr
