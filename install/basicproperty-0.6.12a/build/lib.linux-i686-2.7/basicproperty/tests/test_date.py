import unittest, time
from basicproperty import common
from basictypes import date_types

class TestClass( object ):
	dt = common.DateTimeProperty(
		"dt", "documentation",
		defaultFunction = date_types.now
	)
	dtd = common.DateTimeDeltaProperty(
		"dtd", "documentation",
		defaultFunction = date_types.DateTimeDelta
	)
	tod = common.TimeOfDayProperty(
		"tod", "documentation",
		defaultFunction = date_types.TimeOfDay
	)

from mx.DateTime import RelativeDateTime
t1 = time.mktime((2003, 2, 23, 0, 0, 0, 0, 0, 0))

DATATABLE = [ # attribute, testTable, badValues
	('tod', [
		(
			RelativeDateTime( hour = 2, minute = 3, second = 0.5),
			[
				RelativeDateTime( hour = 2, minute = 3, second = 0.5),
				RelativeDateTime( months = 3, days = 30, hour = 2, minute = 3, second = 0.5),
				u"2:3:.5",
				u"02:03:0.5",
				u"2:3:.5am",
				(2,3,0,500),
				[2,3,0,500],
			],
		),
		(
			RelativeDateTime( hour = 14, minute = 0, second = 0),
			[
				RelativeDateTime( hour = 14, minute = 0, second = 0),
				RelativeDateTime( months = 3, days = 30, hour = 14, minute = 0, second = 0),
				u"14",
				u"14:0:0",
				u"14:00",
				u"14:00pm",
				u"2pm",
				u"2 PM",
				"14",
				(14,0,0),
				(14,),
				(14,0,0,0),
				14,
				14L,
				14.0,
			],
		),
		(
			RelativeDateTime( hour = 14, minute = 30, second=0),
			[
				14.5,
			],
		),
		(
			RelativeDateTime( hour = 0, minute = 30, second=0),
			[
				'24:30',
				'48:30',
			],
		),
		(
			RelativeDateTime( hour = 0, minute = 0, second=0),
			[
				'24:00',
				'12am',
				'0am',
			],
		),
		(
			RelativeDateTime( hour = 12, minute = 0, second=0),
			[
				'0pm',
				'12pm',
			],
		),
	], [ # (bad value, error expected)
		("a", ValueError),
		(None, TypeError),
		("am", ValueError),
	]),
	('dt', [
		(
			date_types.DateTime( "2003-02-23" ),
			[
				date_types.DateTime( "2003-02-23" ),
				'2003-02-23',
				u'2003-02-23',
				time.localtime(t1),
				t1,
			]
		),
		(
			date_types.DateTime( "02/23" ),
			[
				'Feb 23rd',
				'February 23',
				'02/23',
				'feb 23',
			]
		),
		(
			date_types.DateTime( "2003-02-23" ),
			[
				'Feb 23, 2003',
				'February 23, 2003',
				'Sunday February 23, 2003',
				'2003-02-23',
				'feb 23, 2003',
				'2003-02-23',
			]
		),
	], [ # (bad value, error expected)
##		("2", ValueError), # ambiguous, improper formatting
	]),
	('dtd', [
		(
			date_types.DateTimeDelta( 1, 2, 3, 4.0 ),
			[
				date_types.DateTimeDelta( 1, 2, 3, 4.0 ),
				"1 day, 2 hours, 3 minutes and 4 seconds",
				u"1 day, 2 hours, 3 minutes and 4 seconds",
				"1d2h3m4s",
			]
		),
		(
			- date_types.DateTimeDelta( 0, 2, 3, 4.0 ),
			[
				"-2:3:4.0",
				u"-2:3:4.0",
				"-2:3:4",
				(0, -2,-3,-4.0),
			]
		),
		(
			date_types.DateTimeDelta( 0, 2, 3, 4.0 ),
			[
				"2:3:4.0",
				u"2:3:4.0",
				"2:3:4",
				(0, 2,3,4.0),
			]
		),
		(
			date_types.DateTimeDelta( 0, 2, 3, 4.34 ),
			[
				"2:3:4.34",
				u"2:3:4.34",
				"2:3:4.34",
				(0, 2,3,4.34),
			]
		),
	], [ # (bad value, error expected)
	]),
]
if hasattr( common, 'DateTimeDTProperty' ):
	from basictypes import datedatetime_types as ddt
	TestClass.dt2 = common.DateTimeDTProperty(
		'dt2', """Tests the datetime implementation""",
	)
	DATATABLE.append( 
		('dt2', [
			(
				ddt.DateTime( "2003-02-23" ),
				[
					date_types.DateTime( "2003-02-23" ),
					'2003-02-23',
					u'2003-02-23',
					time.localtime(t1),
					t1,
				]
			),
			(
				date_types.DateTime( "02/23" ),
				[
					'Feb 23rd',
					'February 23',
					'02/23',
					'feb 23',
				]
			),
			(
				date_types.DateTime( "2003-02-23" ),
				[
					'Feb 23, 2003',
					'February 23, 2003',
					'Sunday February 23, 2003',
					'2003-02-23',
					'feb 23, 2003',
					'2003-02-23',
				]
			),
		], [ # (bad value, error expected)
	##		("2", ValueError), # ambiguous, improper formatting
		])
	)
		

class DTPropertyTest( unittest.TestCase ):
	def testCoerce( self ):
		"""Test the whole DATATABLE set for coercion"""
		object = TestClass()
		for attribute, table, bad in DATATABLE:
			for value, set in table:
				for v in set:
					setattr( object, attribute, v)
					got = getattr( object, attribute )
					assert got == value, """COERCE(%s): %r -> %r failed, got %r"""%( attribute, v, value, got)
						
			for value, err in bad:
				try:
					setattr(object, attribute, value)
				except err:
					continue
				except Exception, e:
					raise TypeError( """Wrong exc: set %(attribute)r to %(value)r\nExpected: %(err)s\nGot: %(e)s"""%(locals()))
				else:
					result = getattr( object, attribute)
					import pdb
					pdb.set_trace()
					setattr(object, attribute, value)
					raise TypeError( """No exc: set %(attribute)r to %(value)r\nExpected: %(err)r %(err)s\nValue:%(result)s"""%(locals()))
		
if __name__ == "__main__":
	unittest.main()
	
