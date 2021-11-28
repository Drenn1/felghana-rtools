#!/usr/bin/python3
# Dump files from the game into a directory

import os, zlib

def debug(s):
    print(s)

def dword(buffer, o):
    return buffer[o+0] | (buffer[o+1] << 8) | (buffer[o+2] << 16) | (buffer[o+3] << 24)

def decrypt(data):
    x = 0x7c53f961
    for i in range(len(data)):
        x *= 0x3d09
        data[i] = (data[i] - ((x >> 16) & 0xff)) & 0xff
    return data

def nullTerminatedString(data, offset):
    s = bytearray()
    while True:
        if data[offset] == 0:
            return s.decode()
        s.append(data[offset])
        offset += 1

def hashFilename(filename):
    h = 0
    i = 0
    tmp = 0
    while i < len(filename):
        tmp2 = tmp & 0xff
        tmp = (tmp + 5) & 0xffffffff
        h = (h + (((ord(filename[i]) - 0x20) & 0xff) << (tmp2 & 0x1f))) & 0xffffffff
        if tmp > 0x18:
            tmp = 0
        i += 1
    return h % 0xfff1

class Archive():
    def __init__(self, basename):
        self.basename = basename

        f = open(basename + '.ni', 'rb')
        indexData = f.read()
        f.close()

        magic = dword(indexData, 0)
        assert(magic == 0x00494e4e)
        blocks = dword(indexData, 4)
        size2 = dword(indexData, 8)

        debug('FILES: ' + str(blocks))

        data1End = 0x10 + blocks * 0x10
        assert(data1End + size2 == len(indexData))

        self.metadata = filedata1 = decrypt(bytearray(indexData[0x10 : data1End]))
        self.rawFileList = decrypt(bytearray(indexData[data1End : data1End + size2]))
        self.fileList = [s.decode() for s in self.rawFileList.split(b'\x00')]
        while len(self.fileList[-1]) == 0:
            self.fileList = self.fileList[:-1]

        debug('GOT FILE LIST')

        f = open('metadata', 'wb')
        f.write(self.metadata)
        f.close()
        data2 = decrypt(bytearray(indexData[data1End : data1End + size2]))
        f = open('fileList', 'w')
        f.write('\n'.join(self.fileList))
        f.close()

        debug('WROTE FILES')

    def getFileIndex(self, filename):
        h = hashFilename(filename)
        for i in range(len(self.fileList)):
            offset = i * 16

            nameOffset = dword(self.metadata, offset + 12)
            if filename == nullTerminatedString(self.rawFileList, nameOffset):
                h2 = (self.metadata[offset+1] << 8) | self.metadata[offset]
                if h != h2:
                    print('WARNING: Hash mismatch for ' + filename)
                return i
        assert False, "Couldn't find file " + filename

    def dumpAll(self, folder):
        f = open(self.basename + '.na', 'rb')
        cmpData = f.read()
        f.close()

        pos = 0
        for fileIndex in range(len(self.fileList)):
            cmpSize = dword(self.metadata, fileIndex * 16 + 4)
            offset = dword(self.metadata, fileIndex * 16 + 8)
            filenameOffset = dword(self.metadata, fileIndex * 16 + 12)
            decData = zlib.decompress(cmpData[offset + 8 : offset + cmpSize]) 

            name = nullTerminatedString(self.rawFileList, filenameOffset)
            filename = folder + '/' + name.replace('\\', '/')
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            f = open(filename, 'wb')
            f.write(decData)
            f.close()


#data_file = 'files/data_us'
data_file = '/home/matthew/hdd/.steam/steamapps/common/Ys The Oath in Felghana/release/2020_data/data_us'

archive = Archive(data_file)
archive.dumpAll('dump_2020')
