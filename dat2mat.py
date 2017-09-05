from tkinter import filedialog as fdialog
import sys, struct, os, numpy as np

'''
This script stores MetroPro .dat file info in a custom Python
class, Data, which is returned at the end

Input:
FullFileName (optional) - The path, name, and extension of the file to convert.
If no input is given, a select file window will open

Output:
class Data
    .Name = string
    .PathName = string
    .CameraSize = [2 short]
    .mm_per_pixel = float
    .FidX = [n short]
    .FidY = [n short]
    .PhaseOrigin = double
    .x = [n float]
    .y = [n float]
    .z = [n [m float]]
    
To call from another file import dat2mat.py and use dat2mat.dat2mat()
or dat2mat.dat2mat("path/file.ext")

Copyright: Derek Stout, Optimax Systems Inc., 2017
'''
def dat2mat(FullFileName=None):

    #Open file chooser if no file given. Exit if window closed or given file location invalid
    if not FullFileName:
        try:
            FullFileName = fdialog.askopenfile(initialdir="O:\R&D", title="Select file",
                                               filetypes=(("dat files", "*.dat"), ("all files", "*.*"))).name
        except AttributeError:
            sys.exit('No File Selected')
    elif not os.path.isfile(FullFileName):
        sys.exit('Given File or Directory Does Not Exist')

    data = Data()
    data.Name = FullFileName.split('\\')[-1]
    data.PathName = FullFileName.replace(data.Name, '')

    #Open file to read in binary data
    with open(FullFileName, 'rb') as datFile:
        datData = datFile.read()

    camSize = struct.unpack('>hh', datData[234:238])
    data.CameraSize = [camSize[1], camSize[0]]
    data.mm_per_pixel = struct.unpack('>f', datData[184:188])[0] * 1e3

    #Store all fiducial data
    for i in range(430, 485, 4):
        tempFid = struct.unpack('>hh', datData[i:i + 4])
        data.FidX.append(tempFid[0])
        data.FidY.append(tempFid[1])

    #Size of header and aquiredData in bytes
    headByteSize = struct.unpack('>i', datData[6:10])[0]
    aquiredBytes = struct.unpack('>i', datData[60:64])[0]
    aqByteWidth = struct.unpack('>h', datData[51:53])[0]
    aqByteHeight = struct.unpack('>h', datData[53:55])[0]

    phaseOrigin = list(struct.unpack('>hh', datData[64:68]))
    data.PhaseOrigin = phaseOrigin

    #Size of phased data in bytes
    phaseByteStart = headByteSize + aquiredBytes
    phaseNumBytes = struct.unpack('>i', datData[72:76])[0]
    phaseByteEnd = phaseByteStart + phaseNumBytes
    phaseWidth = struct.unpack('>h', datData[68:70])[0]
    phaseHeight = struct.unpack('>h', datData[70:72])[0]

    phasedData = []

    #Read in MetroPro phased binary data
    for i in range(phaseByteStart, phaseByteEnd, 4):
        phasedData.append(struct.unpack('>i', datData[i:i + 4])[0])
        if phasedData[-1] >= 2147483640:
            phasedData[-1] = np.NaN

    phasedData = np.array(phasedData)
    phasedData = phasedData.reshape(phaseHeight, phaseWidth)

    #Convert binary data to Z height
    scaleFactor = struct.unpack('>f', datData[164:168])[0]
    obliquityFactor = struct.unpack('>f', datData[176:180])[0]
    waveLengthIn = struct.unpack('>f', datData[168:172])[0]
    phaseRes = {
        0: 4096,
        1: 32768,
        2: 131072
    }.get(struct.unpack('>h', datData[218:220])[0], 4096)

    phasedData = np.multiply(phasedData, scaleFactor * obliquityFactor / phaseRes)

    data.z = cropNaN(np.rot90(np.multiply(phasedData, waveLengthIn * 1e6)))

    data.x = np.multiply(np.arange(0, data.z.shape[1]), data.mm_per_pixel)
    data.y = np.multiply(np.arange(0, data.z.shape[0]), data.mm_per_pixel)

    return data

'''
Similar Function to cropbox.m
Crops off any rows and columns of the input array that
only consist of NaN values and returns the result
'''
def cropNaN(data):
    rows = np.isnan(data).all(axis=1)
    columns = np.isnan(data).all(axis=0)
    rRange = np.array([i for i, x in enumerate(rows) if not x])[[0, -1]]
    cRange = np.array([i for i, x in enumerate(columns) if not x])[[0, -1]]

    return (np.array(data)[rRange[0]:rRange[1] + 1, cRange[0]:cRange[1] + 1])

#Store the data unpacked from MetroPro .dat binary. Returned after function
class Data():
    Name = ''
    PathName = ''
    CameraSize = [2]
    mm_per_pixel = 0
    FidX = []
    FidY = []
    PhaseOrigin = 0
    x = []
    y = []
    z = []

#Include 'directory\file.ext' in dat2mat() to open a file automatically
#File chooser opens if no file is included
if __name__ == '__main__':
    dat2mat()