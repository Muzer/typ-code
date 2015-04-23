#!/usr/bin/env python3
"""Flask-based web interface for viewing timetables"""

import flask
import database_access
import datetime
import traceback

app = flask.Flask(__name__)
connection = database_access.connectToDb()

@app.route("/station/search")
def search():
    """Looks up station by name and redirects to results."""
    stn = flask.request.args['station']
    dt = flask.request.args['datetime']
    try:
        dt = datetime.datetime.strptime(dt, "%d/%m/%Y %H:%M")
    except:
        flask.abort(400)
    line = flask.request.args['line']

    res = database_access.searchStationLine(connection, stn, line)

    if res == []:
        flask.abort(404)

    stn, line = res[0]

    return flask.redirect(flask.url_for(
        'station', line=line, stn=stn,
        year="{:04d}".format(dt.year), month="{:02d}".format(dt.month),
        day="{:02d}".format(dt.day), time="{:02d}{:02d}".format(dt.hour,
                                                                dt.minute)))

@app.route("/")
def home():
    """Just station search page minus results for now."""
    return flask.render_template('search.html')

@app.route("/station/<line>/<stn>/<year>/<month>/<day>/<time>")
def station(line, stn, year, month, day, time):
    """List of trains arriving/departing a given station around time"""
    if len(time) != 4:
        flask.abort(400)
    try:
        hour = int(time[0:2])
        minute = int(time[2:4])
        syear = year
        year = int(year)
        smonth = month
        month = int(month)
        sday = day
        day = int(day)
        dt = datetime.datetime(year=year, month=month, day=day, hour=hour,
                               minute=minute)
        stationName = database_access.getStationNameById(connection,
                                                         stn)[0][0]
    except:
        traceback.print_exc()
        flask.abort(400)
    realRes = database_access.findTrainArrDepObjectsNoIds(connection, stn,
                                                          dt, line)
    timetableRes = database_access.findTimetableEntriesNoIds(connection,
                                                             stn, dt, line)
    realRes = list(realRes)
    timetableRes = list(timetableRes)
    results = []
    # Add all trains in the real arrivals/departures
    for train in realRes:
        tt = filter(lambda t: t["setNo"] == train["setNo"]
                    and t["tripNo"] == train["tripNo"], timetableRes)
        tt = list(tt)
        if tt != []: # if it's timetabled, add scheduled times
            train["sArrTime"] = tt[0]["sArrTime"]
            train["sDepTime"] = tt[0]["sDepTime"]
            train["osArrTime"] = tt[0]["osArrTime"]
            train["osDepTime"] = tt[0]["osDepTime"]
        train["url"] = "/train/{}/{}/{}/{}/{}/{}/{}".format(
            line, train["setNo"], train["tripNo"], syear, smonth, sday, time)
        results.append(train)
    for train in timetableRes:
        tt = filter(lambda t: t["setNo"] == train["setNo"]
                    and t["tripNo"] == train["tripNo"], results)
        if list(tt) == []:
            # Train has probably not left yet. But we'll check.
            t = database_access.findTrainArrDepObjectDate(
                connection, train["setNo"], train["tripNo"], stn, dt, line)
            if t != []:
                train["lcid"] = t[0][2]
                train["oaArrTime"] = t[0][0]
                train["oaDepTime"] = t[0][1]
                train["aArrTime"] = t[0][0].strftime("%H%M")
                train["aDepTime"] = t[0][1].strftime("%H%M")
            train["url"] = "/train/{}/{}/{}/{}/{}/{}/{}".format(
                line, train["setNo"], train["tripNo"], syear, smonth, sday,
                time)
            results.append(train)
    results = sorted(results,
                     key=lambda x: (x["oaDepTime"], x["oaArrTime"]) if
                     "aDepTime" in x else (x["osDepTime"], x["osArrTime"]))
    return flask.render_template(
        'station.html', stationName=stationName, results=results,
        station=stn, line=line, date="new Date({}, {}, {}, {}, {})".format(
            year, month - 1, day, hour, minute)) # month 0-indexed. Wat.

@app.route("/train/<line>/<setNo>/<tripNo>/<year>/<month>/<day>/<time>")
def trainView(line, setNo, tripNo, year, month, day, time):
    """Timetable (scheduled and actual) of given train."""
    if len(time) != 4:
        flask.abort(400)
    try:
        hour = int(time[0:2])
        minute = int(time[2:4])
        syear = year
        year = int(year)
        smonth = month
        month = int(month)
        sday = day
        day = int(day)
        dt = datetime.datetime(year=year, month=month, day=day, hour=hour,
                               minute=minute)
        lineName = database_access.getLineNameById(connection, line)[0][0]
    except:
        traceback.print_exc()
        flask.abort(400)
    realRes = database_access.findTrainArrDepObjectNoStn(connection, setNo,
                                                         tripNo, dt, line)
    timetableRes = database_access.findTimetableEntriesNoStn(connection, setNo,
                                                             tripNo, dt, line)
    realRes = list(realRes)
    timetableRes = list(timetableRes)
    # Grab the details from the actual running (if possible). This is more
    # likely to be up to date. Grab it from the LAST entry for this reason too
    if realRes != []:
        lcid = realRes[-1]["lcid"]
        destination = realRes[-1]["destination"]
        destCode = realRes[-1]["destCode"]
    else:
        lcid = None
        destination = timetableRes[-1]["destination"]
        destCode = timetableRes[-1]["destCode"]
    # Sanity check things. No good displaying data for a completely different
    # train, after all...
    realRes = list(filter(lambda x: x["lcid"] == lcid and
                          x["destination"] == destination and
                          x["destCode"] == destCode, realRes))
    timetableRes = list(filter(lambda x: x["destination"] == destination and
                               x["destCode"] == destCode, timetableRes))
    # Now we have data as close as can be expected to sanity. So we combine it.
    results = []
    for train in realRes:
        tt = filter(lambda t: t["stationCode"] == train["stationCode"],
                    timetableRes)
        tt = list(tt)
        if tt != []: # if it's timetabled, add scheduled times
            train["sArrTime"] = tt[0]["sArrTime"]
            train["sDepTime"] = tt[0]["sDepTime"]
            train["osArrTime"] = tt[0]["osArrTime"]
            train["osDepTime"] = tt[0]["osDepTime"]
            train["url"] = "/station/{}/{}/{}/{}/{}/{}".format(
                line, train["stationCode"], syear, smonth, sday,
                train["sDepTime"])
        else:
            train["url"] = "/station/{}/{}/{}/{}/{}/{}".format(
                line, train["stationCode"], syear, smonth, sday,
                train["aDepTime"])
        results.append(train)
    for train in timetableRes:
        tt = filter(lambda t: t["stationCode"] == train["stationCode"],
                    results)
        if list(tt) == []:
            train["url"] = "/station/{}/{}/{}/{}/{}/{}".format(
                line, train["stationCode"], syear, smonth, sday,
                train["sDepTime"])
            results.append(train)
    results = sorted(results, key=lambda x:
                     (x["oaDepTime"], x["oaArrTime"]) if "aDepTime" in x
                     else (x["osDepTime"], x["osArrTime"]))
    return flask.render_template(
        'train.html', setNo=setNo, tripNo=tripNo, results=results,
        line=lineName, lcid=lcid, destination=destination, destCode=destCode)

app.run(host='0.0.0.0', port=7711, debug=True)
