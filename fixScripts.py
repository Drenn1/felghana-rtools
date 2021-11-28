#!/usr/bin/python3

# Add voice triggers to JP scripts by comparing them to the corresponding
# english scripts.
#
# I don't have a very good understanding of the structure of the script files,
# but the end of it consists of the script text itself, and is not too difficult
# to modify. The tricky part is figuring out where the data starts; some basic
# heuristics are needed for this. Of course, this wouldn't be necessary if
# I understood how the overall file format is structured.

import struct, os

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

    if len(enScriptFile.scriptList) != len(jpScriptFile.scriptList):
        error(scriptName, 'length mismatch (%d, %d)' % (len(jpScriptFile.scriptList), len(enScriptFile.scriptList)))
        return False

    for i in range(len(enScriptFile.scriptList)):
        enScript = enScriptFile.scriptList[i]
        jpScript = jpScriptFile.scriptList[i]

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

# List of files with voice lines. Got this with the command:
#   grep -l '<voice:\|<narration:' dump_directory/* -R
fileList = [
'MAP/S_62/S_6298/LASTBATTLE_EV.XSO.Z',
'MAP/S_62/S_6298/BATTLE_END.XSO.Z',
'MAP/S_62/S_6298/GOOD_BY.XSO.Z',
'MAP/S_60/S_6001/DETH_ISLAND.XSO.Z',
'MAP/S_60/S_6000/DOGICOMA.XSO.Z',
'MAP/S_60/S_6099/DURAN_EVENT.XSO.Z',
'MAP/S_60/S_6099/AFTERBATTLE.XSO.Z',
'MAP/S_61/S_6199/BATTLEEND.XSO.Z',
'MAP/S_61/S_6199/GARLAND_EV.XSO.Z',
'MAP/S_11/S_1113/EVENT_2.XSO.Z',
'MAP/S_11/S_1111/EVENT_ELENA.XSO.Z',
'MAP/S_11/S_1110/EVENT_2.XSO.Z',
'MAP/S_11/S_1110/EVENT_1.XSO.Z',
'MAP/S_40/S_4099/BATTLERIGATY.XSO.Z',
'MAP/S_40/S_4099/EV_RIGATY.XSO.Z',
'MAP/S_40/S_4009/DOGI_HARMED.XSO.Z',
'MAP/S_02/S_0200/SELEND_2.XSO.Z',
'MAP/S_02/S_0200/GET_BARM.XSO.Z',
'MAP/S_02/S_0200/HELP_ELENA.XSO.Z',
'MAP/S_02/S_0200/SEL_YES.XSO.Z',
'MAP/S_02/S_0200/SEL_PLAY_ARNYA.XSO.Z',
'MAP/S_02/S_0200/EPILOGUE_1.XSO.Z',
'MAP/S_02/S_0200/CAMERASCROLL_2.XSO.Z',
'MAP/S_02/S_0200/GO_HOME_ELENA.XSO.Z',
'MAP/S_02/S_0200/GO_ELENA_2.XSO.Z',
'MAP/S_02/S_0200/CAMERASCROLL_1.XSO.Z',
'MAP/S_02/S_0200/TALKAIDA.XSO.Z',
'MAP/S_02/S_0200/TALKANTON.XSO.Z',
'MAP/S_02/S_0200/TALKRICHARD_1.XSO.Z',
'MAP/S_02/S_0200/SELYES_1.XSO.Z',
'MAP/S_02/S_0200/EVENT_ALL_BIRM.XSO.Z',
'MAP/S_02/S_0200/SELNO_3.XSO.Z',
'MAP/S_02/S_0200/TALKGARDNER.XSO.Z',
'MAP/S_02/S_0200/SEL_NO.XSO.Z',
'MAP/S_02/S_0200/SEL_TAKE_BARM.XSO.Z',
'MAP/S_02/S_0200/TALKHYUGO.XSO.Z',
'MAP/S_02/S_0200/TALKFIONA.XSO.Z',
'MAP/S_02/S_0200/TALKDEWY.XSO.Z',
'MAP/S_02/S_0200/AFTER_BATTLE.XSO.Z',
'MAP/S_02/S_0200/TALKARNYA.XSO.Z',
'MAP/S_02/S_0200/SEL_NO2.XSO.Z',
'MAP/S_02/S_0201/EVENT_1.XSO.Z',
'MAP/S_10/S_1002/TALK_BOY.XSO.Z',
'MAP/S_10/S_1000/BYE_DOGI.XSO.Z',
'MAP/S_10/S_1000/MEET_ELENA.XSO.Z',
'MAP/S_10/S_1000/TALKGARDNER.XSO.Z',
'MAP/S_10/S_1004/TALKFRAN_2.XSO.Z',
'MAP/S_10/S_1004/SELNO_F.XSO.Z',
'MAP/S_10/S_1004/SELYES_F.XSO.Z',
'MAP/S_10/S_1004/TALKFLAN.XSO.Z',
'MAP/S_10/S_1004/HELP_CLIST.XSO.Z',
'MAP/S_10/S_1001/TALKPORL_2.XSO.Z',
'MAP/S_10/S_1005/SAID_NO.XSO.Z',
'MAP/S_10/S_1005/GOODBY_ADOL.XSO.Z',
'MAP/S_10/S_1005/GO_ISLAND.XSO.Z',
'MAP/S_10/S_1005/TALKELENA_2.XSO.Z',
'MAP/S_10/S_1005/TALKELENA.XSO.Z',
'MAP/S_10/S_1005/TALKDOGI.XSO.Z',
'MAP/S_10/S_1005/SAID_YES.XSO.Z',
'MAP/S_10/S_1010/EVENT_TALK_GARDNER.XSO.Z',
'MAP/S_10/S_1010/BEL_LOOKUP.XSO.Z',
'MAP/S_33/S_3301/MEET_ELENA.XSO.Z',
'MAP/S_33/S_3304/LA_QUEBRATA_2.XSO.Z',
'MAP/S_33/S_3304/LA_QUEBRATA.XSO.Z',
'MAP/S_33/S_3399/AFTERBATTLECHESTER.XSO.Z',
'MAP/S_33/S_3399/CHESTER_EVENT.XSO.Z',
'MAP/S_35/S_3507/EVENT_DULAN.XSO.Z',
'MAP/S_55/S_5699/EVENT_2.XSO.Z',
'MAP/S_55/S_5699/BATTLEEND.XSO.Z',
'MAP/S_55/S_5699/EVENT_1.XSO.Z',
'MAP/S_55/S_5599/CHESTER_EVENT.XSO.Z',
'MAP/S_55/S_5599/AFTER_EV.XSO.Z',
'MAP/S_55/S_5598/MCGUIRE_EVENT.XSO.Z',
'MAP/S_45/S_4598/DOGI_OVERTHE_ROCK.XSO.Z',
'MAP/S_45/S_4598/AFTER_BOSS.XSO.Z',
'MAP/S_45/S_4505/MEET_DOGI.XSO.Z',
'MAP/S_45/S_4505/GET_BRACELET.XSO.Z',
'MAP/S_45/S_4505/GET_BRACELET_2.XSO.Z',
'MAP/S_50/S_5007/TALKALICE.XSO.Z',
'MAP/S_50/S_5007/TALKCHRIS.XSO.Z',
'MAP/S_50/S_5007/TALKLIZ.XSO.Z',
'MAP/S_50/S_5007/FINDFAMILY.XSO.Z',
'MAP/S_50/S_5107/TALKNICHO.XSO.Z',
'MAP/S_50/S_5000/EVENT_MEET_ELIZA.XSO.Z',
'MAP/S_53/S_5304/TALKBOB.XSO.Z',
'MAP/S_53/S_5304/FINDELENA.XSO.Z',
'MAP/S_53/S_5304/TALKANDRE.XSO.Z',
'MAP/S_20/S_2013/TALKEDGAR_1.XSO.Z',
'MAP/S_20/S_2013/STOPADOL.XSO.Z',
'MAP/S_20/S_2013/EVENT2.XSO.Z',
'MAP/S_20/S_2199/DURAN_EVENT.XSO.Z',
'MAP/S_20/S_2199/ENDBATTLE.XSO.Z',
'MAP/S_20/S_2009/DEWEYEVENT_1.XSO.Z',
'MAP/S_20/S_2009/STOPDEWEY_1.XSO.Z',
'MAP/S_20/S_2009/TALKDEWEY_1.XSO.Z',
'MAP/S_01/S_0110/TALKADONIS.XSO.Z',
'MAP/S_01/S_0110/SELNO.XSO.Z',
'MAP/S_01/S_0110/SELYES.XSO.Z',
'MAP/S_01/S_0110/CYNTHIA_FIRST.XSO.Z',
'MAP/S_01/S_0130/AIDA_FIRST.XSO.Z',
'MAP/S_01/S_0130/RETURNINGPENDANT.XSO.Z',
'MAP/S_01/S_0180/DYINGDOGI.XSO.Z',
'MAP/S_01/S_0180/EV_BELHART.XSO.Z',
'MAP/S_01/S_0150/TALKSISTERNEL.XSO.Z',
'MAP/S_01/S_0150/TALKPIERRE.XSO.Z',
'MAP/S_01/S_0150/TALKHALORD.XSO.Z',
'MAP/S_01/S_0150/RETURNINGPENDANT.XSO.Z',
'MAP/S_01/S_0150/GET_BARM.XSO.Z',
'MAP/S_01/S_0150/SEL_YES.XSO.Z',
'MAP/S_01/S_0150/TALKNICHOLUS_EV.XSO.Z',
'MAP/S_01/S_0150/TALKAIDA.XSO.Z',
'MAP/S_01/S_0150/TALKANTON.XSO.Z',
'MAP/S_01/S_0150/SELYES_1.XSO.Z',
'MAP/S_01/S_0150/EVENT_NICHOLUS.XSO.Z',
'MAP/S_01/S_0150/EVENT_ALL_BIRM.XSO.Z',
'MAP/S_01/S_0150/SELNO_3.XSO.Z',
'MAP/S_01/S_0150/SEL_NO.XSO.Z',
'MAP/S_01/S_0150/SEL_TAKE_BARM.XSO.Z',
'MAP/S_01/S_0150/TALKHYUGO.XSO.Z',
'MAP/S_01/S_0102/DOGI_EVENT_1.XSO.Z',
'MAP/S_01/S_0120/AFTER_ISHTARSIVA.XSO.Z',
'MAP/S_01/S_0120/TALKEDGAR.XSO.Z',
'MAP/S_01/S_0120/AFTER_ELF.XSO.Z',
'MAP/S_01/S_0120/TALKABOUTFINAL.XSO.Z',
'MAP/S_01/S_0120/AFTER_MOUNTAIN.XSO.Z',
'MAP/S_01/S_0120/AFTER_GARUBA.XSO.Z',
'MAP/S_01/S_0103/EVENT_2.XSO.Z',
'MAP/S_01/S_0121/TALKCHESTER.XSO.Z',
'MAP/S_01/S_0160/TALKROX.XSO.Z',
'MAP/S_01/S_0140/GO_ELENA.XSO.Z',
'MAP/S_01/S_0140/TALKABOUTBRO.XSO.Z',
'MAP/S_01/S_0140/TALKELENA1.XSO.Z',
'MAP/S_01/S_0100/TALKMARGO.XSO.Z',
'MAP/S_01/S_0100/RING_OF_JADE.XSO.Z',
'MAP/S_01/S_0100/TALKJOEL.XSO.Z',
'MAP/S_01/S_0100/SELNO.XSO.Z',
'MAP/S_01/S_0100/RING_TO_RANDOLF2.XSO.Z',
'MAP/S_01/S_0100/TALKBELHERT.XSO.Z',
'MAP/S_01/S_0100/SELYES.XSO.Z',
'MAP/S_01/S_0170/TALKHUGO.XSO.Z',
'MAP/S_01/S_0170/GET_BARM.XSO.Z',
'MAP/S_01/S_0170/EVENT_ALL_BIRM.XSO.Z',
'MAP/S_01/S_0170/SELNO_3.XSO.Z',
'MAP/S_01/S_0170/SEL_TAKE_BARM.XSO.Z',
'MAP/S_25/S_2503/ADOLAWAKEN.XSO.Z',
]

successCount = 0
for i in range(len(fileList)):
    if copyVoiceLines(fileList[i]):
        successCount += 1

print('Successfully converted ' + str(successCount) + ' / ' + str(len(fileList)) + ' files')
