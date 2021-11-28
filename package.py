#!/usr/bin/python3
# Package a directory of files into an archive usable by the game

import os, zlib, struct

def encrypt(data):
    x = 0x7c53f961
    for i in range(len(data)):
        x *= 0x3d09
        data[i] = (data[i] + ((x >> 16) & 0xff)) & 0xff
    return data

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


class ArchiveEntry:
    def __init__(self, name, data):
        self.filename = name
        self.plainData = data
        self.cmpData = zlib.compress(data)
        self.nameHash = hashFilename(name)

        self.cmpDataOffset = None
        self.rawStringOffset = None

class Archive:
    def __init__(self):
        self.fileList = []

    def addFile(self, filename, data):
        entry = ArchiveEntry(filename, data)
        self.fileList.append(entry)

    def save(self, outputName):
        self.fileList.sort(key=lambda x: x.nameHash)

        # Generate ".na" file
        cmpDataBlob = bytearray()
        for fileIndex in range(len(self.fileList)):
            fileStruct = self.fileList[fileIndex]
            fileStruct.cmpDataOffset = len(cmpDataBlob)
            cmpDataBlob.extend(struct.pack('<II', 0, len(fileStruct.plainData)))
            cmpDataBlob.extend(fileStruct.cmpData)

        f = open(outputName + '.na', 'wb')
        f.write(cmpDataBlob)
        f.close()

        # Genarate ".ni" file
        fileListBlob = bytearray()
        for fileStruct in self.fileList:
            fileStruct.rawStringOffset = len(fileListBlob)
            fileListBlob.extend(fileStruct.filename.encode())
            fileListBlob.append(0)

        metadataBlob = bytearray()
        for fileStruct in self.fileList:
            metadataBlob.extend(struct.pack('<IIII', fileStruct.nameHash, len(fileStruct.cmpData) + 8, fileStruct.cmpDataOffset, fileStruct.rawStringOffset))

        # For debugging
        f = open('metadata', 'wb')
        f.write(metadataBlob)
        f.close()
        f = open('fileList', 'wb')
        f.write(fileListBlob)
        f.close()

        fileListBlob = encrypt(fileListBlob)
        metadataBlob = encrypt(metadataBlob)

        f = open(outputName + '.ni', 'wb')
        f.write(b'NNI\x00' + struct.pack('<III', len(self.fileList), len(fileListBlob), 0))
        f.write(metadataBlob)
        f.write(fileListBlob)
        f.close()

def packageDirectory(directory, outputName):
    archive = Archive()

    if directory[-1] != '/':
        directory = directory + '/'

    for root, dirs, files in os.walk(directory):
        encodedRoot = root[len(directory):].replace('/', '\\')
        for fileBasename in files:
            filename = root + '/' + fileBasename
            fileEncodedName = encodedRoot + '\\' + fileBasename
            f = open(filename, 'rb')
            plainData = f.read()
            f.close()
            archive.addFile(fileEncodedName, plainData)

    archive.save(outputName)

packageDirectory('dump_2018', 'new')
