#!/usr/bin/env python3

import mysql.connector
import station

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

def filterTrainsByStationIDAndDate(stationCode, setNo, tripNo, aroundDate,
    line):
    query = "SELECT * FROM trains WHERE stationCode = %s AND setNo = %s AND " \
        "tripNo = %s AND whenCreated BETWEEN %s AND %s " \
        "AND stationLineCode = %s ORDER BY secondsTo ASC"
    cursor.execute(query, (stationCode, setNo, tripNo, aroundDate -
      datetime.timedelta(hours=12), aroundDate + datetime.timedelta(hours=12),
      stationLineCode))
    return cursor.fetchall()

def addPlatformTree(connection, platformObj, stationObj):
    addPlatformObjectIfNotExists(connection, platformObj, stationObj)
    for trainObj in platformObj.trains:
        addTrainObject(connection, trainObj, platformObj, stationObj)

def addStationTree(connection, stationObj):
    addStationObjectIfNotExists(connection, stationObj) # Add station object
    for platformObj in stationObj.platforms:
        addPlatformTree(connection, platformObj, stationObj)
    connection.commit()
