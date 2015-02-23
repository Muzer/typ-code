#!/usr/bin/env python3

import mysql.connector
import station
import datetime
import timetable_analyser

def connectToDb():
    return mysql.connector.connect(user='rtlul', password='dummypassword',
            database='rtlul') # TODO make this read from a file

def addStationObjectIfNotExists(connection, stationObj):
    # Check for existence
    query = "SELECT EXISTS" \
            "(SELECT 1 FROM stations WHERE lineCode=%s AND code=%s)"
    cursor = connection.cursor()
    cursor.execute(query, (stationObj.lineCode, stationObj.code))
    if cursor.fetchall()[0][0] == 0: # doesn't exist
        query = "INSERT INTO stations(lineCode, code, name, lineName) " \
                "VALUES(%s, %s, %s, %s)"
        cursor.execute(query, (stationObj.lineCode, stationObj.code,
            stationObj.name, stationObj.lineName))
    else:
        query = "UPDATE stations SET name=%s, lineName=%s " \
                "WHERE lineCode=%s AND code=%s"
        cursor.execute(query, (stationObj.name, stationObj.lineName,
            stationObj.lineCode, stationObj.code))

def addPlatformObjectIfNotExists(connection, platformObj, stationObj):
    # Check for existence
    query = "SELECT EXISTS(SELECT 1 FROM platforms " \
            "WHERE stationLineCode=%s AND stationCode=%s AND number=%s)"
    cursor = connection.cursor()
    cursor.execute(query, (stationObj.lineCode, stationObj.code,
        platformObj.number))
    if cursor.fetchall()[0][0] == 0: # doesn't exist
        query = "INSERT INTO platforms(stationLineCode, stationCode, number," \
                " name, trackCode) VALUES(%s, %s, %s, %s, %s)"
        cursor.execute(query, (stationObj.lineCode, stationObj.code,
            platformObj.number, platformObj.name, platformObj.trackCode))
    else:
        query = "UPDATE platforms SET name=%s, trackCode=%s " \
                "WHERE stationLineCode=%s AND stationCode=%s AND number=%s"
        cursor.execute(query, (platformObj.name, platformObj.trackCode,
            stationObj.lineCode, stationObj.code, platformObj.number))

# t is trainObj, abbreviated because referenced so much
def addTrainObject(connection, t, platformObj, stationObj):
    # Check for existence (duplicate train, caused by cache being slower than
    # spec'd)
    query = "SELECT EXISTS(SELECT 1 FROM trains WHERE stationLineCode=%s " \
            "AND stationCode=%s AND platformNumber=%s AND whenCreated=%s AND" \
            " lcid=%s)"
    cursor = connection.cursor()
    cursor.execute(query, (stationObj.lineCode, stationObj.code,
        platformObj.number, t.whenCreated, t.lcid))
    if cursor.fetchall()[0][0] == 0: # doesn't exist
        query = "INSERT INTO trains(lcid, setNo, tripNo, secondsTo, " \
                "location, destination, destCode, trackCode, ln, " \
                "whenCreated, stationCode, stationLineCode, platformNumber) " \
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (t.lcid, t.setNo, t.tripNo, t.secondsTo,
            t.location, t.destination, t.destCode, t.trackCode, t.ln,
            t.whenCreated, stationObj.code, stationObj.lineCode,
            platformObj.number))
    else:
        print("Duplicate train ignored")

def addTrainArrDepObject(connection, t, platformObj, stationObj, arrTime,
    depTime):
    query = "SELECT EXISTS(SELECT 1 FROM trainsArrDep WHERE " \
            "stationLineCode=%s AND stationCode=%s AND platformNumber=%s AND" \
            " arrTime=%s AND deptime=%s AND lcid=%s)"
    cursor = connection.cursor()
    cursor.execute(query, (stationObj.lineCode, stationObj.code,
        platformObj.number, arrTime, depTime, t.lcid))
    if cursor.fetchall()[0][0] == 0: # doesn't exist
        delTrainArrDepObject(connection, stationObj.code, t.setNo, t.tripNo,
            arrTime, stationObj.lineCode)
        query = "INSERT INTO trainsArrDep(lcid, setNo, tripNo, destination, " \
                "destCode, ln, stationCode, stationLineCode, platformNumber," \
                " arrTime, depTime) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, " \
                "%s, %s, %s)"
        cursor.execute(query, (t.lcid, t.setNo, t.tripNo, t.destination,
          t.destCode, t.ln, stationObj.code, stationObj.lineCode,
          platformObj.number, arrTime, depTime))
    else:
        print("Duplicate train arrival/departure object ignored")

def findTrainArrDepObject(connection, stationCode, setNo, tripNo, aroundDate,
    line):
    query = "SELECT arrTime, depTime FROM trainsArrDep WHERE " \
        "stationCode = %s AND setNo = %s AND tripNo = %s AND " \
        "arrTime BETWEEN %s AND %s AND stationLineCode = %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
        datetime.timedelta(hours=12),
        aroundDate + datetime.timedelta(hours=12), line))
    return cursor.fetchall()

def delTrainArrDepObject(connection, stationCode, setNo, tripNo, aroundDate,
    line):
    query = "DELETE FROM trainsArrDep WHERE stationCode = %s AND setNo = %s " \
            "AND tripNo = %s AND arrTime BETWEEN %s and %s AND " \
            "stationLineCode = %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
        datetime.timedelta(hours=12),
        aroundDate + datetime.timedelta(hours=12), line))

def filterTrainsByStationIDAndDate(connection, stationCode, setNo, tripNo,
    aroundDate, line):
    query = "SELECT lcid, setNo, tripNo, secondsTo, location, destination, " \
        "destCode, trackCode, ln, whenCreated FROM trains WHERE " \
        "stationCode = %s AND setNo = %s AND tripNo = %s AND " \
        "whenCreated BETWEEN %s AND %s AND stationLineCode = %s " \
        "ORDER BY secondsTo ASC, whenCreated DESC"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
        datetime.timedelta(hours=12),
        aroundDate + datetime.timedelta(hours=12), line))
    return map(lambda item : station.Train(item[0], item[1], item[2], item[3],
        item[4], item[5], item[6], item[7], item[8], item[9]),
        cursor.fetchall())

def addPlatformTree(connection, platformObj, stationObj):
    addPlatformObjectIfNotExists(connection, platformObj, stationObj)
    for trainObj in platformObj.trains:
        addTrainObject(connection, trainObj, platformObj, stationObj)
        # TODO move this out of here
        timetable_analyser.setTrainArrDepFromPrev(connection, trainObj,
            platformObj, stationObj)

def addStationTree(connection, stationObj):
    addStationObjectIfNotExists(connection, stationObj) # Add station object
    for platformObj in stationObj.platforms:
        addPlatformTree(connection, platformObj, stationObj)
    connection.commit()
