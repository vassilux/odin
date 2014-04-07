#! /usr/bin/env python2.2
"""Test everything in one go"""
import unittest
def moduleSuite( module ):
	return unittest.TestLoader().loadTestsFromModule( module )

import test_basic
import test_boundary
import test_classbyname
import test_lists
import test_date
import test_factories

set = [
	test_basic,
	test_boundary,
	test_classbyname,
	test_lists,
	test_date,
	test_factories,
]

def buildSuite( ):
	suite = unittest.TestSuite( [
		moduleSuite( module )
		for module in set
	])
	return suite


if __name__ == "__main__":
	try:
		import wx
	except ImportError:
		unittest.TextTestRunner(verbosity=2).run( buildSuite() )
	else:
		class TestApp( wx.PySimpleApp ):
			def OnInit( self ):
				wx.InitAllImageHandlers()
				import test_wx
				set.append( test_wx )
				frame = wx.Frame( None, -1, "Some frame")
				self.SetTopWindow( frame )
				unittest.TextTestRunner(verbosity=2).run( buildSuite() )
				frame.Close()
				return False
		app = TestApp()
		app.MainLoop()
