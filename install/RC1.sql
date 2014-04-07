-- phpMyAdmin SQL Dump
-- version 3.3.7deb6
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Aug 10, 2011 at 09:52 AM
-- Server version: 5.1.57
-- PHP Version: 5.3.6-6~dotdeb.1

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `RC1`
--

-- --------------------------------------------------------

--
-- Table structure for table `Historique`
--

CREATE TABLE IF NOT EXISTS `Historique` (
  `NoTrans` varchar(30) DEFAULT NULL,
  `Start` datetime DEFAULT NULL,
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
) ENGINE=MyISAM  DEFAULT CHARSET=latin1 AUTO_INCREMENT=78 ;


