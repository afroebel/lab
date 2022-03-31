import binascii
import array

# Open in binary mode (so you don't read two byte line endings on Windows as one byte)
# and use with statement (always do this to avoid leaked file descriptors, unflushed files)
with open('data1.txt', 'rb') as f:
    # Slurp the whole file and efficiently convert it to hex all at once
    hexdata = binascii.hexlify(f.read())
    
x = binascii.unhexlify(hexdata)

y = array.array('H', x)


