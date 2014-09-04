delimiter $$

CREATE TABLE `Historique` (
  `NoTrans` varchar(30) DEFAULT NULL,
  `Start` varchar(19) DEFAULT NULL,
  `Stop` varchar(20) DEFAULT NULL,
  `FileName` varchar(50) DEFAULT NULL,
  `StartLong` int(11) DEFAULT NULL,
  `Duration` varchar(20) DEFAULT NULL,
  `CallerID` varchar(20) DEFAULT NULL,
  `SDA` varchar(10) DEFAULT NULL,
  `F1` varchar(30) DEFAULT NULL,
  `XISDN` int(11) DEFAULT NULL,
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`ID`)
) ENGINE=MyISAM AUTO_INCREMENT=546 DEFAULT CHARSET=latin1$$

CREATE
DEFINER=`root`@`%`
TRIGGER `rc1`.`timestampinserter`
BEFORE INSERT ON `rc1`.`Historique`
FOR EACH ROW
SET NEW.Start = DATE_FORMAT(NEW.Start, '%d/%m/%Y %H:%i:%s')
$$

CREATE
DEFINER=`root`@`%`
TRIGGER `rc1`.`timestampper`
BEFORE UPDATE ON `rc1`.`Historique`
FOR EACH ROW
SET NEW.Stop = DATE_FORMAT(NEW.Stop, '%d/%m/%Y %H:%i:%s')
$$

CREATE TABLE `settings` (
  `id` int(11) NOT NULL,
  `variable` varchar(45) DEFAULT NULL,
  `value` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1$$

CREATE TABLE `recordNumbers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `number` varchar(45) DEFAULT NULL,
  `comments` varchar(120) DEFAULT NULL,
  `recorded` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=latin1 COMMENT='DID or external numbers'$$


INSERT INTO `rc1`.`settings`
(`variable`, `value`) VALUES ('RECORD_ALL','False');$$






