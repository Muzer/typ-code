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

def addTimetableEntry(connection, setNo, tripNo, destination, destCode,
    stationCode, stationLineCode, platformNumber, arrTime, depTime,
    dateCreated, daysOfWeek):
    # daysOfWeek is "W" for weekdays, "S" for Saturdays, and "U" for Sundays
    query = "INSERT INTO timetables(setNo, tripNo, destination, destCode, " \
            "stationCode, stationLineCode, platformNumber, arrTime, depTime," \
            " dateCreated, daysOfWeek) VALUES(%s, %s, %s, %s, %s, %s, %s, " \
            "%s, %s, %s, %s)"
    cursor = connection.cursor()
    cursor.execute(query, (setNo, tripNo, destination, destCode, stationCode,
        stationLineCode, platformNumber, arrTime, depTime, dateCreated,
        daysOfWeek))

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

def findTrainArrDepObjectsNoIds(connection, stationCode, aroundDate, line):
    query = "SELECT lcid, setNo, tripNo, destination, destCode, ln, " \
            "platformNumber, arrTime, depTime FROM trainsArrDep WHERE " \
            "stationCode = %s AND (arrTime BETWEEN %s AND %s OR depTime " \
            "BETWEEN %s AND %s) AND stationLineCode = %s ORDER BY depTime, " \
            "arrTime"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, aroundDate - datetime.timedelta(
        hours=1), aroundDate + datetime.timedelta(hours=1), aroundDate -
        datetime.timedelta(hours=1), aroundDate + datetime.timedelta(hours=1),
        line))
    results = cursor.fetchall()
    return map(lambda item : {"lcid": item[0], "setNo": item[1],
      "tripNo": item[2], "destination": item[3], "destCode": item[4],
      "ln": item[5], "platformNumber": item[6],
      "aArrTime": item[7].strftime("%H%M"),
      "aDepTime": item[8].strftime("%H%M")}, results)

def findTimetableEntriesNoIds(connection, stationCode, aroundDate, line):
    query = "SELECT setNo, tripNo, destination, destCode, stationLineCode, " \
            "platformNumber, arrTime, depTime FROM timetables WHERE " \
            "stationCode = %s AND (arrTime BETWEEN %s AND %s OR depTime " \
            "BETWEEN %s AND %s) AND stationLineCode = %s AND daysOfWeek = %s " \
            "ORDER BY depTime, arrTime"
    cursor = connection.cursor()
    weekday = "S" if aroundDate.weekday() == 5 else "U" if \
        aroundDate.weekday() == 6 else "W"
    cursor.execute(query, (stationCode, (aroundDate - datetime.timedelta(
        hours=1)).time(), (aroundDate + datetime.timedelta(hours=1)).time(),
        (aroundDate - datetime.timedelta(hours=1)).time(), (aroundDate
          + datetime.timedelta(hours=1)).time(), line, weekday))
    results = cursor.fetchall()
    return map(lambda item : {"setNo": item[0], "tripNo": item[1],
      "destination": item[2], "destCode": item[3], "ln": item[4],
      "platformNumber": item[5],
      "sArrTime": (datetime.datetime.min + item[6]).time().strftime("%H%M"),
      "sDepTime": (datetime.datetime.min + item[7]).time().strftime("%H%M")},
      results)

def findTrainArrDepObjectDate(connection, stationCode, setNo, tripNo, 
    aroundDate, line):
    query = "SELECT arrTime, depTime, lcid FROM trainsArrDep WHERE " \
        "stationCode = %s AND setNo = %s AND tripNo = %s AND " \
        "arrTime BETWEEN %s AND %s AND stationLineCode = %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
        datetime.timedelta(hours=12),
        aroundDate + datetime.timedelta(hours=12), line))
    return cursor.fetchall()

def findTrainArrDepObjectsDateFrom(connection, startDate, stationCode, setNo,
    tripNo, line):
    query = "SELECT arrTime, depTime, destination, destCode, platformNumber " \
            "FROM trainsArrDep WHERE stationCode = %s AND setNo = %s " \
            "AND tripNo = %s AND stationLineCode = %s AND arrTime >= %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, line, startDate))
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

def getUniqueSetTripNos(connection, startDate):
    query = "SELECT DISTINCT setNo, tripNo FROM trainsArrDep WHERE " \
        "arrTime >= %s"
    cursor = connection.cursor()
    cursor.execute(query, (startDate,))
    return cursor.fetchall()

def getStationNameById(connection, code):
    query = "SELECT name FROM stations WHERE code = %s"
    cursor = connection.cursor()
    cursor.execute(query, (code,))
    return cursor.fetchall()

def searchStationLine(connection, station, line):
    query = "SELECT code, lineCode FROM stations WHERE (code = %s OR " \
        "name LIKE %s) AND (lineCode = %s OR lineName LIKE %s)"
    cursor = connection.cursor()
    cursor.execute(query, (station, "%" + station + "%", line,
      "%" + line + "%"))
    return cursor.fetchall()

def addPlatformTree(connection, platformObj, stationObj):
    addPlatformObjectIfNotExists(connection, platformObj, stationObj)
    for trainObj in platformObj.trains:
        addTrainObject(connection, trainObj, platformObj, stationObj)
        timetable_analyser.setTrainArrDepFromPrev(connection, trainObj,
            platformObj, stationObj)

def addStationTree(connection, stationObj):
    addStationObjectIfNotExists(connection, stationObj) # Add station object
    for platformObj in stationObj.platforms:
        addPlatformTree(connection, platformObj, stationObj)
    connection.commit()
