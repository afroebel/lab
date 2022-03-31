# -*- coding: utf-8 -*-
"""
Created on Wed Feb  9 10:39:32 2022

@author: THz-FCS
"""

from __future__ import division
import ctypes
import time
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pyvisa as visa              #Had to import from pyvisa to get it to work in new workstation

import atsapi as ats


# #frequencycounter
# rm = visa.ResourceManager()
# rm.list_resources()
# inst = rm.open_resource('GPIB0::3::INSTR')



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


# def getrepratePU():
#     inst.write("FU1")
#     with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
#         masterdata = inst.visalib.read(inst.session,17)
#     a = str(masterdata[0])
#     x = a.find("F")
#     masterfreq = float(a[x+4:x+14])*10**7
#     # print(masterfreq)
#     return masterfreq

# def getrepratePR():
#     inst.write("FU3")
#     with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
#         masterdata = inst.visalib.read(inst.session,17)
#     a = str(masterdata[0])
#     x = a.find("F")
#     masterfreq = float(a[x+4:x+14])*10**7
#     # print(masterfreq)
#     return masterfreq


def plotargmaxes(lo, hi):
    argmaxes = []
    
    for i in argmaxs:
        if i < hi and i > lo:
            argmaxes.append(i)
            
    plt.figure()
    plt.plot(argmaxes)
    
    
#save format = date_time_rep_rate_offset_timeavg
# def savetxt():
#     dateholder = datetime.now()
#     datestr = dateholder.strftime("%Y%m%d_%H%M")
#     np.savetxt(datestr+'_'+str(rep_rate)+'_'+str(offset)+'_'+str(timeavg)+'secavg_testing.txt', avg)
#     # np.savetxt(datestr+'argmaxes.txt',argmaxs)
#     print('saved '+datestr+' '+str(getrepratePU())+' '+str(getrepratePR()))
 

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

while True:
    avg, argmaxs, rep_rate, offset, timeavg = collectspectrum(79228400, 100, 4, 10)
    
    # plt.figure()
    # plt.title(str(timeavg))
    # plt.plot(argmaxs)    
     
    plotargmaxes(0,800000)
    plt.show()

# plt.figure()
# plt.title(str(timeavg))
# plt.plot(avg)

# savetxt()