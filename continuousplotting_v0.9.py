# -*- coding: utf-8 -*-
"""
Created on Wed Feb  9 15:07:53 2022

@author: THz-FCS
"""

from __future__ import division
import ctypes
import time
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa  

import atsapi as ats


#frequencycounter
rm = visa.ResourceManager()
rm.list_resources()
inst = rm.open_resource('GPIB0::3::INSTR')

Master_rep_rate = 79220700
Sfreq = Master_rep_rate
offset = 100
fundint = int(Master_rep_rate/offset) #fundamental interval

def getrepratePU():
    inst.write("FU1")
    with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
        masterdata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    x = a.find("F")
    masterfreq = float(a[x+4:x+14])*10**7
    # print(masterfreq)
    return masterfreq

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


def plotargmaxes(lo, hi):
    argmaxes = []
    
    for i in argmaxs:
        if i < hi and i > lo:
            argmaxes.append(i)
            
    plt.figure()
    plt.plot(argmaxes)
    

def rotate(l, n):
    return np.concatenate((l[n:], l[:n]))

def Fourier_transform(E_field):
    Fourier_transform = abs(np.fft.fft(E_field))
    
    effSfreq = Sfreq*Master_rep_rate/offset
    efftimestep = 1/effSfreq
    freq = np.fft.fftfreq(E_field.size, d=efftimestep) #d=timestep
    
    powerspec = np.square(Fourier_transform)/4
    
    #Consider only positive frequencies (and double):
    lenFT = len(freq)
    freq = freq[0:int(lenFT/2)]
    powerspec = powerspec[0:int(lenFT/2)]
    powerspec = 2*powerspec
    
    f_lowbound = 5E10
    f_upperbound = 3E12
    fstep = freq[1]
    n_lo = int(f_lowbound/fstep)
    n_hi = int(f_upperbound/fstep)
    
    freq = freq[n_lo:n_hi]
    powerspec = powerspec[n_lo:n_hi]

    return freq, powerspec


plt.ion()


while True:
    avg, argmaxs, rep_rate, offset, timeavg = collectspectrum(Master_rep_rate, offset, 4, 1)
    
    # plt.figure()
    # plt.title(str(timeavg))
    # plt.plot(argmaxs)    
     
    # plotargmaxes(0,800000)
    # plt.show()
    
    argmin = np.argmin(avg)
    rotavg = rotate(avg, argmin)

    plt.figure(1)
    plt.clf()
    plt.title(str(getrepratePU())+' TD')
    plt.plot(rotavg)
    plt.show()
    plt.pause(0.001)
    
    #FFT
    
    data_t = avg
      
    n_records = int(np.ceil((len(data_t)+1)/fundint)-1)
    print('no. of records '+str(n_records))
    
    for i in range(n_records):
        record_i = data_t[int(i*fundint):int((i+1)*fundint)]
        if i == 0:
            record_sum = record_i
        else:
            record_sum = record_sum + record_i
    
    record_avg = record_sum/n_records
    
    #rotate
    
    argmax = np.argmax(record_avg)
    rotavg = rotate(record_avg, argmax - len(record_avg)//2)
    
    #windowing
    
    cut_E_field_new = [float(a)*float(b) for a,b in zip(list(np.kaiser(len(rotavg),8)),rotavg)]
    cut_E_field_new = np.array(cut_E_field_new)
    
    freq, powerspec = Fourier_transform(cut_E_field_new)

    plt.figure(2)
    plt.clf()
    plt.title(str(getrepratePU())+' FFT')
    plt.plot(freq, powerspec)
    plt.show()
    plt.pause(0.001)

# savetxt()