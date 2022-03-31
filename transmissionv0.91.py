import numpy as np
import matplotlib.pyplot as plt
from glob import glob

master_reprate = 79228400
thresh_l = 0.4                    #Noise level above which peaks are clearly peaks...
plusminusf = 10000000

fnames = glob('*csv')
fnames.sort()

fnames

freqlist = np.loadtxt(fnames[2])

sample = np.loadtxt(fnames[3])

background = np.loadtxt(fnames[1])

# freqintvl = freqlist[1] - freqlist[0]
#
# plusminus_i = int(plusminusf/freqintvl)
#
# i_firstpeak = np.argmax(background[0:int(master_reprate/freqintvl)])
# f_firstpeak = freqlist[i_firstpeak]
# n_firsttooth = int(np.rint(freqlist[i_firstpeak]/master_reprate))
# n_lasttooth = int(np.rint(freqlist[-200]/master_reprate))

freqpeaks = freqlist
backgroundpeaks = background
samplepeaks = sample


# for i in np.arange(n_firsttooth,n_lasttooth,dtype='int64'):  #dtype int64 necesary to avoid overflow
#     centerfreq = i * master_reprate
#     diff = centerfreq - f_firstpeak
#     diff_i = int(diff/freqintvl)
#     j = i_firstpeak + diff_i
#     j_minus = j - plusminus_i
#     j_plus = j + plusminus_i
#     max_j = np.argmax(background[j_minus:j_plus])
#     max_k = j_minus + max_j
#     if background[max_k] < thresh_l:
#         freqpeaks.append(freqlist[j])
#         backgroundpeaks.append(1)
#         samplepeaks.append(1)
#     else:
#         freqpeaks.append(freqlist[max_k])
#         backgroundpeaks.append(background[max_k])
#         s_peak = np.amax(sample[j_minus:j_plus])
#         samplepeaks.append(s_peak)

samplepeaks = np.array(samplepeaks)
backgroundpeaks = np.array(backgroundpeaks)

inten_mag_s = np.sqrt(2*samplepeaks)
inten_mag_b = np.sqrt(2*backgroundpeaks)

transmission_mag = inten_mag_s/inten_mag_b

absorbance_mag = []

for i in range(len(transmission_mag)):
    transmission_mag_i = transmission_mag[i]
    absorbance_mag_i = 100*((1-transmission_mag_i)**2)
    absorbance_mag.append(absorbance_mag_i)


transmission = samplepeaks/backgroundpeaks

def smoothener(data,plusminus):
    smooth_trans = []

    #lowindex
    for i in range(len(transmission)):
        low_help = i - plusminus
        if low_help < 0:
            newminus = abs(abs(low_help) - plusminus)
        else:
            newminus = plusminus
        low_index = i - newminus

        #highindex
        high_help = i + plusminus
        if high_help > (len(transmission) - 1):
            high_index = int(len(transmission) - 1)
        else:
            high_index = i + plusminus

        newrange = transmission[low_index:(high_index+1)]

        smooth_trans.append(np.mean(newrange))

    return smooth_trans


# plus_minus_list = [0, 2, 5, 10, 20, 50]

# for i in plus_minus_list:
#     smooth_trans = smoothener(transmission, i)
#     plt.figure()
#     plt.title(str(i))
#     plt.plot(freqpeaks, smooth_trans)

#
# absorbance = -np.log10(transmission)
#
# plt.figure()
# plt.title('backgroundpeaks')
# plt.plot(freqpeaks,backgroundpeaks)
#

inverseT = 1/transmission

plt.figure()
plt.title(fnames[3])
plt.xlim(0, 1.75E12)
plt.ylim(0,2)
plt.plot(freqpeaks,transmission)

plt.figure()
plt.title(fnames[3])
plt.xlim(0, 1.75E12)
plt.ylim(0,2)
plt.plot(freqpeaks,inverseT)
# #
# plt.figure()
# plt.title('absorbance')
# plt.plot(freqpeaks,absorbance_mag)
#
# plt.figure()
# plt.title('smooth_trans')
# plt.plot(freqpeaks, smooth_trans)

plt.show()
#
# np.savetxt(fnames[3] + 'absorbance.csv',absorbance)
