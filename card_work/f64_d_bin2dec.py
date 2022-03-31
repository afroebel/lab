import binascii
import array
import numpy as np

plus_minusV = 0.2

# Open in binary mode (so you don't read two byte line endings on Windows as one byte)
# and use with statement (always do this to avoid leaked file descriptors, unflushed files)
with open('100avgopfile0.txt', 'rb') as f:
    # Slurp the whole file and efficiently convert it to hex all at once
    hexdata = binascii.hexlify(f.read())
    
x = binascii.unhexlify(hexdata)

y = array.array('d', x)

z = np.array(y)

v1 = []

for i in range(len(z)):
    vv = plus_minusV*((z[i] - 32768)/32768)
    v1.append(vv)
    
v1

