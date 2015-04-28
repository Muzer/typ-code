#!/usr/bin/env python3
"""Generate the working timetable. Run occasionally, when there are a few
   weeks' or more worth of data."""

import database_access
import datetime
import linedefs
import timetable_analyser

latestWttStartDate = datetime.datetime(year=2015, month=3, day=8, hour=0,
                                       minute=0, second=0)

def generateWtt():
    """Generate the timetable."""
    connection = database_access.connectToDb()
    # Get a list of unique set and trip number combinations. This is to decide
    # which services need to be looked for.
    uniqueSetTripNos = database_access.getUniqueSetTripNos(connection,
                                                           latestWttStartDate)
    for setNo, tripNo in uniqueSetTripNos:
        if setNo == "000":
            continue
        for line, station in linedefs.victoria:
            print((setNo, tripNo, line, station))
            # Mon-Fri
            for dayFrom, dayTo, dayChar in [(0, 5, "W"),  # Mon-Fri
                                            (5, 6, "S"),  # Sat
                                            (6, 7, "U")]: # Sun
                arrTime, depTime, destination, destCode, platformNumber = \
                timetable_analyser.calculate_median(
                    connection, latestWttStartDate,
                    station, setNo, tripNo, line, dayFrom, dayTo)
                if arrTime != None and depTime != None:
                    database_access.addTimetableEntry(
                        connection, setNo, tripNo,
                        destination, destCode, station, line, platformNumber,
                        arrTime, depTime, datetime.date.today(), dayChar)

generateWtt()
