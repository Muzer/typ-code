#!/usr/bin/env python3

class Train:
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
    def __init__(self, number, name, trackCode):
        self.number = number
        self.name = name
        self.trackCode = trackCode
        self.trains = []
    def addTrain(self, lcid, setNo, tripNo, secondsTo, location, destination,
            destCode, trackCode, ln, whenCreated): # create train, add, return
        train = Train(lcid, setNo, tripNo, secondsTo, location, destination,
                destCode, trackCode, ln, whenCreated)
        self.trains.append(train)
        return train
    def getTrainByLcid(self, lcid):
        return [x for x in self.trains if x.lcid == lcid][0]
    def getTrainBySetTripNo(self, setNo, tripNo):
        return [x for x in self.trains if x.setNo == setNo
            and x.tripNo == tripNo][0]
    def getTrainBySetNo(self, setNo):
        return [x for x in self.trains if x.setNo == setNo][0]

class Station:
    def __init__(self, code, name, lineCode, lineName):
        self.code = code
        self.name = name
        self.lineCode = lineCode
        self.lineName = lineName
        self.platforms = []
    def addPlatform(self, number, name, trackCode): # create new platform, add,
                                                    # return it
        platform = Platform(number, name, trackCode)
        self.platforms.append(platform)
        return platform
    def getPlatform(self, number):
        return [x for x in self.platforms if x.number == number][0]
