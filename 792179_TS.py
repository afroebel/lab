from __future__ import division
import ctypes
import os
import time
import numpy as np
import matplotlib.pyplot as plt

import atsapi as ats

# Configures a board for acquisition
def ConfigureBoard(board):
    global samplesPerSec
    samplesPerSec = 79217900.0
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
    
    
def AcquireData(board,fno):
    # TODO: Select the total acquisition length in seconds
    acquisitionLength_sec = 30.

    # TODO: Select the number of samples in each DMA buffer
    multiplier = int(4)
    samplesPerBuffer = int(792179*multiplier)
    
    # TODO: Select the active channels.
    channels = ats.CHANNEL_A | ats.CHANNEL_B
    channelCount = 0
    for c in ats.channels:
        channelCount += (c & channels == c)

    # TODO: Should data be saved to file?
    saveData = False
    dataFile = None
    if saveData:
        dataFile = open(os.path.join(os.path.dirname(__file__),
                                     "data.bin"), 'wb')

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
                          ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_TRIGGERED_STREAMING)
    


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
        # argmax = []
        accum = np.zeros(int(792179*multiplier))
        while (buffersCompleted < buffersPerAcquisition and not
               ats.enter_pressed()):
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = buffers[buffersCompleted % len(buffers)]
            board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000)
            buffersCompleted += 1
            bytesTransferred += buffer.size_bytes
            
            data = buffer.buffer[:samplesPerBuffer]
            data = data.astype('float64')
            accum = np.add(accum, data)
            # print(len(data))
            argmax = np.argmax(data[0:1000000])
            # print(argmax)
            if abs(argmax-792150) > 20:
                print(argmax)
            # argmax.append(np.argmax(data[0:1000000]))  ##Could maybe use this to improve locks... 
            # plt.plot(data)

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
            # Optionaly save data to file
            if dataFile:
                buffer.buffer.tofile(dataFile)

            # Add the buffer to the end of the list of available buffers.
            board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
        # plt.plot(argmax)
        plt.plot(accum)
        average = accum/buffersPerAcquisition
        # print('lenaccum',len(accum)/multiplier)
        # print('lenavg',len(average)/multiplier)
        f = open('m'+str(fno).zfill(3)+'x'+str(acquisitionLength_sec)+"secopfile.txt", "w")
        average.tofile(f)
        f.close()
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

if __name__ == "__main__":
    board = ats.Board(systemId = 1, boardId = 1)
    ConfigureBoard(board)
    time1 = time.time()
    for i in range(2): 
        AcquireData(board,i)
    print('time',time.time()-time1)