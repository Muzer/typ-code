#!/usr/bin/env python3

import flask
import database_access
import datetime

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
    except:
        flask.abort(400)
    results = database_access.findTrainArrDepObjectsNoIds(connection, station,
        datetime.datetime(year=year, month=month, day=day, hour=hour,
          minute=minute), line)
    return flask.render_template('station.html', station=station,
        results=results)

app.run(host='0.0.0.0', debug=True)
