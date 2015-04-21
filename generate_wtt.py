#!/usr/bin/env python3

import database_access
import datetime
import linedefs
import timetable_analyser

latestWttStartDate = datetime.datetime(year=2015, month=3, day=8, hour=0,
    minute=0, second=0)

def generateWtt():
    connection = database_access.connectToDb()
    # Get a list of unique set and trip number combinations. This is to decide
    # which services need to be looked for.
    uniqueSetTripNos = database_access.getUniqueSetTripNos(connection,
        latestWttStartDate)
    for setNo, tripNo in uniqueSetTripNos:
        for line, station in linedefs.victoria:
            print((setNo, tripNo, line, station))
            # Mon-Fri
            arrTime, depTime, destination, destCode, platformNumber = \
            timetable_analyser.calculate_median(connection, latestWttStartDate,
                station, setNo, tripNo, line, 0, 5)
            if arrTime != None and depTime != None:
                database_access.addTimetableEntry(connection, setNo, tripNo,
                    destination, destCode, station, line, platformNumber,
                    arrTime, depTime, datetime.date.today(), "W")
            # Sat
            arrTime, depTime, destination, destCode, platformNumber = \
            timetable_analyser.calculate_median(connection, latestWttStartDate,
                station, setNo, tripNo, line, 5, 6)
            if arrTime != None and depTime != None:
                database_access.addTimetableEntry(connection, setNo, tripNo,
                    destination, destCode, station, line, platformNumber,
                    arrTime, depTime, datetime.date.today(), "S")
            # Sun
            arrTime, depTime, destination, destCode, platformNumber = \
            timetable_analyser.calculate_median(connection, latestWttStartDate,
                station, setNo, tripNo, line, 6, 7)
            if arrTime != None and depTime != None:
                database_access.addTimetableEntry(connection, setNo, tripNo,
                    destination, destCode, station, line, platformNumber,
                    arrTime, depTime, datetime.date.today(), "U")

generateWtt()
