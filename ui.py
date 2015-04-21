#!/usr/bin/env python3

import flask
import database_access
import datetime
import traceback

app = flask.Flask(__name__)
connection = database_access.connectToDb()

@app.route("/station/<line>/<station>/<year>/<month>/<day>/<time>")
def station(line, station, year, month, day, time):
    if len(time) != 4:
        flask.abort(400)
    try:
        hour = int(time[0:2])
        minute = int(time[2:4])
        year = int(year)
        month = int(month)
        day = int(day)
        stationName = database_access.getStationNameById(connection,
            station)[0][0]
    except:
        traceback.print_exc()
        flask.abort(400)
    realRes = database_access.findTrainArrDepObjectsNoIds(connection, station,
        datetime.datetime(year=year, month=month, day=day, hour=hour,
          minute=minute), line)
    timetableRes = database_access.findTimetableEntriesNoIds(connection,
        station, datetime.datetime(year=year, month=month, day=day,
          hour=hour, minute=minute), line)
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
        results.append(train)
    for train in timetableRes:
        tt = filter(lambda t: t["setNo"] == train["setNo"]
            and t["tripNo"] == train["tripNo"], results)
        if list(tt) == []:
            # Train has probably not left yet. But we'll check.
            t = database_access.findTrainArrDepObjectDate(connection,
                train["setNo"], train["tripNo"], station,
                datetime.datetime(year=year, month=month, day=day, hour=hour,
                  minute=minute), line)
            if t != []:
                train["lcid"] = t[0][2]
                train["aArrTime"] = t[0][0]
                train["aDepTime"] = t[0][1]
            results.append(train)
    results = sorted(results,
        key=lambda x : (x["aDepTime"], x["aArrTime"]) if "aDepTime" in x \
            else (x["sDepTime"], x["sArrTime"]))
    return flask.render_template('station.html', station=stationName,
        results=results)

app.run(host='0.0.0.0', port=7711, debug=True)
