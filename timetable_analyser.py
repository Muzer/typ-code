#!/usr/bin/env python3
"""Various functions to perform analysis on trains, to produce a timetable."""

import database_access
import datetime
import collections

dwellTime = 20

def calculateTrainArrDepFromPrev(prev, train):
    if len(prev) == 0:
        arrTime = train.whenCreated + datetime.timedelta(
            seconds=train.secondsTo)
        depTime = arrTime + datetime.timedelta(seconds=dwellTime)
    else:
        result = prev[0] # Assume only one; there should be only one
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
    return (arrTime, depTime)

def setTrainArrDepFromPrev(connection, train, platform, station):
    """Given a train, create and add a train arrival/departure record for the
       train."""
    results = database_access.findTrainArrDepObjectDate(
        connection, station.code, train.setNo, train.tripNo, train.whenCreated,
        station.lineCode)
    arrTime, depTime = calculateTrainArrDepFromPrev(results, train)
    database_access.addTrainArrDepObject(connection, train, platform,
                                         station, arrTime, depTime)

def getSeconds(time):
    """Get number of seconds from a time"""
    return time.hour * 60 * 60 + time.minute * 60 + time.second

def getTime(seconds):
    """Convert number of seconds to a time."""
    return datetime.time(hour=int(seconds + 0.5) // (60 * 60),
                         minute=(int(seconds + 0.5) % (60 * 60)) // 60,
                         second=int(seconds + 0.5) % 60)

def median(dictArray, getAttr):
    """Calculate a median from a list of dicts with dictArray[getAttr] being a
       datetime and only the times being relevant (ie not dates). Returns a
       time."""
    results = sorted(dictArray, key=lambda x: x[getAttr].time())
    if len(results) < 1:
        return None
    if len(results) % 2 == 1:
        return results[(len(results) - 1) // 2][getAttr].time()
    if len(results) % 2 == 0:
        return getTime((
            getSeconds(
                results[len(results) // 2][getAttr].time())
            + getSeconds(
                results[len(results) // 2 - 1][getAttr].time())) / 2)

def mode(dictArray, getAttr):
    """Calculate mode from a list of dicts with dictarray[getAttr] being the
       thing to look for."""
    counter = collections.Counter(map(lambda x: x[getAttr], dictArray))
    return counter.most_common(1)[0][0]

def calculateMedianFromTrainArrDeps(results, dayFrom, dayTo):
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

def calculateMedian(connection, startDate, stationCode, setNo, tripNo, line,
                     dayFrom, dayTo):
    """Calculate median for timetable for given train info. dayFrom is minimum
       day of the week (where 0 is Monday) and dayTo is max plus one day of the
       week"""
    results = database_access.findTrainArrDepObjectsDateFrom(
        connection, startDate, stationCode, setNo, tripNo, line)
    return calculateMedianFromTrainArrDeps(results, dayFrom, dayTo)
