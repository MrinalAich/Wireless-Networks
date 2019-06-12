from __future__ import division
import os, matplotlib.pyplot as plt, numpy as np
import math

gSimTime = 10
gRngRuns = 5.0
gNoOfUes = 20

# Class definations
class pairInfo():
     def __init__(self):
         self.cellid = 0
         self.imsi   = 0
         self.listOfParameter = []
         self.listOfTime = []

class schedulerType():
    def __init__(self):
        self.schedularName = ""
        self.pairInfo = []

class resultOutput():
    def __init__(self):
        self.schedularName = ""
        self.total = 0.0
        self.totalList = []

class buckets():
    def __init__(self):
        self.count = 0
        self.total = 0.0
        self.indicator = 0.0

# Get the index of the scheduler by schedulerName
def getSchedulerIndex(schedulerList, shedulerType):
    index = 0
    for iter in schedulerList:
        if iter.schedularName == str(shedulerType):
            return index
        else:
            index = index + 1
    
    if index == len(schedulerList):
        return -1

# Calculates Aggregate System Throughput specific to speed
def CalculateAggregateSysThroughput_N(value):
    if value == 5:
        rFile = open("myDlRlcStatsAt5.txt", "r")
    else:
        rFile = open("myDlRlcStatsAt0.txt", "r")

    # List of Schedulers
    schedulers = []

    start = 0.0
    end = 0.0
    duration = 0.0
    rxBytes = 0.0
    throughput = 0.0
    schedulerIndex = 0
    pairIndex = 0
    innerIndex = 0

    for line in rFile:
        found = 0
        data = line.split()

        start = float(data[0])
        end   = float(data[1])

        schedulerIndex = getSchedulerIndex(schedulers, str(data[18]))
        if schedulerIndex == -1:
            # Add the scheduler Information
            obj = schedulerType()
            obj.schedularName = str(data[18])
            obj.pairInfo = []
            schedulers.append(obj)
            schedulerIndex = len(schedulers)-1

        # Search for IMSI
        for pairIndex in range(0, len(schedulers[schedulerIndex].pairInfo)):
            if schedulers[schedulerIndex].pairInfo[pairIndex].imsi == int(data[3]):
                found = 1
                break

        if not found:
            # Add IMSI/Cell-Id information
            obj = pairInfo()
            obj.cellid = int(data[2])
            obj.imsi = int(data[3])
            obj.listOfParameter = []
            obj.listOfTime = []
            schedulers[schedulerIndex].pairInfo.append(obj)
            pairIndex = len(schedulers[schedulerIndex].pairInfo) - 1

        duration = end - start
        rxBytes = float(data[9]) # Rx Byte Column

        throughput = (rxBytes * 8.0) / (duration * 1000.0 * 1000.0) # Mbps
        
        foundTime = 0
        for innerIndex in range(0, len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfTime)):
            if float(data[1]) == schedulers[schedulerIndex].pairInfo[pairIndex].listOfTime[innerIndex]:
                foundTime = 1
                break
            
        if not foundTime:
            # Add information about Time and Throughput
            schedulers[schedulerIndex].pairInfo[pairIndex].listOfTime.append(float(data[1]))
            schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter.append(throughput)
            innerIndex = len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfTime) - 1
        else:
            schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[innerIndex] = schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[innerIndex] + throughput

    # Average over RngRuns : Per Schedular per UE Throughput per Time (Across all RngRuns)
    for schedulerIndex in range(0, len(schedulers)):
        for pairIndex in range(0, len(schedulers[schedulerIndex].pairInfo)):
            for innerIndex in range(0, len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter)):
                schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[innerIndex] = schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[innerIndex] / gRngRuns;

    # AggregateSysThroughput
    aggSysTP = []
    for schedulerIndex in range(0, len(schedulers)):
        obj = resultOutput()
        obj.schedularName = schedulers[schedulerIndex].schedularName
        obj.total = 0.0
        obj.totalList = []
        for pairIndex in range(0, len(schedulers[schedulerIndex].pairInfo)):
            for innerIndex in range(0, len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter)):
                obj.total = obj.total + schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[innerIndex]
        obj.total = (obj.total / len(schedulers[schedulerIndex].pairInfo)) / (len(schedulers[schedulerIndex].pairInfo[0].listOfTime))
        aggSysTP.append(obj)

    return schedulers,aggSysTP


