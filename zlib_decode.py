#!/usr/bin/python3
import sys
import zlib

f = open(sys.argv[1], 'rb')
data = f.read()
f.close()

f = open(sys.argv[2], 'wb')
dec = zlib.decompress(data)
f.write(dec)
f.close()
