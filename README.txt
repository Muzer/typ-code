Designed for Python3

You will need lxml, Flask and the MySQL connector

Database setup instructions:

Create a MySQL database and user as usual

Use the following to create the tables required:

CREATE TABLE `stations` (
  `code` char(3) NOT NULL,
  `lineCode` char(1) NOT NULL,
  `name` varchar(30) DEFAULT NULL,
  `lineName` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`lineCode`,`code`),
  KEY `stations_index` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `platforms` (
  `number` varchar(3) NOT NULL,
  `name` varchar(30) DEFAULT NULL,
  `trackCode` varchar(10) DEFAULT NULL,
  `stationLineCode` char(1) NOT NULL,
  `stationCode` char(3) NOT NULL,
  PRIMARY KEY (`number`,`stationLineCode`,`stationCode`),
  KEY `stationLineCode` (`stationLineCode`),
  KEY `stationCode` (`stationCode`),
  CONSTRAINT `platforms_ibfk_1` FOREIGN KEY (`stationLineCode`) REFERENCES `stations` (`lineCode`),
  CONSTRAINT `platforms_ibfk_2` FOREIGN KEY (`stationCode`) REFERENCES `stations` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `trains` (
  `lcid` varchar(7) NOT NULL,
  `setNo` varchar(3) DEFAULT NULL,
  `tripNo` varchar(2) DEFAULT NULL,
  `secondsTo` int(11) DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `destination` varchar(60) DEFAULT NULL,
  `destCode` varchar(3) DEFAULT NULL,
  `trackCode` varchar(10) DEFAULT NULL,
  `ln` varchar(1) DEFAULT NULL,
  `whenCreated` datetime DEFAULT NULL,
  `stationCode` char(3) NOT NULL,
  `stationLineCode` char(1) NOT NULL,
  `platformNumber` varchar(3) NOT NULL,
  KEY `stationLineCode` (`stationLineCode`),
  KEY `stationCode` (`stationCode`),
  KEY `platformNumber` (`platformNumber`),
  CONSTRAINT `trains_ibfk_1` FOREIGN KEY (`stationLineCode`) REFERENCES `platforms` (`stationLineCode`),
  CONSTRAINT `trains_ibfk_2` FOREIGN KEY (`stationCode`) REFERENCES `platforms` (`stationCode`),
  CONSTRAINT `trains_ibfk_3` FOREIGN KEY (`platformNumber`) REFERENCES `platforms` (`number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `trainsArrDep` (
  `lcid` varchar(7) NOT NULL,
  `setNo` varchar(3) NOT NULL,
  `tripNo` varchar(2) NOT NULL,
  `destination` varchar(60) NOT NULL,
  `destCode` varchar(3) NOT NULL,
  `ln` varchar(1) NOT NULL,
  `stationCode` char(3) NOT NULL,
  `stationLineCode` char(1) NOT NULL,
  `platformNumber` varchar(3) NOT NULL,
  `arrTime` datetime NOT NULL,
  `depTime` datetime NOT NULL,
  KEY `dateidx` (`arrTime`)
  KEY `stationLineCode` (`stationLineCode`),
  KEY `stationCode` (`stationCode`),
  KEY `platformNumber` (`platformNumber`),
  CONSTRAINT `trainsArrDep_ibfk_1` FOREIGN KEY (`stationLineCode`) REFERENCES `platforms` (`stationLineCode`),
  CONSTRAINT `trainsArrDep_ibfk_2` FOREIGN KEY (`stationCode`) REFERENCES `platforms` (`stationCode`),
  CONSTRAINT `trainsArrDep_ibfk_3` FOREIGN KEY (`platformNumber`) REFERENCES `platforms` (`number`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8

CREATE TABLE `timetables` (
  `setNo` varchar(3) NOT NULL,
  `tripNo` varchar(2) NOT NULL,
  `destination` varchar(60) NOT NULL,
  `destCode` varchar(3) NOT NULL,
  `stationCode` char(3) NOT NULL,
  `stationLineCode` char(1) NOT NULL,
  `platformNumber` varchar(3) NOT NULL,
  `arrTime` time NOT NULL,
  `depTime` time NOT NULL,
  `dateCreated` date NOT NULL,
  `daysOfWeek` char(1) NOT NULL
  KEY `stationLineCode` (`stationLineCode`),
  KEY `stationCode` (`stationCode`),
  KEY `platformNumber` (`platformNumber`),
  CONSTRAINT `timetables_ibfk_1` FOREIGN KEY (`stationLineCode`) REFERENCES `platforms` (`stationLineCode`),
  CONSTRAINT `timetables_ibfk_2` FOREIGN KEY (`stationCode`) REFERENCES `platforms` (`stationCode`),
  CONSTRAINT `timetables_ibfk_3` FOREIGN KEY (`platformNumber`) REFERENCES `platforms` (`number`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8

(IN THAT ORDER)




data_logger should be left running continuously.

generate_wtt should be run occasionally to calculate the working timetable. It
should only be run after the data logger has been running for at least a few
weeks. You should update the date towards the top of the file if a new Working
Timetable comes out.

ui.py runs the server (in debug mode) for the web interface, on port 7711.