# Plots Throughput CDF for all UEs specific to speed
def PlotUEThroughputCDF_N(schedulers, value):
    if value == 5:
        plotName = "UeThroughputCdfAt5"
    else:
        plotName = "UeThroughputCdfAt0"

    schedulerIndex = 0
    pairIndex = 0
    innerIndex = 0
    ueIndex = 0

    result = [] # Per Scheduler Per UE (1...20) Total-Throughput / All-Time (Each Throughput averaged over all Rng-Runs)
    for schedulerIndex in range(0, len(schedulers)):
        obj = resultOutput()
        obj.total = 0.0
        obj.totalList = []
        obj.schedularName = schedulers[schedulerIndex].schedularName
        for ueIndex in range(1, gNoOfUes+1):
            total = 0.0
            for pairIndex in range(0, len(schedulers[schedulerIndex].pairInfo)):
                if schedulers[schedulerIndex].pairInfo[pairIndex].imsi == ueIndex:
                    for innerIndex in range(0, len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter)):
                        total = total + schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[innerIndex]
                    total = total / (len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfTime) * 1.0)
                    # Cumulative
                    if len(obj.totalList):
                        total = total + obj.totalList[-1]
                    obj.totalList.append(total)
        result.append(obj)

    # UE-List
    ueList = []
    for index in range(1, gNoOfUes+1):
        ueList.append(index)

    # Plot Figure
    legene = []

    for schedulerIndex in range(0, len(result)):
        if result[schedulerIndex].schedularName == "ns3::RrFfMacScheduler":
            legene_r, = plt.plot(ueList, result[schedulerIndex].totalList, 'r', label='RoundRobin')
        elif result[schedulerIndex].schedularName == "ns3::PfFfMacScheduler":
            legene_g, = plt.plot(ueList, result[schedulerIndex].totalList, 'g', label='Proportional Fair')
        elif result[schedulerIndex].schedularName == "ns3::FdBetFfMacScheduler":
            legene_b, = plt.plot(ueList, result[schedulerIndex].totalList, 'b', label='BTAS')
        elif result[schedulerIndex].schedularName == "ns3::TdMtFfMacScheduler":
            legene_y, = plt.plot(ueList, result[schedulerIndex].totalList, 'y', label='Max Throughput')
        else:
            print "Programming Error. Scenario should not occur"

    plt.xlabel("UE(s)")
    plt.ylabel("Throughput (in Mbps)")
    plt.xlim([0,21])
    plt.legend(handles=[legene_r, legene_g, legene_b, legene_y], loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fontsize=10)
    
    try: # Remove file, if already exists
        os.remove(plotName + ".png")
    except:
        pass
    plt.savefig(plotName + ".png")
    plt.close()

# Plots Throughput CDF for all UEs
def PlotUEThroughputCDF(schedulerInfo_0, schedulerInfo_5):
    PlotUEThroughputCDF_N(schedulerInfo_0, 0)
    PlotUEThroughputCDF_N(schedulerInfo_5, 5)

# Main function
def main():
    schedulerInfo_0,schedulerInfo_5 = CalculateAggregateSysThroughput()
    PlotUEThroughputCDF(schedulerInfo_0, schedulerInfo_5)
    PlotInstantaneousThroughput_IMSI_1(schedulerInfo_0, schedulerInfo_5)
    PlotSINR_IMSI_1()

