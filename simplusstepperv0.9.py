# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 21:37:03 2021

@author: THz-FCS
"""

import serial
import pyvisa as visa              #Had to import from pyvisa to get it to work in new workstation
import time

#frequencycounter
rm = visa.ResourceManager()
rm.list_resources()
inst = rm.open_resource('GPIB0::3::INSTR')

#synth
synth = rm.open_resource('GPIB0::21::INSTR')

#SIM900
ser = serial.Serial('COM4', 9600, timeout = 3)
time.sleep(0.001)

#Working range decided to be 79.2179 to 79.239 MHz

#ser1 is master stepper
ser1 = serial.Serial(
    'COM6', 9600, 
    timeout = 3,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)

#ser2 is probe stepper
ser2 = serial.Serial(
    'COM7', 9600, 
    timeout = 3,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)

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

def reprates():
    print(getrepratePU())
    print(getrepratePR())

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
    while abs(target-getrepratePU()) > 5:
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
    

def setsimzero():
    ser.write(str.encode('CONN 1, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    time.sleep(0.001)   
    ser.write(str.encode('MOUT 0.00 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.write(str.encode('CONN 3, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    time.sleep(0.001)   
    ser.write(str.encode('MOUT 0.00 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.write(str.encode('CONN 5, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    ser.write(str.encode('xyz\n'))
    
    
def steptotargetPU(targetPU):    
    Hzperstep = 795/50000    #tuned
    repratern = getrepratePU()
    print(repratern)
    diff = targetPU - repratern
    if abs(diff) < 150:  #arbitrary, small movements too inconsistent
        print('diff < 150, switch to PZT control')
    elif abs(diff) > 25000:   #arbitrary
        print('diff > 25000, out of range')
    else:
        #print(diff)
        diffinsteps = diff/Hzperstep
        #print(diffinsteps)
        
        if diffinsteps > 0:
            direction = 'P'
        else:
            direction = 'D'
        #print(direction)    
        
        newsteps = round(abs(diffinsteps))
        #print(newsteps)
        
        newstring = '/1' + direction + str(newsteps) +'R\r\n'
        print(newstring)
        
        ser1.write(str.encode(newstring))
        
        waittime = abs(diff)/1400   #tuned
        #print(waittime)
        time.sleep(waittime)
        
        
def steptotargetPU2(targetPU2):
    stepcounter = 0
    while abs(targetPU2 - getrepratePU()) > 150:
        print('steptotargetPU2')
        steptotargetPU(targetPU2)
        stepcounter += 1
    else:
        print(stepcounter)
        steptotargetPU(targetPU2)
          
        
def steptotargetPR(targetPR):    
    Hzperstep = 791/50000 #tuned
    repratern = getrepratePR()
    print(repratern)
    diff = targetPR - repratern
    if abs(diff) < 150:  #arbitrary, small movements too inconsistent
        print('diff < 150, switch to PZT control')
    elif abs(diff) > 25000:   #arbitrary
        print('diff > 25000, out of range')
    else:
        #print(diff)
        diffinsteps = diff/Hzperstep
        #print(diffinsteps)
        
        if diffinsteps > 0:
            direction = 'D'
        else:
            direction = 'P'
        #print(direction)    
        
        newsteps = round(abs(diffinsteps))
        #print(newsteps)
        
        newstring = '/1' + direction + str(newsteps) +'R\r\n'
        print(newstring)
        
        ser2.write(str.encode(newstring))
        
        waittime = abs(diff)/1400   #tuned
        #print(waittime)
        time.sleep(waittime)
        
        
def steptotargetPR2(targetPR2):
    stepcounter = 0
    while abs(targetPR2 - getrepratePR()) > 150:
        print('steptotargetPR2')
        steptotargetPR(targetPR2)
        stepcounter += 1
    else:
        print(stepcounter)
        steptotargetPR(targetPR2)
 
    
def totargetstart(target, offset):
    #setfreqsynth
    setfreqsynth(target)
    
    setsimzero()
    while abs(target-getrepratePU()) > 1000:
        steptotargetPU2(target)
    else:
    
        #pump lock
        ser.write(str.encode('CONN 1, "xyz"\n'))
        time.sleep(0.001)
        ser.write(str.encode('AMAN 0 \n'))
        totarget2(target)
        ser.write(str.encode('AMAN 1 \n'))
        ser.write(str.encode('xyz\n'))
        time.sleep(0.001)
        #totarget2 takes about a second, even though totarget takes < 0.5 s....
   
    while abs((target-offset)-getrepratePR()) > 1500:
        steptotargetPR2(int(target-offset))
    else:
        
        #probe tofreq
        ser.write(str.encode('CONN 3, "xyz"\n'))
        time.sleep(0.001)
        ser.write(str.encode('AMAN 0 \n'))
        newtarget = int(target-offset)
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
        
def totargetstartnolocks(target, offset):
    #setfreqsynth
    setfreqsynth(target)
    
    setsimzero()
    while abs(target-getrepratePU()) > 1000:
        steptotargetPU2(target)
    else:
    
        #pump lock
        ser.write(str.encode('CONN 1, "xyz"\n'))
        time.sleep(0.001)
        ser.write(str.encode('AMAN 0 \n'))
        totarget2(target)
        # ser.write(str.encode('AMAN 1 \n'))
        ser.write(str.encode('xyz\n'))
        time.sleep(0.001)
        #totarget2 takes about a second, even though totarget takes < 0.5 s....
   
    while abs((target-offset)-getrepratePR()) > 1500:
        steptotargetPR2(int(target-offset))
    else:
        
        #probe tofreq
        ser.write(str.encode('CONN 3, "xyz"\n'))
        time.sleep(0.001)
        ser.write(str.encode('AMAN 0 \n'))
        newtarget = int(target-offset)
        totarget2PR(newtarget)
        ser.write(str.encode('xyz\n'))
        
        #engage PID fast
        # ser.write(str.encode('CONN 5, "xyz"\n'))
        # time.sleep(0.001)
        # ser.write(str.encode('AMAN 1 \n'))
        # ser.write(str.encode('xyz\n'))
        
        # #engage PID slow
        # ser.write(str.encode('CONN 3, "xyz"\n'))
        # time.sleep(0.001)
        # ser.write(str.encode('AMAN 1 \n'))
        # ser.write(str.encode('xyz\n'))
    
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
    time.sleep(0.001)   
    ser.write(str.encode('MOUT 0.00 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.write(str.encode('CONN 3, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    time.sleep(0.001)   
    ser.write(str.encode('MOUT 0.00 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.write(str.encode('CONN 5, "xyz"\n'))
    time.sleep(0.001)
    ser.write(str.encode('AMAN 0 \n'))
    ser.write(str.encode('xyz\n'))
    
    ser.close()
    ser1.close()
    ser2.close()
    


# t1 = time.time()


# totargetstart(79218900, 100)


# print(time.time() - t1)

# time.sleep(10)

# t1 = time.time()
# scanto(79217800)
# print(time.time() - t1)


# synth.write("POW:AMPL 2 dBm\n")

# totargetstart(79214700)

# listfreqsr = range(79214700, 79219001, 100)
# listfreqs = []

# for i in listfreqsr:
#     listfreqs.append(i)
    
# for freq in listfreqs:
#     scanto(freq)
#     time.sleep(10)
    
# listfreqs.reverse()

# for freq in listfreqs:
#     scanto(freq)
#     time.sleep(10)





#PU good from 79214700, PR bad at 79219000, or PU 79219100

#scanto seems to work fine for increments of 100, both directions

