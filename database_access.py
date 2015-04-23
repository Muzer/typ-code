#!/usr/bin/env python3
"""Perform database-related functionality for rtlul"""

import mysql.connector
import station
import datetime
import timetable_analyser

def connectToDb():
    """Connect to the database"""
    return mysql.connector.connect(user='rtlul', password='dummypassword',
                                   database='rtlul')

def addStationObjectIfNotExists(connection, stationObj):
    """Add a station object to the database if it doesn't already exist"""
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
    """Add a platform object to the database if it doesn't already exist"""
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
                               platformObj.number, platformObj.name,
                               platformObj.trackCode))
    else:
        query = "UPDATE platforms SET name=%s, trackCode=%s " \
                "WHERE stationLineCode=%s AND stationCode=%s AND number=%s"
        cursor.execute(query, (platformObj.name, platformObj.trackCode,
                               stationObj.lineCode, stationObj.code,
                               platformObj.number))

# t is trainObj, abbreviated because referenced so much
def addTrainObject(connection, t, platformObj, stationObj):
    """Add a train object to the database if it doesn't already exist"""
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
                               t.location, t.destination, t.destCode,
                               t.trackCode, t.ln, t.whenCreated,
                               stationObj.code, stationObj.lineCode,
                               platformObj.number))
    else:
        print("Duplicate train ignored")

def addTimetableEntry(connection, setNo, tripNo, destination, destCode,
                      stationCode, stationLineCode, platformNumber, arrTime,
                      depTime, dateCreated, daysOfWeek):
    """Add a timetable entry to the database"""
    # daysOfWeek is "W" for weekdays, "S" for Saturdays, and "U" for Sundays
    query = "INSERT INTO timetables(setNo, tripNo, destination, destCode, " \
            "stationCode, stationLineCode, platformNumber, arrTime, depTime," \
            " dateCreated, daysOfWeek) VALUES(%s, %s, %s, %s, %s, %s, %s, " \
            "%s, %s, %s, %s)"
    cursor = connection.cursor()
    cursor.execute(query, (setNo, tripNo, destination, destCode, stationCode,
                           stationLineCode, platformNumber, arrTime, depTime,
                           dateCreated, daysOfWeek))

def addTrainArrDepObject(connection, t, platformObj, stationObj, arrTime,
                         depTime):
    """Add a train arrival/departure record to the database"""
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
                               t.destCode, t.ln, stationObj.code,
                               stationObj.lineCode, platformObj.number,
                               arrTime, depTime))
    else:
        print("Duplicate train arrival/departure object ignored")

def findTrainArrDepObjectsNoIds(connection, stationCode, aroundDate, line):
    """Find train arrival/departure records by station code, datetime (within
       one hour) and line. Return as dictionary for website."""
    query = "SELECT lcid, setNo, tripNo, destination, destCode, ln, " \
            "platformNumber, arrTime, depTime FROM trainsArrDep WHERE " \
            "stationCode = %s AND (arrTime BETWEEN %s AND %s OR depTime " \
            "BETWEEN %s AND %s) AND stationLineCode = %s ORDER BY depTime, " \
            "arrTime"
    cursor = connection.cursor()
    cursor.execute(query, (
        stationCode, aroundDate - datetime.timedelta(hours=1),
        aroundDate + datetime.timedelta(hours=1), aroundDate -
        datetime.timedelta(hours=1), aroundDate + datetime.timedelta(hours=1),
        line))
    results = cursor.fetchall()
    return map(lambda item: {
        "lcid": item[0], "setNo": item[1],
        "tripNo": item[2], "destination": item[3], "destCode": item[4],
        "ln": item[5], "platformNumber": item[6],
        "aArrTime": item[7].strftime("%H%M"), "oaArrTime": item[7],
        "aDepTime": item[8].strftime("%H%M"), "oaDepTime": item[8]}, results)

def assTime(timedelta, aroundDate):
    """Given a date and a time, combine the date with the time such that the
       final date is within twelve hours."""
    # We need to assign the time to a date.
    assdTime = datetime.datetime.combine(aroundDate.date(), \
        (datetime.datetime.min + timedelta).time())
    # now correct for day boundary
    if assdTime > aroundDate + datetime.timedelta(hours=12):
        assdTime -= datetime.timedelta(days=1)
    if assdTime < aroundDate - datetime.timedelta(hours=12):
        assdTime += datetime.timedelta(days=1)
    return assdTime

