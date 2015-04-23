#!/usr/bin/env python3
"""Logs data for train arrivals/departures into database"""

import trackernet_access
import database_access
import linedefs
import time

def main():
    """Logs data for train arrivals/departures into database"""
    connection = database_access.connectToDb()
    while True:
        for line, station in linedefs.victoria:
            print("Getting station {line}/{station}.".format(line=line,
                                                             station=station))
            stationObj = trackernet_access.getStation(line, station)
            database_access.addStationTree(connection, stationObj)
            print("Done")
            # Add train arrival/departure object
            # sleep such that the time between gets will be 30 seconds,
            # factoring in get time of about half a second
            time.sleep((30-0.5*len(linedefs.victoria))/len(linedefs.victoria))

main()