# Calculates Aggregate System Throughput
def CalculateAggregateSysThroughput():
    schedulerInfo_0,aggSysTPSchedulers_0 = CalculateAggregateSysThroughput_N(0)
    schedulerInfo_5,aggSysTPSchedulers_5 = CalculateAggregateSysThroughput_N(5)

    # Plot figure    
    N = 2               # the x locations for the groups
    ind = np.arange(2)  
    width = 0.12        # the width of the bars

    fig = plt.figure()
    plt.ylim([0,5])
    ax = fig.add_subplot(111)

    for lsIndex in range(0, len(aggSysTPSchedulers_0)):
        if aggSysTPSchedulers_0[lsIndex].schedularName == "ns3::RrFfMacScheduler":
            for rsIndex in range(0, len(aggSysTPSchedulers_5)):
                if aggSysTPSchedulers_5[rsIndex].schedularName == "ns3::RrFfMacScheduler":
                    scheduler1 = [aggSysTPSchedulers_0[lsIndex].total,aggSysTPSchedulers_5[rsIndex].total]
                    rects1 = ax.bar(ind, scheduler1, width, color='r')
                    break
    
    for lsIndex in range(0, len(aggSysTPSchedulers_0)):
        if aggSysTPSchedulers_0[lsIndex].schedularName == "ns3::PfFfMacScheduler":
            for rsIndex in range(0, len(aggSysTPSchedulers_5)):
                if aggSysTPSchedulers_5[rsIndex].schedularName == "ns3::PfFfMacScheduler":
                    scheduler2 = [aggSysTPSchedulers_0[lsIndex].total,aggSysTPSchedulers_5[rsIndex].total]
                    rects2 = ax.bar(ind+width, scheduler2, width, color='g')
                    break

    for lsIndex in range(0, len(aggSysTPSchedulers_0)):
        if aggSysTPSchedulers_0[lsIndex].schedularName == "ns3::FdBetFfMacScheduler":
            for rsIndex in range(0, len(aggSysTPSchedulers_5)):
                if aggSysTPSchedulers_5[rsIndex].schedularName == "ns3::FdBetFfMacScheduler":
                    scheduler3 = [aggSysTPSchedulers_0[lsIndex].total,aggSysTPSchedulers_5[rsIndex].total]
                    rects3 = ax.bar(ind+width*2, scheduler3, width, color='b')
                    break
    
    for lsIndex in range(0, len(aggSysTPSchedulers_0)):
        if aggSysTPSchedulers_0[lsIndex].schedularName == "ns3::TdMtFfMacScheduler":
            for rsIndex in range(0, len(aggSysTPSchedulers_5)):
                if aggSysTPSchedulers_5[rsIndex].schedularName == "ns3::TdMtFfMacScheduler":
                    scheduler4 = [aggSysTPSchedulers_0[lsIndex].total,aggSysTPSchedulers_5[rsIndex].total]
                    rects4 = ax.bar(ind+width*3, scheduler4, width, color='y')
                    break
    
    ax.set_ylabel('Average Aggregate System Throughput (Mbps)')
    ax.set_xticks(ind+width)
    ax.set_xticklabels(('0 m/s', '5 m/s'))
    
    ax.legend((rects1[0], rects2[0], rects3[0], rects4[0]), ('RoundRobin', 'Proportional Fair', 'BTAS', 'Max Throughput'), loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fontsize=10)

    try: # Remove file, if already exists
        os.remove("AggregateSysThroughput" + ".png")
    except:
        pass
    plt.savefig("AggregateSysThroughput" + ".png")
    plt.close()
    
    return schedulerInfo_0,schedulerInfo_5