def findTimetableEntriesNoIds(connection, stationCode, aroundDate, line):
    """Find timetable records by station code, datetime (within one hour) and
       line. Return as dictionary for website."""
    query = "SELECT setNo, tripNo, destination, destCode, stationLineCode, " \
            "platformNumber, arrTime, depTime FROM timetables WHERE " \
            "stationCode = %s AND (arrTime BETWEEN %s AND %s OR " \
            "depTime BETWEEN %s AND %s OR " \
            "(%s >= TIME '22:00' AND (arrTime BETWEEN %s AND TIME '24:00' OR" \
            " arrTime BETWEEN TIME '00:00' AND %s OR " \
            "depTime BETWEEN %s AND TIME '24:00' OR " \
            "depTime BETWEEN TIME '00:00' AND %s))) AND " \
            "stationLineCode = %s AND daysOfWeek = %s " \
            "ORDER BY depTime, arrTime"
    cursor = connection.cursor()
    weekday = "S" if aroundDate.weekday() == 5 else "U" if \
        aroundDate.weekday() == 6 else "W"
    timea = (aroundDate - datetime.timedelta(hours=1)).time()
    timeb = (aroundDate + datetime.timedelta(hours=1)).time()
    cursor.execute(query, (stationCode, timea, timeb, timea, timeb, timea,
                           timea, timeb, timea, timeb, line, weekday))
    results = cursor.fetchall()
    return map(lambda item: {
        "setNo": item[0], "tripNo": item[1],
        "destination": item[2], "destCode": item[3], "ln": item[4],
        "platformNumber": item[5],
        "sArrTime": (datetime.datetime.min + item[6]).time().strftime("%H%M"),
        "osArrTime": assTime(item[6], aroundDate),
        "sDepTime": (datetime.datetime.min + item[7]).time().strftime("%H%M"),
        "osDepTime": assTime(item[7], aroundDate)}, results)

def findTrainArrDepObjectDate(connection, stationCode, setNo, tripNo,
                              aroundDate, line):
    """Find train arrival/departure records by station code, set number, trip
       number, date (within twelve hours) and line. Return as (arrTime,
       depTime, lcid) tuple."""
    query = "SELECT arrTime, depTime, lcid FROM trainsArrDep WHERE " \
        "stationCode = %s AND setNo = %s AND tripNo = %s AND " \
        "arrTime BETWEEN %s AND %s AND stationLineCode = %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
                           datetime.timedelta(hours=12),
                           aroundDate + datetime.timedelta(hours=12), line))
    return cursor.fetchall()

def findTrainArrDepObjectNoStn(connection, setNo, tripNo, aroundDate, line):
    """Find train arrival/departure records by set number, trip number, date
       (within twelve hours) and line. Return as dictionary for website."""
    query = "SELECT t.arrTime, t.depTime, t.lcid, t.destination, t.destCode," \
        " t.stationCode, t.platformNumber, s.name FROM trainsArrDep t, " \
        "stations s WHERE t.setNo = %s AND t.tripNo = %s AND " \
        "t.arrTime BETWEEN %s AND %s AND t.stationLineCode = %s AND " \
        "t.stationCode = s.code ORDER BY depTime, arrTime"
    cursor = connection.cursor()
    cursor.execute(query, (setNo, tripNo, aroundDate -
                           datetime.timedelta(hours=12),
                           aroundDate + datetime.timedelta(hours=12), line))
    results = cursor.fetchall()
    return map(lambda item: {
        "lcid": item[2], "stationCode": item[5],
        "stationName": item[7], "destination": item[3], "destCode": item[4],
        "platformNumber": item[6],
        "aArrTime": item[0].strftime("%H%M"), "oaArrTime": item[0],
        "aDepTime": item[1].strftime("%H%M"), "oaDepTime": item[1]}, results)

def findTimetableEntriesNoStn(connection, setNo, tripNo, aroundDate, line):
    """Find timetable records by set number, trip number, date (within twelve
       hours) and line. Return as dictionary for website."""
    query = "SELECT t.arrTime, t.depTime, t.destination, t.destCode, " \
        "t.stationCode, t.platformNumber, s.name FROM timetables t, " \
        "stations s WHERE t.setNo = %s AND t.tripNo = %s AND " \
        "(t.arrTime BETWEEN %s AND TIME '24:00' OR " \
        "t.arrTime BETWEEN TIME '00:00' AND %s) AND t.stationLineCode = %s " \
        "AND daysOfWeek = %s AND t.stationCode = s.code " \
        "ORDER BY depTime, arrTime"
    cursor = connection.cursor()
    weekday = "S" if aroundDate.weekday() == 5 else "U" if \
        aroundDate.weekday() == 6 else "W"
    cursor.execute(query, (
        setNo, tripNo, (aroundDate - datetime.timedelta(hours=12)).time(),
        (aroundDate + datetime.timedelta(hours=12)).time(), line, weekday))
    results = cursor.fetchall()
    return map(lambda item: {
        "stationCode": item[4],
        "stationName": item[6], "destination": item[2], "destCode": item[3],
        "platformNumber": item[5],
        "sArrTime": (datetime.datetime.min + item[0]).time().strftime("%H%M"),
        "osArrTime": assTime(item[0], aroundDate),
        "sDepTime": (datetime.datetime.min + item[1]).time().strftime("%H%M"),
        "osDepTime": assTime(item[1], aroundDate)}, results)

