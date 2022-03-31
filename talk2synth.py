import pyvisa as visa
import time

rm = visa.ResourceManager()
rm.list_resources()
synth = rm.open_resource('GPIB0::21::INSTR')

def setfreqsynth(synthfreq):
    rm = visa.ResourceManager()
    rm.list_resources()
    synth = rm.open_resource('GPIB0::21::INSTR')
    Command = 'FREQ '+str(synthfreq)+' Hz\n'
    synth.write(Command)

synth.write("*CLS\n")  #clear errors

synth.write("*RST\n")  #reset synth

synth.write("POW:AMPL 3.5 dBm\n")

synth.write("OUTP:STAT ON\n")

synth.write("OUTP:STAT OFF\n")

listfreq = [950448000.000, 950448475.172, 950448950.345, 950449425.517]

for i in range(len(listfreq)):
    print(listfreq[i])
    setfreqsynth(listfreq[i])
    time.sleep(15)
    