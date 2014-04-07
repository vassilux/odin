import unittest
from wxPython.wx import *
from basicproperty import common, basic
from basicproperty.ext import wxtypes
from basictypes.wxtypes import pen as pen_module

class TestClass( object ):
	col = wxtypes.ColourProperty(
		"col", "Colour property",
	)
	pen = wxtypes.PenProperty(
		"pen", "Pen property",
	)

	penStyle = basic.BasicProperty(
		"penStyle", "Pen style property",
		baseType = pen_module.PenStyle,
	)
	penCap = basic.BasicProperty(
		"penCap", "Pen cap property",
		baseType = pen_module.PenCap,
	)
	penJoin = basic.BasicProperty(
		"penJoin", "Pen Join property",
		baseType = pen_module.PenJoin,
	)

DATATABLE = [ # attribute, testTable, badValues
	('col', [
		(
			wxColour( 0,0,0),
			[
				'#000000',
				'#0',
				'black',
				(0,0,0),
			],
		),
	], [ # (bad value, error expected)
		("a", ValueError),
		((0,0,0,0), TypeError),
		
	]),
	("pen", [
		(
			wxtypes.PenProperty.baseType( "BLACK", 1, wxSOLID),
			[
				wxPen( "BLACK", 1, wxSOLID),
				( "BLACK", 1, wxSOLID),
				( "BLACK", 1, wxtypes.wxPenStyleProperty.baseType("wxSOLID")),
				( "BLACK", 1, wxtypes.wxPenStyleProperty.baseType(wxSOLID)),
				( ),
				( "BLACK", 1),
				( "BLACK",),
				[ ],
				{ 'colour':'#000000', 'style':wxSOLID},
			],
		),
	], [ # (bad value, error expected)
	]),
	("penStyle", [
		(
			wxSOLID ,
			[
				wxSOLID,
				'wxSOLID',
				' wxSOLID ',
			],
		),
	], [ # (bad value, error expected)
		("a", ValueError),
		(None, ValueError),
		("wxJOIN_BEVEL", ValueError),
		(wxJOIN_BEVEL, ValueError),
	]),
	("penCap", [
		(
			wxCAP_BUTT,
			[
				wxCAP_BUTT,
				'wxCAP_BUTT',
				' wxCAP_BUTT ',
			],
		),
	], [ # (bad value, error expected)
		("wxSOLID", ValueError),
	]),
	("penJoin", [
		(
			wxJOIN_BEVEL,
			[
				wxJOIN_BEVEL,
				'wxJOIN_BEVEL',
				' wxJOIN_BEVEL ',
			],
		),
	], [ # (bad value, error expected)
		("wxSOLID", ValueError),
	]),
		
]
		

class PropertyTest( unittest.TestCase ):
	def testCoerce( self ):
		"""Test the whole DATATABLE set for coercion"""
		object = TestClass()
		for attribute, table, bad in DATATABLE:
			for value, set in table:
				for v in set:
					setattr( object, attribute, v)
					got = getattr( object, attribute )
					assert got == value, """COERCE(%s):\n  source:%r\n  expected: %r\n  got: %r"""%( attribute, v, value, got)
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
	class TestApp( wxPySimpleApp ):
		def OnInit( self ):
			frame = wxFrame( None, -1, "Some frame")
			self.SetTopWindow( frame )
			unittest.main()
			frame.Close()
	app = TestApp()
	app.MainLoop()
	
