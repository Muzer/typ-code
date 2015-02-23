#!/usr/bin/env python3

import database_access
import timetable_analyser

connection = database_access.connectToDb()
print(timetable_analyser.calculate_median(connection, 'OXC', '230', '13', 'V', 0, 5))
