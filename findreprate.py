# -*- coding: utf-8 -*-
"""
Created on Sun Nov  7 16:08:38 2021

@author: THz-FCS
"""

freqLO = 79.2179E6
freqHI = 79.239E6

desiredfrequency = 425056000000
toothno = desiredfrequency//freqLO
desiredreprate = desiredfrequency/toothno
if desiredreprate > freqLO and desiredreprate < freqHI:
    print(desiredreprate)
