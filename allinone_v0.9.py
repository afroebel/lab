# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 08:01:36 2021

@author: THz-FCS
"""

import serial
import pyvisa as visa              #Had to import from pyvisa to get it to work in new workstation
import time

import atsapi as ats
import ctypes
import numpy as np
import matplotlib.pyplot as plt
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
    
####


# Configures a board for acquisition
def ConfigureBoard(board, master_rep_rate):
    global samplesPerSec
    samplesPerSec = master_rep_rate
    board.setCaptureClock(ats.EXTERNAL_CLOCK_AC,
                          ats.SAMPLE_RATE_USER_DEF,
                          ats.CLOCK_EDGE_FALLING,
                          0)
    board.setExternalClockLevel(60) #MAYBE IT ISNT NEEDED?
    
    board.inputControlEx(ats.CHANNEL_A,
                         ats.DC_COUPLING,
                         ats.INPUT_RANGE_PM_200_MV,
                         ats.IMPEDANCE_50_OHM)
    
    board.setBWLimit(ats.CHANNEL_A, 0)
    
    board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                              ats.TRIG_ENGINE_J,
                              ats.TRIG_CHAN_A,
                              ats.TRIGGER_SLOPE_NEGATIVE,
                              117,  #FOR -117.25MV
                              ats.TRIG_ENGINE_K,
                              ats.TRIG_DISABLE,
                              ats.TRIGGER_SLOPE_POSITIVE,
                              128)
    
    board.setExternalTrigger(ats.DC_COUPLING,
                             0)
    
    triggerDelay_sec = 0
    triggerDelay_samples = int(triggerDelay_sec * samplesPerSec + 0.5)
    board.setTriggerDelay(0)  #modified to match log file
    
    # TODO: Set trigger timeout as required.
    #
    # NOTE: The board will wait for a for this amount of time for a
    # trigger event.  If a trigger event does not arrive, then the
    # board will automatically trigger. Set the trigger timeout value
    # to 0 to force the board to wait forever for a trigger event.
    #
    # IMPORTANT: The trigger timeout value should be set to zero after
    # appropriate trigger parameters have been determined, otherwise
    # the board may trigger if the timeout interval expires before a
    # hardware trigger event arrives.
    board.setTriggerTimeOut(0)
    
    # Configure AUX I/O connector as required
    board.configureAuxIO(ats.AUX_OUT_TRIGGER,
                         0)
    
    
#mess with number of buffers?
def AcquireData(board, avgtime, fundint, n_fundints_per_buffer):
    # TODO: Select the total acquisition length in seconds
    acquisitionLength_sec = avgtime
    # TODO: Select the number of samples in each DMA buffer
    samplesPerBuffer = int(fundint*n_fundints_per_buffer)
    
    # TODO: Select the active channels.
    channels = ats.CHANNEL_A
    channelCount = 0
    for c in ats.channels:
        channelCount += (c & channels == c)


    # Compute the number of bytes per record and per buffer
    memorySize_samples, bitsPerSample = board.getChannelInfo()
    bytesPerSample = (bitsPerSample.value + 7) // 8
    bytesPerBuffer = bytesPerSample * samplesPerBuffer * channelCount;
    # Calculate the number of buffers in the acquisition
    samplesPerAcquisition = int(samplesPerSec * acquisitionLength_sec + 0.5);
    buffersPerAcquisition = ((samplesPerAcquisition + samplesPerBuffer - 1) //
                             samplesPerBuffer)

    # TODO: Select number of DMA buffers to allocate
    bufferCount = 20

    # Allocate DMA buffers

    sample_type = ctypes.c_uint8
    if bytesPerSample > 1:
        sample_type = ctypes.c_uint16

    buffers = []
    for i in range(bufferCount):
        buffers.append(ats.DMABuffer(board.handle, sample_type, bytesPerBuffer))
    
    board.beforeAsyncRead(channels,
                          0,                 # Must be 0
                          samplesPerBuffer,
                          1,                 # Must be 1
                          0x7FFFFFFF,        # Ignored
                          ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_CONTINUOUS_MODE)
    


    # Post DMA buffers to board
    for buffer in buffers:
        board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

    start = time.time() # Keep track of when acquisition started
    try:
        board.startCapture() # Start the acquisition
        print("Capturing %d buffers. Press <enter> to abort" %
              buffersPerAcquisition)
        buffersCompleted = 0
        bytesTransferred = 0
        
        argmaxes = []
        
        accum = np.zeros(int(fundint*n_fundints_per_buffer))
        
        while (buffersCompleted < buffersPerAcquisition and not
               ats.enter_pressed()):
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            buffersCompleted += 1
            bytesTransferred += buffer.size_bytes
            
            data = buffer.buffer
            # data = data.astype('float64') 
            # print(len(data))
            
            # plt.plot(data)
            # print(np.argmax(data))
            
            argmaxes.append(np.argmax(data))
            
            accum = np.add(accum,data)
            
            # print(accum[0])
            
           
            # TODO: Process sample data in this buffer. Data is available
            # as a NumPy array at buffer.buffer

            # NOTE:
            #
            # While you are processing this buffer, the board is already
            # filling the next available buffer(s).
            #
            # You MUST finish processing this buffer and post it back to the
            # board before the board fills all of its available DMA buffers
            # and on-board memory.
            #
            # Samples are arranged in the buffer as follows:
            # S0A, S0B, ..., S1A, S1B, ...
            # with SXY the sample number X of channel Y.
            #
            #
            # Sample codes are unsigned by default. As a result:
            # - 0x0000 represents a negative full scale input signal.
            # - 0x8000 represents a ~0V signal.
            # - 0xFFFF represents a positive full scale input signal.

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
    finally:
        board.abortAsyncRead()
    # Compute the total transfer time, and display performance information.
    transferTime_sec = time.time() - start
    print("Capture completed in %f sec" % transferTime_sec)
    buffersPerSec = 0
    bytesPerSec = 0
    if transferTime_sec > 0:
        buffersPerSec = buffersCompleted / transferTime_sec
        bytesPerSec = bytesTransferred / transferTime_sec
    print("Captured %d buffers (%f buffers per sec)" %
          (buffersCompleted, buffersPerSec))
    print("Transferred %d bytes (%f bytes per sec)" %
          (bytesTransferred, bytesPerSec))
    
    average = accum/buffersPerAcquisition
    
    return average, argmaxes


def collectspectrum(mrr, offst, n_teeth, avgtime):
    master_rep_rate = mrr
    offset = offst
    fundint = master_rep_rate/offset
    n_fundints_per_buffer = n_teeth
    timeavg = avgtime
    
    board = ats.Board(systemId = 1, boardId = 1)
    ConfigureBoard(board, master_rep_rate)
    
    avg, argmaxs = AcquireData(board, avgtime, fundint, n_fundints_per_buffer)
    
    return avg, argmaxs, master_rep_rate, offset, timeavg



    
    
# #save format = date_time_rep_rate_offset_timeavg
# def savetxt():
#     dateholder = datetime.now()
#     datestr = dateholder.strftime("%Y%m%d_%H%M")
#     np.savetxt(datestr+'_'+str(rep_rate)+'_'+str(offset)+'_'+str(timeavg)+'secavg_bg.txt', avg)
#     # np.savetxt(datestr+'argmaxes.txt',argmaxs)
#     print('saved '+datestr+' '+str(getrepratePU())+' '+str(getrepratePR()))
 



def collectstep(master_rr, offst):
    # totargetstart(master_rr, offst)  
    time.sleep(10)
    
    avg, argmaxs, rep_rate, offset, timeavg = collectspectrum(master_rr, offst, 4, 300)
    
    plt.figure()
    plt.title(str(timeavg))
    plt.plot(argmaxs)    
    def plotargmaxes(lo, hi):
        argmaxes = []
        
        for i in argmaxs:
            if i < hi and i > lo:
                argmaxes.append(i)
                 
        plt.figure()
        plt.plot(argmaxes)
    
    plotargmaxes(0,800000)
    
    plt.figure()
    plt.title(str(timeavg))
    plt.plot(avg)
    
    plt.show()
    
    print('000000000000000000000000000000')
    print('000000000000000000000000000000')
    print('000000000000000000000000000000')
    
    dateholder = datetime.now()
    datestr = dateholder.strftime("%Y%m%d_%H%M")
    np.savetxt(datestr+'_'+str(rep_rate)+'_'+str(offset)+'_'+str(timeavg)+'secavg_bg.txt', avg)
    # np.savetxt(datestr+'argmaxes.txt',argmaxs)
    print('saved '+datestr+' '+str(getrepratePU())+' '+str(getrepratePR()))
    
   
    time.sleep(10)
    
    print('111111111111111111111111111111')
    print('111111111111111111111111111111')
    print('111111111111111111111111111111')

    
    ###
    
    avg, argmaxs, rep_rate, offset, timeavg = collectspectrum(master_rr, offst, 4, 300)
    
    plt.figure()
    plt.title(str(timeavg))
    plt.plot(argmaxs)    
    def plotargmaxes(lo, hi):
        argmaxes = []
        
        for i in argmaxs:
            if i < hi and i > lo:
                argmaxes.append(i)
                 
        plt.figure()
        plt.plot(argmaxes)
    
    plotargmaxes(0,800000)
    
    plt.figure()
    plt.title(str(timeavg))
    plt.plot(avg)
    
    print('000000000000000000000000000000')
    print('000000000000000000000000000000')
    print('000000000000000000000000000000')
    
    dateholder = datetime.now()
    datestr = dateholder.strftime("%Y%m%d_%H%M")
    np.savetxt(datestr+'_'+str(rep_rate)+'_'+str(offset)+'_'+str(timeavg)+'secavg_expansion.txt', avg)
    # np.savetxt(datestr+'argmaxes.txt',argmaxs)
    print('saved '+datestr+' '+str(getrepratePU())+' '+str(getrepratePR()))




# while True:
#     avg, argmaxs, rep_rate, offset, timeavg = collectspectrum(79216500, 100, 4, 1)
    
#     # plt.figure()
#     # plt.plot(argmaxs)    
     
#     # plotargmaxes(0,800000)
    
#     plt.figure()
#     plt.plot(avg)
#     plt.show()

# times = [10,10,300,300,600,600,1200,1200,300,300,300,300,300,300,300,300,150,150]

# for timei in times:    
#     avg, argmaxs, rep_rate, offset, timeavg = collectspectrum(79216500, 100, 4, timei)
    
#     plt.figure()
#     plt.title(str(timeavg))
#     plt.plot(argmaxs)    
     
#     plotargmaxes(0,800000)
    
#     plt.figure()
#     plt.title(str(timeavg))
#     plt.plot(avg)
    
#     savetxt()