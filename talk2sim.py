# -*- coding: utf-8 -*-
"""
Created on Tue Apr 13 21:37:03 2021

@author: THz-FCS
"""

import serial

ser = serial.Serial('COM4', 9600, timeout = 3)

ser.write(str.encode('CONN 1, "xyz"\n'))

ser.write(str.encode('AMAN 1\n'))

ser.write(str.encode('AMAN? \n'))

ser.readline()

ser.close()
