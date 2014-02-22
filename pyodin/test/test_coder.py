import os
import sys
import unittest

from commons import AsteriskHelper

class AsteriskHelperCase(unittest.TestCase):

	def test_callref(self):
		coder = AsteriskHelper()
		uniqueid="1372690610.14545"
		callref = coder.add_uniqueid(uniqueid)
		count = coder.get_callrefs_count()
		self.assertEqual(count, 1)
		hasUniqueid  = coder.has_uniqueid(uniqueid)
		self.assertEqual(hasUniqueid, True)
		coder.remove_callref_by_uniqueid(uniqueid)
		count = coder.get_callrefs_count()
		self.assertEqual(count, 0)
		hasUniqueid  = coder.has_uniqueid(uniqueid)
		self.assertEqual(hasUniqueid, False)
		callref = coder.add_uniqueid(uniqueid)
		count = coder.get_callrefs_count()
		self.assertEqual(count, 1)
		coder.remove_callref(callref)
		count = coder.get_callrefs_count()
		self.assertEqual(count, 0)
	
	def test_uniqueid(self):
		uniqueid="1372690610.14545"
		#uniqueid="137269.14545"
		coder = AsteriskHelper()
		encoded = coder.encode_call_unique_id(uniqueid)
		print("encoded : %s " % (encoded))
		decoded = coder.decode_call_unique_id(encoded)
		print("dencoded : %s " % (encoded))
		self.assertEqual(uniqueid, decoded)

	def test_get_number_from_channel(self):
		coder = AsteriskHelper()
		number = coder.get_number_from_channel("Parked/SIP/6000-5645645")
		self.assertEqual(number, '6000')
		number = coder.get_number_from_channel("IAX/6006-5645645")
		self.assertEqual(number, '6006')


