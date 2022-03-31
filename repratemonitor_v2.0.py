import pyvisa as visa              #Had to import from pyvisa to get it to work in new workstation
import time
from datetime import datetime
import numpy as np

rm = visa.ResourceManager()
rm.list_resources()

inst = rm.open_resource('GPIB0::3::INSTR')

# def purate():
#     inst.write("FU1")
#     masterdata = inst.visalib.read(inst.session,17)
#
# def prrate():
#     inst.write("FU3")
#     slavedata = inst.visalib.read(inst.session,17)

masterfreq = 0
# slavefreq = 0

pumpholder = 0
# probeholder = 0

switchcounter = False

while True:
    inst.write("FU1")
    masterdata = inst.visalib.read(inst.session,17)
    time.sleep(0.25)
    inst.write("FU3")
    slavedata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    b = str(slavedata[0])
    x = a.find("F")
    y = b.find("F")
    
    pumpholder1 = pumpholder
    # probeholder1 = probeholder    
    
    pumpholder = masterfreq
    # probeholder = slavefreq
    
    masterfreq = float(a[x+4:x+14])*10**7
    slavefreq = float(b[y+4:y+14])*10**7
    diff = masterfreq - slavefreq
    
    diffA = abs(masterfreq - pumpholder)
    diffB = abs(pumpholder - pumpholder1)
    diffC = abs(masterfreq - pumpholder1)
    
    if switchcounter:
        if diffA > 10 or diffB > 10 or diffC > 10:
            print('LOST LOCK!!! ' + str(datetime.now()))
            switchcounter = False
        else:
            switchcounter = True
            
    else:
        if diffA < 10 and diffB < 10 and diffC < 10:
            print('locked ' + str((masterfreq + pumpholder + pumpholder1)/3) + ' ' + str(datetime.now()))
            switchcounter = True
        else:
            switchcounter = False
    
    
    print('PU   ',masterfreq,'PR   ',slavefreq, 'diff   ',diff, "    ",str(datetime.now()))
    time.sleep(0.25)
