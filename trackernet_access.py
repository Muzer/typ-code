#!/usr/bin/env python3
"""Functions to communicate with TrackerNet, the London Underground open data
   system for train movements."""

import lxml.etree
import urllib.parse
import station
import datetime
import locale

predictionDetailed = \
    "http://cloud.tfl.gov.uk/TrackerNet/PredictionDetailed/{line}/{station}"

def parseDateWithCLocale(dateStr, formatStr):
    """NOT THREADSAFE; modifies global state. Parse the given date string with
       the "C" locale and given format string."""
    savedLocale = locale.setlocale(locale.LC_TIME)
    try:
        locale.setlocale(locale.LC_TIME, "C")
        return datetime.datetime.strptime(dateStr, formatStr)
    finally:
        locale.setlocale(locale.LC_TIME, savedLocale)

def generateUrl(line, stn):
    """Return a URL to request the given line and station from TrackerNet"""
    return predictionDetailed.format(
        line=urllib.parse.quote(line, safe=''),
        station=urllib.parse.quote(stn, safe=''))

def getXmlTree(url):
    """Get XML from given URL and return lxml etree."""
    return lxml.etree.parse(url)

def xmlPlatformGetTrains(platformObj, platformElement, whenCreated):
    """Add trains to a given platform object from a given platform tree."""
    for trainElement in platformElement.iter("{http://trackernet.lul.co.uk}T"):
        lcid = trainElement.get("LCID")
        setNo = trainElement.get("SetNo")
        tripNo = trainElement.get("TripNo")
        secondsTo = int(trainElement.get("SecondsTo"))
        location = trainElement.get("Location")
        destination = trainElement.get("Destination")
        destCode = trainElement.get("DestCode")
        trackCode = trainElement.get("TrackCode")
        ln = trainElement.get("LN")
        platformObj.addTrain(lcid, setNo, tripNo, secondsTo, location,
                             destination, destCode, trackCode, ln, whenCreated)

def xmlStationGetPlatforms(stationObj, stationElement, whenCreated):
    """Add platforms to a given station object from a given station tree."""
    for platformElement in \
            stationElement.iter("{http://trackernet.lul.co.uk}P"):
        name = platformElement.get("N")
        number = platformElement.get("Num")
        trackCode = platformElement.get("TrackCode")
        platformObj = stationObj.addPlatform(number, name, trackCode)
        xmlPlatformGetTrains(platformObj, platformElement, whenCreated)

def xmlRootGetStation(root, whenCreated):
    """Get the station object from the XML root element and given date."""
    lineCode = root.findtext("{http://trackernet.lul.co.uk}Line")
    lineName = root.findtext("{http://trackernet.lul.co.uk}LineName")
    stationElement = root.find("{http://trackernet.lul.co.uk}S")
    code = stationElement.get("Code")
    name = stationElement.get("N")
    stationObj = station.Station(code, name, lineCode, lineName)
    xmlStationGetPlatforms(stationObj, stationElement, whenCreated)
    return stationObj

def xmlTreeToStation(tree):
    """Get the station object including date created from XML tree."""
    # Get the station
    root = tree.getroot()
    whenCreatedStr = root.findtext("{http://trackernet.lul.co.uk}WhenCreated")
    whenCreated = parseDateWithCLocale(whenCreatedStr, "%d %b %Y %H:%M:%S")
    stationObj = xmlRootGetStation(root, whenCreated)
    return stationObj

def getStation(line, stn):
    """Get station object from given line and station."""
    url = generateUrl(line, stn)
    tree = getXmlTree(url)
    return xmlTreeToStation(tree)
