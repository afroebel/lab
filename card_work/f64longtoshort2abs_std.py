# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 22:29:00 2021

@author: THz-FCS
"""


import binascii
import array
import numpy as np
from glob import glob
import matplotlib.pyplot as plt

def loadf64toV(fname):
    plus_minusV = 0.2
    
    with open(fname, 'rb') as f:
        hexdata = binascii.hexlify(f.read())
        
    x = binascii.unhexlify(hexdata)
    y = array.array('d', x)  #this 'd' is equal to double in c to signify a 64-bit num
    z = np.array(y)
    
    v1 = []
    
    for i in range(len(z)):
        vv = plus_minusV*((z[i] - 32768)/32768)
        v1.append(vv)
        
    return v1 

def fftpowerspec_g(data1, mrp):
    Master_rep_rate = mrp
    offset = 100
    f_lowbound = 5E10
    f_upperbound = 3E12
    
    Sfreq = Master_rep_rate
    
    E_field = data1
    fundint = int(Master_rep_rate/offset) #fundamental interval
    E_field = E_field[0:fundint]
    E_field = np.array(E_field)
    
    #Windowing
    # cut_E_field_new = [float(a)*float(b) for a,b in zip(list(np.kaiser(len(E_field),8)),E_field)]
    #
    # num_fft = 2**27
    
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
    
    fstep = freq[1]
    n_lo = int(f_lowbound/fstep)
    n_hi = int(f_upperbound/fstep)
    
    freq = freq[n_lo:n_hi]
    powerspec = powerspec[n_lo:n_hi]
    
    if plotpspec:
        plt.figure()
        # plt.title(fnames[0])  #This will not label it properly... 
        plt.plot(freq,powerspec)
    
        # plt.figure()
        # plt.plot(E_field)
        
        # plt.figure()
        # plt.title(fnames[0])
        # plt.plot(cut_E_field_new)
        plt.show()
    
    if savepspec_p_freq:
        np.savetxt(fnames[0] + 'freq_list.csv',freq)
        np.savetxt(fnames[0] + 'powerspec.csv',powerspec)
        
    return freq, powerspec

def calcabs(freqsl, bckg, smpl):
    
    
    #The threshold might be good to include for readability... 
    # thresh_l = 0.4                    #Noise level above which peaks are clearly peaks...       
    
    freqpeaks = freqsl
    backgroundpeaks = bckg
    samplepeaks = smpl
    
    # samplepeaks = np.array(samplepeaks)
    # backgroundpeaks = np.array(backgroundpeaks)
    
    inten_mag_s = np.sqrt(2*samplepeaks)
    inten_mag_b = np.sqrt(2*backgroundpeaks)
    
    transmission_mag = inten_mag_s/inten_mag_b
    
    percentTRANs_mag = 100*transmission_mag
    
    # absorbance_mag = []
    
    # for i in range(len(transmission_mag)):
    #     transmission_mag_i = transmission_mag[i]
    #     absorbance_mag_i = 100*((1-transmission_mag_i)**2)
    #     absorbance_mag.append(absorbance_mag_i)
    
    
    # transmission = samplepeaks/backgroundpeaks
    #
    # absorbance = -np.log10(transmission)
    #
    # plt.figure()
    # plt.title('backgroundpeaks')
    # plt.plot(freqpeaks,backgroundpeaks)
    #
    # plt.figure()
    # plt.title('transmission')
    # plt.plot(freqpeaks,transmission)
    #
    # plt.figure()
    # plt.title('absorbance')
    # plt.plot(freqpeaks,absorbance_mag)
    
    # plt.show()


    # np.savetxt(fnames[3] + 'absorbance.csv',absorbance)
    
    return percentTRANs_mag
 
def collapseroll(fname,multiplier,roll,mrp):
    v12 = loadf64toV(fname)
    
    fundint = int(mrp/100)
    v3f = np.zeros(fundint)
    
    for i in range(multiplier):
        # print(i)
        v3 = v12[int(i*fundint):int((i+1)*fundint)]
        # print(v3[0])
        # print(v3[-1])
        v3f = np.add(v3f,v3)
    
    v3f = v3f/4    
    v3fr = np.roll(v3f,roll)  #shifts pulse position in record
    plt.figure()
    plt.plot(v3fr)

    return v3fr


plotpspec = False
savepspec_p_freq = False
mrp = 79217900
fundint = int(mrp/100)

multiplier = 4
roll = int(fundint/2)
 
fnames = glob('*.txt')
fnames.sort()   ###Need to make sure files are sorted properly... 





listofstds = []

for i in range(int(len(fnames)/2)):
    fnameb = fnames[2*i]
    fnamei = fnames[2*i+1]
    
    datab = collapseroll(fnameb,multiplier,roll,mrp)
    datas = collapseroll(fnamei,multiplier,roll,mrp)
        
    bgall = fftpowerspec_g(datab, mrp)
    sall = fftpowerspec_g(datas, mrp)
    
    freqsl = bgall[0]
    bckg = bgall[1]
    smpl = sall[1]
        
    pctTrans = calcabs(freqsl, bckg, smpl)
    
    stdpctT = np.std(pctTrans[4000:10000])  # in 792179 case from 366.858 to 842.165 GHz
    listofstds.append(stdpctT)
    
    plt.figure()
    plt.title(fnamei + '\n' + str(stdpctT))
    plt.plot(freqsl[4000:10000],pctTrans[4000:10000])
    plt.show()
    
    if i ==0:
        accumpctT = pctTrans
    else:
        currentpctT = pctTrans
        accumpctT = np.add(accumpctT,currentpctT)
        
averagepctT = accumpctT/(len(fnames)/2)

stdavgpctT = np.std(averagepctT[4000:10000])
    
plt.figure()
plt.title('average pctT \n' +str(stdavgpctT))
plt.plot(freqsl[4000:10000],averagepctT[4000:10000])
plt.show()

print(np.mean(listofstds))