# Calculates and plots Instantaneous throughput for IMSI-1 specific to speed
def CalculateInstantaneousThroughput_N_IMSI_1(schedulerInfo, value):
    if value == 5:
        plotName = "InstantThroughput_UE1_5"
    else:
        plotName = "InstantThroughput_UE1_0"

    legene = []
    for schedulerIndex in range(0, len(schedulerInfo)):
        if schedulerInfo[schedulerIndex].schedularName == "ns3::RrFfMacScheduler":
            for pairIndex in range(0, len(schedulerInfo[schedulerIndex].pairInfo)):
                if schedulerInfo[schedulerIndex].pairInfo[pairIndex].imsi == 1:
                    legene_r, = plt.plot(schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfTime, schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfParameter, 'r', label='RoundRobin')
                    break
        elif schedulerInfo[schedulerIndex].schedularName == "ns3::PfFfMacScheduler":
            for pairIndex in range(0, len(schedulerInfo[schedulerIndex].pairInfo)):
                if schedulerInfo[schedulerIndex].pairInfo[pairIndex].imsi == 1:
                    legene_g, = plt.plot(schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfTime, schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfParameter, 'g', label='Proportional Fair')
                    break
        elif schedulerInfo[schedulerIndex].schedularName == "ns3::FdBetFfMacScheduler":
            for pairIndex in range(0, len(schedulerInfo[schedulerIndex].pairInfo)):
                if schedulerInfo[schedulerIndex].pairInfo[pairIndex].imsi == 1:
                    legene_b, = plt.plot(schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfTime, schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfParameter, 'b', label='BTAS')
                    break
        elif schedulerInfo[schedulerIndex].schedularName == "ns3::TdMtFfMacScheduler":
            for pairIndex in range(0, len(schedulerInfo[schedulerIndex].pairInfo)):
                if schedulerInfo[schedulerIndex].pairInfo[pairIndex].imsi == 1:
                    legene_y, = plt.plot(schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfTime, schedulerInfo[schedulerIndex].pairInfo[pairIndex].listOfParameter, 'y', label='Max Throughput')
                    break
        else:
            print "Programming Error. Scenario should not occur!"

    plt.xlabel("Time (in sec)")
    plt.ylabel("Throughput (in Mbps)")
    plt.legend(handles=[legene_r, legene_g, legene_b, legene_y], loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fontsize=10)
    try: # Remove file, if already exists
        os.remove(plotName + ".png")
    except:
        pass
    plt.savefig(plotName + ".png")
    plt.close()


# Calculates Instantaneous throughput for IMSI-1
def PlotInstantaneousThroughput_IMSI_1(schedulerInfo_0, schedulerInfo_5):
    CalculateInstantaneousThroughput_N_IMSI_1(schedulerInfo_0, 0)
    CalculateInstantaneousThroughput_N_IMSI_1(schedulerInfo_5, 5)
    

