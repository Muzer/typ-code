#!/usr/bin/env python3

import flask
import database_access
import datetime
import traceback

app = flask.Flask(__name__)
connection = database_access.connectToDb()

@app.route("/station/search")
def search():
    station = flask.request.args['station']
    dt = flask.request.args['datetime']
    try:
        dt = datetime.datetime.strptime(dt, "%d/%m/%Y %H:%M")
    except:
        flask.abort(400)
    line = flask.request.args['line']

    res = database_access.searchStationLine(connection, station, line)

    if res == []:
        flask.abort(404)

    station, line = res[0]

    return flask.redirect(flask.url_for('station', line=line, station=station,
      year="{:04d}".format(dt.year), month="{:02d}".format(dt.month),
      day="{:02d}".format(dt.day), time="{:02d}{:02d}".format(dt.hour,
        dt.minute)))

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
        dt = datetime.datetime(year=year, month=month, day=day, hour=hour,
            minute=minute)
        stationName = database_access.getStationNameById(connection,
            station)[0][0]
    except:
        traceback.print_exc()
        flask.abort(400)
    realRes = database_access.findTrainArrDepObjectsNoIds(connection, station,
        dt, line)
    timetableRes = database_access.findTimetableEntriesNoIds(connection,
        station, dt, line)
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
                train["setNo"], train["tripNo"], station, dt, line)
            if t != []:
                train["lcid"] = t[0][2]
                train["aArrTime"] = t[0][0]
                train["aDepTime"] = t[0][1]
            results.append(train)
    results = sorted(results,
        key=lambda x : (x["aDepTime"], x["aArrTime"]) if "aDepTime" in x \
            else (x["sDepTime"], x["sArrTime"]))
    return flask.render_template('station.html', stationName=stationName,
        results=results, station=station, line=line,
        date="new Date({}, {}, {}, {}, {})".format(year,
          month - 1, day, hour, minute)) # month 0-indexed. WTF, JavaScript?

app.run(host='0.0.0.0', port=7711, debug=True)
