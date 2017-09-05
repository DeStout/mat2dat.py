from tkinter import filedialog
import os, sys, shutil, struct, time, math, numpy as np

'''
This script converts a 2D array of Z height data across a resolution
of milimeters per pixel to binary and writes it to a MetroPro .dat file

Input:
data - A 2D array of height data in python list or Numpy array form

mm_per_pixel - A float or int specifying the lateral resolution of the data
in milimeters per pixel

FullFileName (optional) - The path, name, and extension of the file to convert.
Is optional, if no input is given, a select file window will open

Output:
Nothing is returned
[newDatFile].dat is saved in the users directory of choice

mat2dat.py will not run independently unless data and mm_per_pixel are replaced within
the call in the main function
To call from another file import mat2dat.py and use mat2dat.mat2dat(data, mm_per_pixel)
or mat2dat.mat2dat(data, mm_per_pixel, "path/file.ext")

Copyright: Derek Stout, Optimax Systems Inc., 2017
'''
def mat2dat(data = [], mm_per_pixel = None, FullFileName = None):

    #Convert data to Numpy array if Python list. Exit error if neither
    if not data.any():
        sys.exit("No ZData to save")
    elif type(data) is list:
        data = np.array(data)
        print('Data converted to Numpy array')
    elif not isinstance(data, np.ndarray):
        sys.exit("ZData needs to be a list")

    #Convert mm_per_pixel to float if int. Exit if neither
    if not mm_per_pixel:
        sys.exit("No MM per pixel specified")
    elif isinstance(mm_per_pixel, int):
        mm_per_pixel = float(mm_per_pixel)
        print('MM per pixel converted to float')
    elif not isinstance(mm_per_pixel, float):
        sys.exit("MM per pixel must be a float or integer")

    #Prompt user to create a new file or save over a previous. Exit if closed or provided file does not exist
    if not FullFileName:
        try:
            newDatFile = filedialog.asksaveasfile(initialdir='O:\R&D_old', title='Save As',
                                                filetypes=[('dat file', '*.dat'), ('all files', '*.*')], defaultextension='.dat').name
        except AttributeError:
            sys.exit('No File Selected')
    elif not os.path.isfile(FullFileName):
        sys.exit('Given File or Directory Does Not Exist')
    else:
        newDatFile = FullFileName

    #Overwrite new file with blank .dat file and open to write to
    blankDat = 'O:\Company\SoftwareTools\Data_DoNotEdit\\blankfile.dat'
    shutil.copyfile(blankDat, newDatFile)
    with open(newDatFile, 'bw+') as datFile:
        print('Writing .dat file')

        #Header info
        datFile.write(bytearray([0x88, 0x1B, 0x03, 0x6F]))              #Binary file magic number
        datFile.write(struct.pack('>hih', 1, 834, 1))                   #Header format and size, swinfo.type
        datFile.write(b'Mon Jan 04 08:42:09 2010')                      #MetroPro copyright date
        datFile.write(struct.pack('>hhh', 8, 3, 5))                     #MetroPro maj, min, bug fix info

        datFile.seek(60)
        datFile.write(struct.pack('>ihh', 0, 0, 0))                     #Aquired byte size, phased camera x and y
        datFile.write(struct.pack('>hh', len(data[0]), len(data)))      #Phazed data width and height
        datFile.write(struct.pack('>i', len(data) * len(data[0])))      #Phazed byte size

        datFile.write(struct.pack('>i', int(time.time())))              #Timestamp

        IntFScaleFactor_DefaultVal = 0.5
        WaveLengthIn_DefaultVal = 6.328e-7
        ObliquityFactor_DefaultVal = 1
        PhaseResolution_DefaultVal = 0
        if PhaseResolution_DefaultVal == 0:
            phaseRes = 4096

        datFile.seek(164)
        datFile.write(struct.pack('>f', IntFScaleFactor_DefaultVal))    #IntF Scale Factor
        datFile.write(struct.pack('>f', WaveLengthIn_DefaultVal))       #Wave Length In
        datFile.seek(176)
        datFile.write(struct.pack('>f', ObliquityFactor_DefaultVal))    #Obliquity Factor
        datFile.seek(184)
        datFile.write(struct.pack('>f', mm_per_pixel/1e3))              #Lateral res/MM per pixel
        datFile.seek(218)
        datFile.write(struct.pack('>i', PhaseResolution_DefaultVal))    #Phase Resolution

        #Convert MM Z Data into wave length and then MetroPro binary data
        waveData = np.divide(np.rot90(data, 3), WaveLengthIn_DefaultVal*1e6)
        MetroProData = (waveData*phaseRes)/(IntFScaleFactor_DefaultVal * ObliquityFactor_DefaultVal)

        #Phased data
        datFile.seek(834)
        for subArray in MetroProData:
            for zData in subArray:
                if math.isnan(zData):
                    zData = 2147483640
                zData = int(zData)
                datFile.write(struct.pack('>i', zData))

#Replace data, mm_per_pixel, and 'directory/file.ext' to run script
#data and mm_per_pixel are necessary but file name is optional
if __name__ == '__main__':
    mat2dat(data, mm_per_pixel, 'directory/file.ext')