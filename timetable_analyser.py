#!/usr/bin/env python3

import database_access
import datetime

#station="VIC"
#line="V"
#aroundDate=datetime.datetime(2015, 2, 3, 12, 0, 0)
#setNo="007"
#tripNo="2"

dwellTime=20

def setTrainArrDepFromPrev(connection, train, platform, station):
    results = database_access.findTrainArrDepObject(connection, station.code,
        train.setNo, train.tripNo, train.whenCreated, station.lineCode)
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


#connection = database_access.connectToDb()
#arrPredTime, depPredTime = getTrainArrDep(connection, station, setNo, tripNo,
#      aroundDate, line)
#if arrPredTime == None or depPredTime == None:
#    print("Something went wrong. Did you actually specify a real train?")
#print(arrPredTime)
#print(depPredTime)
