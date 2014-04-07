import unittest
from basicproperty import boundary, basic, xmlencoder

class TestClass( object ):
	simple = basic.BasicProperty(
		"simple", "documentation"
	)
	withBound = basic.BasicProperty(
		"withBound", "documentation",
		bounds=( boundary.TypeBoundary(str),)
	)
	withDefaultValue = basic.BasicProperty(
		"withDefaultValue", "documentation",
		defaultValue = 'this',
	)
	withDefaultFunction = basic.BasicProperty(
		"withDefaultFunction", "documentation",
		defaultFunction = lambda x,y: [],
	)
	withDefaultValueNoSet = basic.BasicProperty(
		"withDefaultValueNoSet", "documentation",
		defaultValue = 'this',
		setDefaultOnGet = 0,
	)
	withDefaultFunctionNoSet = basic.BasicProperty(
		"withDefaultFunctionNoSet", "documentation",
		defaultFunction = lambda x,y: [],
		setDefaultOnGet = 0,
	)
class TestClass2( object ):
	simple = basic.MethodStoreProperty(
		"simple", "documentation",
		getMethod = "doGet",
		setMethod = "doSet",
		delMethod = "doDel",
	)
	def doGet( self, ):
		return self.value
	def doSet( self, value ):
		self.value = value
	def doDel( self):
		del self.value

storage = xmlencoder.Storage()

class XMLTest( unittest.TestCase ):
	def testString( self ):
		"""Test simple encoding of string values"""
		encoder = xmlencoder.StringEncoder()
		result = encoder("this", storage)
		expected = xmlencoder.Tag( name = "str", attributes = {"enc":"utf-8"}, content = ["this"])
		assert result == expected,"""String encoding:\n\tWanted %r\n\tGot %r"""%(expected, result)
	def testRepresentation (self):
		"""Test representation of a tag object"""
		result = repr(xmlencoder.Tag( name = "str", attributes = {"enc":"utf-8"}, content = ["this"]))
		print result
		

if __name__ == "__main__":
	unittest.main()
	