import unittest
from basicproperty import common

class TestClass( object ):
	strings = common.StringsProperty(
		"strings", "documentation",
		defaultValue = ('this','that','those',u'32',32,None),
	)
	ints = common.IntegersProperty(
		"ints", "documentation",
		defaultValue = ('32',42.0,u'32',32),
	)
	floats = common.FloatsProperty(
		"floats", "documentation",
		defaultValue = ('32',42.4,u'32',32),
	)
	booleans = common.BooleansProperty(
		"booleans", "documentation",
		defaultValue = ('null',0.0,1.0,'2','0',()),
	)
	

class BasicPropertyTest( unittest.TestCase ):
	def testStandard( self ):
		"""Test standard get/set/del semantics"""
		object = TestClass()
		for attr,expected in [
			("strings",[u'this',u'that',u'those',u'32',u'32',u'']),
			('ints',[32,42,32,32]),
			('floats',[32.0,42.4,32.0,32.0]),
			('booleans',[0,0,1,1,0,0]),
		]:
			value = getattr(object, attr)
			assert value == expected, """Didn't get expected for %s:\ngot: %r\nexp: %r"""%(attr, value, expected)
	def testBad(self):
		object = TestClass()
		self.failUnlessRaises( TypeError, setattr, (object, 'ints', [ [32],[45]]) )
		self.failUnlessRaises( TypeError, setattr, (object, 'strings', [ [32],[45]]), )
		self.failUnlessRaises( TypeError, setattr, (object, 'floats', [ [32],[45]]), )
		self.failUnlessRaises( TypeError, setattr, (object, 'booleans', [ [32],[45]]), )
		
		

if __name__ == "__main__":
	unittest.main()
	