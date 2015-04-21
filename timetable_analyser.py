#!/usr/bin/env python3

import database_access
import datetime
import math
import operator
import collections

#station="VIC"
#line="V"
#aroundDate=datetime.datetime(2015, 2, 3, 12, 0, 0)
#setNo="007"
#tripNo="2"

dwellTime=20

def setTrainArrDepFromPrev(connection, train, platform, station):
    results = database_access.findTrainArrDepObjectDate(connection,
        station.code, train.setNo, train.tripNo, train.whenCreated,
        station.lineCode)
    if len(results) == 0:
        arrTime = train.whenCreated + datetime.timedelta(
            seconds=train.secondsTo)
        depTime = arrTime + datetime.timedelta(seconds=dwellTime)
    else:
        result = results[0] # Assume only one; there should be only one
        oldArrTime = result[0]
        oldDepTime = result[1]
        if train.secondsTo == 0: # only change if violates expectations
            if train.whenCreated < oldArrTime:
                arrTime = train.whenCreated
            else:
                arrTime = oldArrTime
            if train.whenCreated > oldDepTime:
                depTime = train.whenCreated
            else:
                depTime = oldDepTime
        else:
            arrTime = train.whenCreated + datetime.timedelta(
                seconds=train.secondsTo)
            depTime = arrTime + datetime.timedelta(seconds=dwellTime)
    database_access.addTrainArrDepObject(connection, train, platform,
        station, arrTime, depTime)

def getTrainArrDep(connection, stationCode, setNo, tripNo, aroundDate, line):
    results = database_access.filterTrainsByStationIDAndDate(connection,
        stationCode, setNo, tripNo, aroundDate, line)
    results = list(results)

    # Get the earliest time for it to have arrived in the station
    arrivedTimes = (item for item in results if item.secondsTo == 0)
    arrivedTimes = sorted(arrivedTimes, key=lambda x : x.whenCreated)
    earliestArrived = arrivedTimes[0] if len(arrivedTimes) != 0 else None

    # Get the latest time for it to still be in the station (before depart)
    latestArrived = None
    for latestArrived in arrivedTimes:
        pass

    # Get the most accurate time for predicted arrival (LUL's predictions)
    arrLulPred = None
    for arrLulPred in results:
        if arrLulPred.secondsTo != 0:
            break

    # Predicted arrival time is earliest of arrived time and predicted arrive
    arrPredTime = None
    if arrLulPred != None:
        arrPredTime = arrLulPred.whenCreated + \
            datetime.timedelta(seconds=arrLulPred.secondsTo)
    if earliestArrived != None and (arrPredTime == None or 
        earliestArrived.whenCreated < arrPredTime):
        arrPredTime = earliestArrived.whenCreated

    depPredTime = None
    if latestArrived != None:
        depPredTime = latestArrived.whenCreated
    elif arrPredTime != None:
        depPredTime = arrPredTime + datetime.timedelta(seconds=dwellTime)
    
    return (arrPredTime, depPredTime)

def get_seconds(time):
    return time.hour * 60 * 60 + time.minute * 60 + time.second

def get_time(seconds):
    return datetime.time(hour=int(seconds + 0.5) // (60 * 60),
        minute=(int(seconds + 0.5) % (60 * 60)) // 60,
        second=int(seconds + 0.5) % 60)

def median(dictArray, getAttr):
    results = sorted(dictArray, key=lambda x: x[getAttr].time())
    if len(results) < 1:
        return None
    if len(results) % 2 == 1:
        return results[(len(results) - 1) // 2][getAttr].time()
    if len(results) % 2 == 0:
        return get_time((get_seconds(results[len(results)
          // 2][getAttr].time()) + get_seconds(results[len(results)
            // 2 - 1][getAttr].time())) / 2)

def mode(dictArray, getAttr):
    counter = collections.Counter(map(lambda x: x[getAttr], dictArray))
    return counter.most_common(1)[0][0]

def calculate_median(connection, startDate, stationCode, setNo, tripNo, line,
    dayFrom, dayTo): # dayFrom is minimum day of week (where 0 is monday),
            # dayTo is max plus one day of the week
    results = database_access.findTrainArrDepObjectsDateFrom(connection,
        startDate, stationCode, setNo, tripNo, line)
    results = [x for x in results if dayFrom <= x[0].weekday() < dayTo]
    
    # Calculate median
    arrMedian = median(results, 0) # arrTime
    depMedian = median(results, 1) # depTime
    if arrMedian == None or depMedian == None:
        return (None, None, None, None, None)

    # Modes of other useful things
    destMode = mode(results, 2) # destination
    dCodeMode = mode(results, 3) # destCode
    platNoMode = mode(results, 4) # platformNumber

    print(results)
    return (arrMedian, depMedian, destMode, dCodeMode, platNoMode)
