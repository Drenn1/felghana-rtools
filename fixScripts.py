#!/usr/bin/python3

# Add voice triggers to JP scripts by comparing them to the corresponding
# english scripts.
#
# I don't have a very good understanding of the structure of the script files,
# but the end of it consists of the script text itself, and is not too difficult
# to modify. The tricky part is figuring out where the data starts; some basic
# heuristics are needed for this. Of course, this wouldn't be necessary if
# I understood how the overall file format is structured.

import sys, struct, os, binascii

def dword(buffer, o):
    return buffer[o+0] | (buffer[o+1] << 8) | (buffer[o+2] << 16) | (buffer[o+3] << 24)

def error(f, s):
    print('ERROR in ' + f + ': ' + s)

def warning(f, s):
    print('WARNING in ' + f + ': ' + s)

class ScriptFile:
    def __init__(self, filename, header):
        self.filename = filename
        self.header = header # Consists of all data I don't understand or care about
        self.scriptList = [] # The modifiable text data we're interested in
        self.numNullStrings = 0

    def addScript(self, data, addr):
        end = addr
        while data[end] != 0: # TODO: Is this ok with Shift-JIS?
            end += 1
        self.scriptList.append(data[addr : end + 1])
        if data[addr] == 0:
            self.numNullStrings += 1

    def save(self, outputFile):
        dirname = os.path.dirname(outputFile)
        os.makedirs(dirname, exist_ok=True)
        f = open(outputFile, 'wb')
        f.write(self.header)

        offset = 0
        for script in self.scriptList:
            f.write(struct.pack("<I", offset))
            offset += len(script)

        for script in self.scriptList:
            f.write(script)

        f.close()

def parseScriptFile(filename):
    f = open(filename, 'rb')
    data = f.read()
    f.close()

    # This is still just a guess, we'll need to verify it
    pointersStart = (len(data) & 0xfffffffc) - 4
    while True:
        if pointersStart < 4:
            error(filename, 'Reached start of file')
            return None
        if dword(data, pointersStart - 4) == 0x01000000:
            break
        pointersStart -= 4

    scriptDataStart = pointersStart
    while True:
        if scriptDataStart >= len(data):
            error(filename, 'Reached end of file')
            return None
        if dword(data, scriptDataStart) >= 0x00080000: # End of pointers (file offsets)
            break
        scriptDataStart += 4

    scriptCount = (scriptDataStart - pointersStart) // 4
    script = ScriptFile(filename, data[0:pointersStart])

    for i in range(scriptCount):
        ptrAddr = pointersStart + i * 4
        dataAddr = dword(data, ptrAddr) + scriptDataStart

        if dataAddr < 4 or dataAddr >= len(data):
            error(filename, 'Data address invalid')
            return None
        if data[dataAddr - 1] != 0:
            error(filename, 'Null terminator expected (2)')
            return None

        script.addScript(data, dataAddr)

    return script


def copyVoiceLines(scriptName):
    enScriptFile = parseScriptFile('dump_us_2020/' + scriptName)
    if not enScriptFile:
        return False
    jpScriptFile = parseScriptFile('dump_main_2020/' + scriptName)
    if not jpScriptFile:
        return False

    if len(enScriptFile.scriptList) != len(jpScriptFile.scriptList) and not scriptName in indexOverride:
        error(scriptName, 'length mismatch (%d, %d)' % (len(jpScriptFile.scriptList), len(enScriptFile.scriptList)))
        return False

    for i in range(len(jpScriptFile.scriptList)):
        j = i
        if scriptName in indexOverride:
            if i in indexOverride[scriptName]:
                j = indexOverride[scriptName][i]
                if j is None:
                    continue

        if i >= len(enScriptFile.scriptList):
            continue;
        jpScript = jpScriptFile.scriptList[i]
        enScript = enScriptFile.scriptList[j]

        voiceStrings = [ b'<voice:', b'<narration:' ]

        for vs in voiceStrings:
            if enScript[0:len(vs)] == vs:
                end = enScript.find(b'>') + 1
                voiceString = enScript[0 : end]
                jpScriptFile.scriptList[i] = voiceString + jpScript

            p = enScript.rfind(vs)
            if p != -1 and p != 0:
                warning(scriptName, 'voice line not at text start')

    jpScriptFile.save('staging/' + scriptName)
    return True

def analyzeScript(scriptFile, outname=None):
    scriptFile = parseScriptFile(scriptFile)
    if not scriptFile:
        return False

    if outname is None:
        f = sys.stdout
    else:
        f = open(outname, 'w')
    for i in range(len(scriptFile.scriptList)):
        f.write('SCRIPT ' + hex(i) + ':\n')
        try:
            f.write(scriptFile.scriptList[i].decode('shift-jis'))
        except:
            f.write('ERROR DECODING STRING: ' + binascii.hexlify(scriptFile.scriptList[i]).decode())
        f.write('\n\n')
    if not outname is None:
        f.close()

def analyzeScriptPair(scriptName):
    analyzeScript('dump_us_2020/' + scriptName, 'analyze_en')
    analyzeScript('dump_main_2020/' + scriptName, 'analyze_jp')


from scriptInfo import *


def convertAllVoiceLines():
    successCount = 0
    for i in range(len(fileList)):
        if copyVoiceLines(fileList[i]):
            successCount += 1
    print('Successfully converted ' + str(successCount) + ' / ' + str(len(fileList)) + ' files')

convertAllVoiceLines()

#analyzeScript('staging/MAP/S_62/S_6298/GOOD_BY.XSO.Z')
#analyzeScriptPair('MAP/S_01/S_0170/TALKHUGO.XSO.Z')
