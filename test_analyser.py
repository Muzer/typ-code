#!/usr/bin/env python3
import unittest
import timetable_analyser
import station
import datetime

class TestCalculateTrainArrDep(unittest.TestCase):
    def testEmptyCase(self):
        prev = []
        train = station.Train(
            "", "", "", 25, "", "", "", "", "", datetime.datetime(
                year=2015, month=4, day=1, hour=10, minute=30, second=44))
        arrTime, depTime = timetable_analyser.calculateTrainArrDepFromPrev(
                prev, train)
        self.assertEqual(arrTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=9))
        self.assertEqual(depTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=29))
    def testAtStationEarlyArr(self):
        prev = [(datetime.datetime(year=2015, month=4, day=1, hour=10,
                                   minute=31, second=8), datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=28)), ""]
        train = station.Train(
            "", "", "", 0, "", "", "", "", "", datetime.datetime(
                year=2015, month=4, day=1, hour=10, minute=29, second=23))
        arrTime, depTime = timetable_analyser.calculateTrainArrDepFromPrev(
                prev, train)
        self.assertEqual(arrTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=29, second=23))
        self.assertEqual(depTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=28))
    def testAtStationLateDep(self):
        prev = [(datetime.datetime(year=2015, month=4, day=1, hour=10,
                                   minute=31, second=8), datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=28)), ""]
        train = station.Train(
            "", "", "", 0, "", "", "", "", "", datetime.datetime(
                year=2015, month=4, day=1, hour=10, minute=31, second=43))
        arrTime, depTime = timetable_analyser.calculateTrainArrDepFromPrev(
                prev, train)
        self.assertEqual(arrTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=8))
        self.assertEqual(depTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=43))
    def testAtStationNoViolations(self):
        prev = [(datetime.datetime(year=2015, month=4, day=1, hour=10,
                                   minute=31, second=8), datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=28)), ""]
        train = station.Train(
            "", "", "", 0, "", "", "", "", "", datetime.datetime(
                year=2015, month=4, day=1, hour=10, minute=31, second=20))
        arrTime, depTime = timetable_analyser.calculateTrainArrDepFromPrev(
                prev, train)
        self.assertEqual(arrTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=8))
        self.assertEqual(depTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=28))
    def testExistingNotAtStation(self):
        prev = [(datetime.datetime(year=2015, month=4, day=1, hour=10,
                                   minute=31, second=8), datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=28)), ""]
        train = station.Train(
            "", "", "", 7, "", "", "", "", "", datetime.datetime(
                year=2015, month=4, day=1, hour=10, minute=31, second=0))
        arrTime, depTime = timetable_analyser.calculateTrainArrDepFromPrev(
                prev, train)
        self.assertEqual(arrTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=7))
        self.assertEqual(depTime, datetime.datetime(
            year=2015, month=4, day=1, hour=10, minute=31, second=27))

class TestTimeWrangling(unittest.TestCase):
    def testGetSeconds(self):
        time = datetime.time(hour=13, minute=34, second=8)
        sec = timetable_analyser.getSeconds(time)
        self.assertEqual(sec, 48848)
    def testGetTime(self):
        time = timetable_analyser.getTime(48848)
        self.assertEqual(time, datetime.time(hour=13, minute=34, second=8))

class TestMedianMode(unittest.TestCase):
    def testMode(self):
        dictArr = [{"thing": "1"}, {"thing": "2"}, {"thing": "2"},
                   {"thing": "2"}, {"thing": "3"}, {"thing": "3"}]
        mode = timetable_analyser.mode(dictArr, "thing")
        self.assertEqual(mode, "2")
        dictArr = [{"thing": "3", "otherThing": "4"}]
        mode = timetable_analyser.mode(dictArr, "otherThing")
        self.assertEqual(mode, "4")
    def testEmptyMedian(self):
        dictArr = []
        median = timetable_analyser.median(dictArr, "time")
        self.assertIsNone(median)
    def testOddMedian(self):
        dictArr = [{"time": datetime.datetime(
            year=2015, month=4, day=1, hour=12, minute=00, second=00)},
            {"time": datetime.datetime(year=2015, month=3, day=30, hour=11,
                                       minute=25, second=20)},
            {"time": datetime.datetime(year=2015, month=4, day=2, hour=11,
                                       minute=0, second=0)}]
        median = timetable_analyser.median(dictArr, "time")
        self.assertEqual(median, datetime.time(hour=11, minute=25, second=20))
    def testEvenMedian(self):
        dictArr = [{"time": datetime.datetime(
            year=2015, month=4, day=1, hour=12, minute=00, second=00)},
            {"time": datetime.datetime(year=2015, month=3, day=30, hour=11,
                                       minute=25, second=20)},
            {"time": datetime.datetime(year=2015, month=4, day=30, hour=11,
                                       minute=25, second=22)},
            {"time": datetime.datetime(year=2015, month=4, day=2, hour=11,
                                       minute=0, second=0)}]
        median = timetable_analyser.median(dictArr, "time")
        self.assertEqual(median, datetime.time(hour=11, minute=25, second=21))

class TestArrDepMedian(unittest.TestCase):
    def testEmptyList(self):
        results = []
        arr, dep, dest, dCode, platNo = \
            timetable_analyser.calculateMedianFromTrainArrDeps(results, 0, 5)
        self.assertIsNone(arr)
        self.assertIsNone(dep)
        self.assertIsNone(dest)
        self.assertIsNone(dCode)
        self.assertIsNone(platNo)
    def testSaturday(self):
        results = [(datetime.datetime(year=2015, month=4, day=1, hour=12,
                                      minute=0, second=0),
                    datetime.datetime(year=2015, month=4, day=1, hour=12,
                                      minute=0, second=20), "A", "B", "C"),
                   (datetime.datetime(year=2015, month=4, day=4, hour=13,
                                      minute=0, second=0),
                    datetime.datetime(year=2015, month=4, day=4, hour=13,
                                      minute=0, second=20), "D", "E", "F")]
        arr, dep, dest, dCode, platNo = \
            timetable_analyser.calculateMedianFromTrainArrDeps(results, 5, 6)
        self.assertEqual(arr, datetime.time(hour=13, minute=0, second=0))
        self.assertEqual(dep, datetime.time(hour=13, minute=0, second=20))
        self.assertEqual(dest, "D")
        self.assertEqual(dCode, "E")
        self.assertEqual(platNo, "F")
    def testMedians(self):
        results = [(datetime.datetime(year=2015, month=4, day=1, hour=12,
                                      minute=0, second=0),
                    datetime.datetime(year=2015, month=4, day=1, hour=12,
                                      minute=0, second=20), "A", "B", "C"),
                   (datetime.datetime(year=2015, month=4, day=2, hour=13,
                                      minute=0, second=0),
                    datetime.datetime(year=2015, month=4, day=2, hour=13,
                                      minute=0, second=20), "D", "E", "F"),
                   (datetime.datetime(year=2015, month=4, day=3, hour=14,
                                      minute=0, second=0),
                    datetime.datetime(year=2015, month=4, day=3, hour=14,
                                      minute=0, second=20), "D", "E", "F")]
        arr, dep, dest, dCode, platNo = \
            timetable_analyser.calculateMedianFromTrainArrDeps(results, 0, 5)
        self.assertEqual(arr, datetime.time(hour=13, minute=0, second=0))
        self.assertEqual(dep, datetime.time(hour=13, minute=0, second=20))
        self.assertEqual(dest, "D")
        self.assertEqual(dCode, "E")
        self.assertEqual(platNo, "F")

if __name__ == '__main__':
    unittest.main()
