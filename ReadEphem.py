#!/usr/bin/env python3

'''
This reads the data that have been exported by Tracking.py.

USAGE:
        ./ReadEphem.py InputBinaryFile

EXAMPLE USAGE:
        python3 ReadEphem.py SV1.bin
'''

import argparse
import numpy as np
import time
import matplotlib.pyplot as plt
from FindInList import *
import pdb
import sys

np.set_printoptions(threshold=np.inf)
sys.argv = [sys.argv[0], 'SV1_120s.bin']

parser = argparse.ArgumentParser(
        description='Reads ephemeris data from Tracking data bit dump.',
        usage='./ReadEphem.py InputBinaryFile'
        )
parser.add_argument('DataFile')
args = parser.parse_args()

# Create class to store words:
class SingleWord:
    def __init__(self):
        self.WordData = None # 30 bits (stored as one byte per bit)
        self.LastD29 = None # Second-to-last bit from last frame (value 0 or 1 initially)
        self.LastD30 = None # Second-to-last bit from last frame (value 0 or 1 initially)
        self.ParityD25toD30 = None # Current parity bits
        self.PassesParityCheck = None

# Create class to store subframes:
class SubFrame:
    def __init__(self):
        self.Word = []
        self.FrameNumber = None # Will be a value 1-5
        self.PassesParityCheck = None

TrackingData = np.fromfile(args.DataFile, dtype=np.int8, count=-1,sep='')

PreambleRegular  = np.array([1,0,0,0,1,0,1,1]) # 0x0100000001000101
PreambleInverted = np.array([0,1,1,1,0,1,0,0]) # 0x0001010100010000

# Find occurences of preamble pattern and store indexes in array
matches = FindListInList(TrackingData, PreambleInverted)

#### Will need to search for both the regular, as well as inverted preamble. For
# now, just using the inverted, since manually confirmed this was the one in the data.

# Assume each index value is a preamble, which means that every 300 samples,
# there will be another preamble. If the first index is 15, then the next actual
# preamble would be 315. So subtract 15 from all of the indexes, and take
# the modulus of 300 of each index value. If the result is zero, than that index
# is a multiple of 300 in reference to that index. The indexes with the largest
# amount of zeros will be assumed to be the indexes that are actual preambles.
# Once that index is determined, will store all indexes that resulted in zeros
# as the indexes for the preambles.
ZeroCount = []
for indexOfFirstPreamble in range(0,len(matches)):
    multOfThreeHundred = []
    for (ind,val) in enumerate(matches):
        multOfThreeHundred.append(((val-matches[indexOfFirstPreamble]) % 300))
    ZeroCount.append(multOfThreeHundred.count(0))

FirstPreamble = np.argmax(np.array(ZeroCount))
multOfThreeHundred = []
preambleIndexList = []
for (ind,val) in enumerate(matches):
    multOfThreeHundred.append(((val-matches[FirstPreamble]) % 300))
    if multOfThreeHundred[len(multOfThreeHundred)-1] == 0:
        preambleIndexList.append(val) #ind

# Print indexes of preambles.
print(preambleIndexList)
print("Total preambles found: %d" %len(preambleIndexList))

# Now that the preambles are found, load class with subframe information
SubFrameList = []
for (ind,val) in enumerate(preambleIndexList):
    if (len(TrackingData) - 300) < val:
        print("Subframe associated with last preamble not complete, so discarding.")
        break # Current subframe not complete, so break.
        # Will need to do another check to make sure val > 1
    curSubFrame = SubFrame()
    for indWord in range(10):
        curWord = SingleWord()
        curWord.LastD29 = TrackingData[val + indWord*30 - 2]
        curWord.LastD30 = TrackingData[val + indWord*30 - 1]
        curWord.ParityD25toD30 = TrackingData[val + indWord*30 + 24:val + indWord*30 + 30]
        curWord.WordData = TrackingData[val + indWord*30:val + indWord*30 + 24]
        curSubFrame.Word.append(curWord)
    SubFrameList.append(curSubFrame)

for curFrame in range(len(SubFrameList)):
    for curWord in range(10):
        parityResult, PolarityCorrectedData = CheckParity(SubFrameList[curFrame].Word[curWord].WordData, SubFrameList[curFrame].Word[curWord].ParityD25toD30, SubFrameList[curFrame].Word[curWord].LastD29, SubFrameList[curFrame].Word[curWord].LastD30)
        #print(parityResult)
        if curWord == 1:  # This means it is the HOW word, so we'll find the SubFrame number
            SubframeNumber = 4*PolarityCorrectedData[19] + 2*PolarityCorrectedData[20] + 1*PolarityCorrectedData[21]
            SubFrameList[curFrame].FrameNumber = SubframeNumber
            print("Frame number: %d" %(SubframeNumber))
        print(PolarityCorrectedData)
quit()

#pdb.set_trace() # Spawn python shell