# Calculates and plots Instantaneous throughput for IMSI-1 specific to speed
def CalculateSINR_IMSI_1(value):
    if value == 5:
        plotName = "SinrImsi_UE1_At5"
        rFile =open("myDlSinrStatsAt5.txt", 'r')
    else:
        plotName = "SinrImsi_UE1_At0"
        rFile =open("myDlSinrStatsAt0.txt", 'r')

    # List of Schedulers
    schedulers = []

    time = 0.0
    sinr = 0.0
    sinrdb = 0.0
    schedulerIndex = 0
    pairIndex = 0
    innerIndex = 0

    for line in rFile:
        data = line.split()
        # IMSI check
        if int(data[2]) != 1:
            continue

        time = float(data[0])
        schedulerIndex = getSchedulerIndex(schedulers, str(data[6]))
        if schedulerIndex == -1:
            # Add the scheduler Information
            obj = schedulerType()
            obj.schedularName = str(data[6])
            schedulers.append(obj)
            schedulerIndex = len(schedulers)-1

        # Search for IMSI :: 1
        found = 0
        for pairIndex in range(0, len(schedulers[schedulerIndex].pairInfo)):
            if schedulers[schedulerIndex].pairInfo[pairIndex].imsi == int(data[2]):
                found = 1
                break

        if not found:
            # Add IMSI/Cell-Id information
            obj = pairInfo()
            obj.cellid = int(data[1])
            obj.imsi = int(data[2])
            obj.listOfParameter = []
            obj.listOfTime = []
            schedulers[schedulerIndex].pairInfo.append(obj)
            pairIndex = len(schedulers[schedulerIndex].pairInfo) - 1
            # Initialize buckets of time interval : 0.1 seconds
            for timeInterval in range(0, gSimTime*10):
                obj = buckets()
                obj.total = 0.0 
                obj.count = 0
                obj.indicator = timeInterval/10
                schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter.append(obj)

        sinr = float(data[5]) # Sinr value column
        sinrdb = 10.0 * math.log10(sinr)

        # Store in buckets
        for timeInterval in range(0, len(schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter)):
            if schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[timeInterval].indicator > time:
                schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[timeInterval].total = schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[timeInterval].total + sinrdb
                schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[timeInterval].count = schedulers[schedulerIndex].pairInfo[pairIndex].listOfParameter[timeInterval].count + 1
                break

    # Average the Sinr Values
    result = []
    for schedulerIndex in range(0, len(schedulers)):
        obj = resultOutput()
        obj.totalList = []
        obj.total = 0.0
        obj.schedularName = schedulers[schedulerIndex].schedularName
        for paramIndex in range(0, len(schedulers[schedulerIndex].pairInfo[0].listOfParameter)):
            if schedulers[schedulerIndex].pairInfo[0].listOfParameter[paramIndex].count == 0:
                print "Error Scenario!!!"
                schedulers[schedulerIndex].pairInfo[0].listOfParameter[paramIndex].total = 0.0
            else:
                schedulers[schedulerIndex].pairInfo[0].listOfParameter[paramIndex].total = schedulers[schedulerIndex].pairInfo[0].listOfParameter[paramIndex].total / (float)(schedulers[schedulerIndex].pairInfo[0].listOfParameter[paramIndex].count)
            obj.totalList.append(schedulers[schedulerIndex].pairInfo[0].listOfParameter[paramIndex].total) # Storing in buckets
        result.append(obj)

    # Slots of Time
    timeList = []
    for index in range(0, gSimTime*10):
        timeList.append(((index+1)*1.0)/10.0)

    # Plot SINR for IMSI-1
    legene = []
    for schedulerIndex in range(0, len(result)):
        if result[schedulerIndex].schedularName == "ns3::RrFfMacScheduler":
            legene_r, = plt.plot(timeList, result[schedulerIndex].totalList, 'r', label='RoundRobin')
        elif result[schedulerIndex].schedularName == "ns3::PfFfMacScheduler":
            legene_g, = plt.plot(timeList, result[schedulerIndex].totalList, 'g', label='Proportional Fair')
        elif result[schedulerIndex].schedularName == "ns3::FdBetFfMacScheduler":
            legene_b, = plt.plot(timeList, result[schedulerIndex].totalList, 'b', label='BTAS')
        elif result[schedulerIndex].schedularName == "ns3::TdMtFfMacScheduler":
            legene_y, = plt.plot(timeList, result[schedulerIndex].totalList, 'y', label='Max Throughput')
        else:
            print "Programming Error. Scenario should not occur"

    plt.xlabel("Time (in sec)")
    plt.ylabel("SINR (in dB)")
    plt.ylim([-50,80])
    plt.legend(handles=[legene_r, legene_g, legene_b, legene_y], loc='upper center', bbox_to_anchor=(0.5, 1.05), ncol=4, fontsize=10)

    try: # Remove file, if already exists
        os.remove(plotName + ".png")
    except:
        pass
    plt.savefig(plotName + ".png")
    plt.close()

# Calculates and plots Instantaneous throughput for IMSI-1
def PlotSINR_IMSI_1():
    CalculateSINR_IMSI_1(0)
    CalculateSINR_IMSI_1(5)

if __name__ == "__main__": main()

