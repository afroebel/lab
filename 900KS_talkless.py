#Based on AR_NotRecommended... It might be an improvement to try with data streaming...

from __future__ import division
import ctypes
import os
import time
import numpy as np

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

def AcquireData(board):
    preTriggerSamples = 44992
    postTriggerSamples = 855008

    # TODO: Select the number of records in the acquisition.
    recordsPerCapture = 1

    # TODO: Select the amount of time to wait for the acquisition to
    # complete to on-board memory.
    acquisition_timeout_sec = 10

    # TODO: Select the active channels.
    channels = ats.CHANNEL_A
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
    samplesPerRecord = preTriggerSamples + postTriggerSamples
    bytesPerRecord = bytesPerSample * samplesPerRecord

    # Calculate the size of a record buffer in bytes. Note that the
    # buffer must be at least 16 bytes larger than the transfer size.
    bytesPerBuffer = (bytesPerSample *
                      (samplesPerRecord + 0))

    # Set the record size
    board.setRecordSize(preTriggerSamples, postTriggerSamples)

    # Configure the number of records in the acquisition
    board.setRecordCount(recordsPerCapture)

    start = time.time() # Keep track of when acquisition started
    board.startCapture() # Start the acquisition
    # print("Capturing %d record. Press <enter> to abort" % recordsPerCapture)
    buffersCompleted = 0
    bytesTransferred = 0
    while not ats.enter_pressed():
        if not board.busy():
            # Acquisition is done
            break
        if time.time() - start > acquisition_timeout_sec:
            board.abortCapture()
            raise Exception("Error: Capture timeout. Verify trigger")
        time.sleep(10e-3)

    captureTime_sec = time.time() - start
    recordsPerSec = 0
    if captureTime_sec > 0:
        recordsPerSec = recordsPerCapture / captureTime_sec
    # print("Captured %d records in %f rec (%f records/sec)" %
    #       (recordsPerCapture, captureTime_sec, recordsPerSec))

    sample_type = ctypes.c_uint8
    if bytesPerSample > 1:
        sample_type = ctypes.c_uint16

    buffer = ats.DMABuffer(board.handle, sample_type, bytesPerBuffer + 16)

    # Transfer the records from on-board memory to our buffer
    # print("Transferring %d records..." % recordsPerCapture)

    for record in range(recordsPerCapture):
        if ats.enter_pressed():
            break
        for channel in range(channelCount):
            channelId = ats.channels[channel]
            if channelId & channels == 0:
                continue
            board.read(channelId,             # Channel identifier
                       buffer.addr,           # Memory address of buffer
                       bytesPerSample,        # Bytes per sample
                       record + 1,            # Record (1-indexed)
                       -preTriggerSamples,    # Pre-trigger samples
                       samplesPerRecord)      # Samples per record
            bytesTransferred += bytesPerRecord;

            # Records are arranged in the buffer as follows:
            # R0A, R1A, R2A ... RnA, R0B, R1B, R2B ...
            #
            #
            # Sample codes are unsigned by default. As a result:
            # - 0x0000 represents a negative full scale input signal.
            # - 0x8000 represents a ~0V signal.
            # - 0xFFFF represents a positive full scale input signal.

            # Optionaly save data to file
            if dataFile:
                buffer.buffer[:samplesPerRecord].tofile(dataFile)

            if ats.enter_pressed():
                break

    # Compute the total transfer time, and display performance information.
    transferTime_sec = time.time() - start
    bytesPerSec = 0
    if transferTime_sec > 0:
        bytesPerSec = bytesTransferred / transferTime_sec
    # print("Transferred %d bytes (%f bytes per sec)" %
          # (bytesTransferred, bytesPerSec))
    data = buffer.buffer[:samplesPerRecord]
    data = np.array(data)
    data = data.astype('float64')     #to get larger numbers...
    return data


def avgcollect(num_avg, fno):
    nustartT = time.time()
    if __name__ == "__main__":
        board = ats.Board(systemId = 1, boardId = 1)
        ConfigureBoard(board)
        for i in range(int(num_avg)):
            if i == 0:
                accum = AcquireData(board)
            else:
                current = AcquireData(board)
                accum = np.add(accum,current)
        # print('total time ' + str(time.time() - nustartT))
                
        average = accum/num_avg
        
        # print('time with avg ' + str(time.time() - nustartT))
        
        # v1 = []
        # plus_minusV = 0.2
        # for i in range(len(average)):
        #     vv = plus_minusV*((average[i] - 32768)/32768)
        #     v1.append(vv)
            
        # print('time with Vconv ' + str(time.time() - nustartT))  ##Takes over half a second.... 
        
        # np.savetxt('data0.txt',average)
        
        # print('time with np.save ' + str(time.time() - nustartT))  #takes about 2 seconds...
        
        f = open(str(num_avg)+"avgopfile"+str(fno)+".txt", "w")
        average.tofile(f)
        f.close()
            
        print('time with opfilesave ' + str(time.time() - nustartT))  #about 5 ms!!
        
f4avgtimestart = time.time()

for i in range(100):
    avgcollect(100,i)
    
print('avging time' + str(time.time() - f4avgtimestart))

f4avgtimestart = time.time()

for i in range(40):
    avgcollect(250,i)
    
print('avging time' + str(time.time() - f4avgtimestart))
    
f4avgtimestart = time.time()

for i in range(20):
    avgcollect(500,i)
    
print('avging time' + str(time.time() - f4avgtimestart))

    
f4avgtimestart = time.time()

for i in range(10):
    avgcollect(1000,i)
    
print('avging time' + str(time.time() - f4avgtimestart))

f4avgtimestart = time.time()

for i in range(4):
    avgcollect(2500,i)
    
print('avging time' + str(time.time() - f4avgtimestart))

f4avgtimestart = time.time()

for i in range(2):
    avgcollect(5000,i)
    
print('avging time' + str(time.time() - f4avgtimestart))


# board.configureAuxIO(14, 0) #TTL OFF
# board.configureAuxIO(14, 1) #TTL ON