def findTrainArrDepObjectsDateFrom(connection, startDate, stationCode, setNo,
                                   tripNo, line):
    """Find train arrival/departure records from a certain date by station
       code, set number, trip number and line. Return as (arrTime, depTime,
       destination, destCode, platformNumber) tuple"""
    query = "SELECT arrTime, depTime, destination, destCode, platformNumber " \
            "FROM trainsArrDep WHERE stationCode = %s AND setNo = %s " \
            "AND tripNo = %s AND stationLineCode = %s AND arrTime >= %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, line, startDate))
    return cursor.fetchall()

def delTrainArrDepObject(connection, stationCode, setNo, tripNo, aroundDate,
                         line):
    """Delete train arrival/departure record by station code, set number, trip
       number, date (within twelve hours) and line."""
    query = "DELETE FROM trainsArrDep WHERE stationCode = %s AND setNo = %s " \
            "AND tripNo = %s AND arrTime BETWEEN %s and %s AND " \
            "stationLineCode = %s"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
                           datetime.timedelta(hours=12),
                           aroundDate + datetime.timedelta(hours=12), line))

def filterTrainsByStationIDAndDate(connection, stationCode, setNo, tripNo,
                                   aroundDate, line):
    """Return train objects by station code, set number, trip number, date
       (within twelve hours) and line."""
    query = "SELECT lcid, setNo, tripNo, secondsTo, location, destination, " \
        "destCode, trackCode, ln, whenCreated FROM trains WHERE " \
        "stationCode = %s AND setNo = %s AND tripNo = %s AND " \
        "whenCreated BETWEEN %s AND %s AND stationLineCode = %s " \
        "ORDER BY secondsTo ASC, whenCreated DESC"
    cursor = connection.cursor()
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
                           datetime.timedelta(hours=12),
                           aroundDate + datetime.timedelta(hours=12), line))
    return map(lambda item: station.Train(
        item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7],
        item[8], item[9]), cursor.fetchall())

def getUniqueSetTripNos(connection, startDate):
    """Get a list of tuples containing set and trip numbers in use from a
       certain date."""
    query = "SELECT DISTINCT setNo, tripNo FROM trainsArrDep WHERE " \
        "arrTime >= %s"
    cursor = connection.cursor()
    cursor.execute(query, (startDate,))
    return cursor.fetchall()

def getStationNameById(connection, code):
    """Get station name by code."""
    query = "SELECT name FROM stations WHERE code = %s"
    cursor = connection.cursor()
    cursor.execute(query, (code,))
    return cursor.fetchall()

def getLineNameById(connection, code):
    """Get line name by code."""
    query = "SELECT lineName FROM stations WHERE lineCode = %s"
    cursor = connection.cursor()
    cursor.execute(query, (code,))
    return cursor.fetchall()

def searchStationLine(connection, stationName, line):
    """For search purposes, get a station and line code by matching substrings
       of given names of station and line code."""
    query = "SELECT code, lineCode FROM stations WHERE (code = %s OR " \
        "name LIKE %s) AND (lineCode = %s OR lineName LIKE %s)"
    cursor = connection.cursor()
    cursor.execute(query, (stationName, "%" + stationName + "%", line,
                           "%" + line + "%"))
    return cursor.fetchall()

def addPlatformTree(connection, platformObj, stationObj):
    """Add platform and all trains contained within."""
    addPlatformObjectIfNotExists(connection, platformObj, stationObj)
    for trainObj in platformObj.trains:
        addTrainObject(connection, trainObj, platformObj, stationObj)
        timetable_analyser.setTrainArrDepFromPrev(connection, trainObj,
                                                  platformObj, stationObj)

def addStationTree(connection, stationObj):
    """Add station and all platforms and trains contained within."""
    addStationObjectIfNotExists(connection, stationObj) # Add station object
    for platformObj in stationObj.platforms:
        addPlatformTree(connection, platformObj, stationObj)
    connection.commit()
