from __future__ import division
import os, matplotlib.pyplot as plt, sys
import math

def MergeFile(fileToRead, fileToWrite, schedulerType):
    rFile = open(fileToRead, "r")
    wFile = open(fileToWrite, "a+")

    firstLineFlag = 1
    for line in rFile:
        # Skip the first line 
        if firstLineFlag:
            firstLineFlag = 0
            continue
        # Skip empty lines, if any 
        if line == [] or line == "":
            continue

        wFile.write(str(line[0:-2]) + " " + str(schedulerType) + "\n")

    wFile.close()
    rFile.close()

# Command Line arguments <scriptName> <Speed [0|5]> <SchedularType> <IMSI_1 Classification [0|1]>
def main():
    if(len(sys.argv) < 3):
        print "Invalid Input"
        return

    if str(sys.argv[1]) is "5":
        fileToWriteRlcStats = "myDlRlcStatsAt5.txt"
        if len(sys.argv) == 4 and int(sys.argv[3]) == 1:
            fileToWriteSinrStats = "myDlSinrStatsAt5.txt"
    else:
        fileToWriteRlcStats = "myDlRlcStatsAt0.txt"
        if len(sys.argv) == 4 and int(sys.argv[3]) == 1:
            fileToWriteSinrStats = "myDlSinrStatsAt0.txt"

    schedulerType = str(sys.argv[2])
    MergeFile("DlRlcStats.txt", fileToWriteRlcStats, schedulerType)
    if len(sys.argv) == 4 and int(sys.argv[3]) == 1:
        MergeFile("DlRsrpSinrStats.txt", fileToWriteSinrStats, schedulerType)

if __name__ == "__main__": main()
