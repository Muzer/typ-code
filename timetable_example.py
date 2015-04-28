#!/usr/bin/env python3
"""Calculate single timetable entry for example train at example station."""

import database_access
import timetable_analyser
import datetime

connection = database_access.connectToDb()
print(timetable_analyser.calculateMedian(
    connection,
    datetime.datetime(year=2015, month=3, day=8, hour=0, minute=0, second=0),
    'OXC', '230', '13', 'V', 0, 5))
