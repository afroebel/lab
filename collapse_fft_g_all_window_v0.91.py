import numpy as np
import matplotlib.pyplot as plt
from glob import glob

Master_rep_rate = 79220700
Sfreq = Master_rep_rate
offset = 100

fnames = glob('*.txt')
fnames.sort()

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
    
    
    
    # print((time.time())-StartTime) #77.7s
    
    # print(j)
    # print(fnames[j])
    
    plt.figure()
    # plt.title(fnames[j])
    plt.plot(freq,powerspec)
    
    print('done')
    
    return freq, powerspec

for j in range(len(fnames)):

    print(j)

    #this is faster than np.loatxt, gets rid of first value...
    # data_longDF = pd.read_csv(fnames[j], header=None)
    # data_longnp = data_longDF.to_numpy()
    
    data_t = np.loadtxt(fnames[j])

    plt.figure()
    plt.title(fnames[j])
    plt.plot(data_t)

    fundint = int(Master_rep_rate/offset) #fundamental interval

    n_records = int(np.ceil((len(data_t)+1)/fundint)-1)
    print('no. of records '+str(n_records))

    for i in range(n_records):
        record_i = data_t[int(i*fundint):int((i+1)*fundint)]
        if i == 0:
            record_sum = record_i
        else:
            record_sum = record_sum + record_i

    record_avg = record_sum/n_records

    plt.figure()
    plt.plot(record_avg)

    #rotate
    
    argmax = np.argmax(record_avg)
    rotavg = rotate(record_avg, argmax - len(record_avg)//2)
    plt.figure()
    plt.plot(rotavg)
    
    #windowing
    
    cut_E_field_new = [float(a)*float(b) for a,b in zip(list(np.kaiser(len(rotavg),8)),rotavg)]
    cut_E_field_new = np.array(cut_E_field_new)

    freq, powerspec = Fourier_transform(cut_E_field_new)

    np.savetxt(fnames[j] + 'freq_list.csv',freq)
    np.savetxt(fnames[j] + 'powerspec.csv',powerspec)

plt.show()
