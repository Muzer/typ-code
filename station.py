#!/usr/bin/env python3
"""Class definitions for station, platform and train"""

class Train:
    """Contains information about one snapshot of a train's position in
       relation to a platform at a station."""
    def __init__(self, lcid, setNo, tripNo, secondsTo, location, destination,
                 destCode, trackCode, ln, whenCreated):
        self.lcid = lcid
        self.setNo = setNo
        self.tripNo = tripNo
        self.secondsTo = secondsTo
        self.location = location
        self.destination = destination
        self.destCode = destCode
        self.trackCode = trackCode
        self.ln = ln
        self.whenCreated = whenCreated

class Platform:
    """Contains information about a platform."""
    def __init__(self, number, name, trackCode):
        self.number = number
        self.name = name
        self.trackCode = trackCode
        self.trains = []
    def addTrain(self, lcid, setNo, tripNo, secondsTo, location, destination,
                 destCode, trackCode, ln, whenCreated):
        """Create, add and return a train object, in relation to this
           platform."""
        train = Train(lcid, setNo, tripNo, secondsTo, location, destination,
                      destCode, trackCode, ln, whenCreated)
        self.trains.append(train)
        return train
    def getTrainByLcid(self, lcid):
        """Get a train by the leading carriage ID."""
        return [x for x in self.trains if x.lcid == lcid][0]
    def getTrainBySetTripNo(self, setNo, tripNo):
        """Get a train by set and trip numbers."""
        return [x for x in self.trains if x.setNo == setNo
                and x.tripNo == tripNo][0]
    def getTrainBySetNo(self, setNo):
        """Get a train by set number only."""
        return [x for x in self.trains if x.setNo == setNo][0]

class Station:
    """Contains information about a station."""
    def __init__(self, code, name, lineCode, lineName):
        self.code = code
        self.name = name
        self.lineCode = lineCode
        self.lineName = lineName
        self.platforms = []
    def addPlatform(self, number, name, trackCode):
        """Create, add and return a platform object for this station."""
        platform = Platform(number, name, trackCode)
        self.platforms.append(platform)
        return platform
    def getPlatform(self, number):
        """Get a platform by number."""
        return [x for x in self.platforms if x.number == number][0]
