import os
import sys
import string
import random



CODER_DICTIONARY = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_`\"!$'()*,-"
UNIXTIME_2000    = 1370131200


def _encode_number(n):
	encoded = ''
	while n > 0:
		n, r = divmod(n, len(CODER_DICTIONARY))
		encoded = CODER_DICTIONARY[r] + encoded
	return encoded

def _decode_string(encoded):
	decoded = 0
	while len(encoded) > 0:
		decoded = decoded * len(CODER_DICTIONARY) + CODER_DICTIONARY.find(encoded[0])
		encoded = encoded[1:]
	return decoded

def callref_generator(size=7, chars=string.ascii_uppercase + string.digits):
	callref = '@'
	generated = ''.join(random.choice(chars) for x in range(size))
	callref += generated
	return callref

class  AsteriskHelper(object):
	"""
	Simpel helper class to boilerplate operations
	Encapsulate management of "callref" vs uniqueid
	Encode/Decode uniqueid
	"""
	def __init__(self):
		super(AsteriskHelper, self).__init__()
		self._callRefs = {}

	def encode_call_unique_id(self, uniqueid):
		'''
		Encode Asterisk channel uniqueid
		Uniqueid composed with a unixtime string and a sequence string
	    Uniqueid string splited into two numeric strings, encoded and build a new callref(F1 style)
	    callref string prefixed by @ 
		'''
		stringcalltime, stringseq = uniqueid.split('.',1)
		realcalltime = int(stringcalltime) - UNIXTIME_2000
		calltime = _encode_number(realcalltime)
		seq = _encode_number(int(stringseq))
		encoded = '@%s.%s' % (calltime,seq)
		return encoded

	def decode_call_unique_id(self, encoded):
		encoded = encoded[1:]
		stringcalltime, stringseq = encoded.split('.',1)
		calltime = _decode_string(stringcalltime)
		realcalltime = UNIXTIME_2000 + calltime
		seq = _decode_string(stringseq)
		decoded = '%s.%s' % (realcalltime,seq)
		return decoded

	def get_number_from_channel(self, channel):
	        number = channel[channel.rfind("/")+1: channel.find("-")]
	        return number

	def add_uniqueid(self, uniqueid):
		callref = callref_generator()
		self._callRefs[uniqueid] = callref
		return callref

	def remove_callref_by_uniqueid(self, uniqueid):
		if uniqueid in self._callRefs.keys():
			del self._callRefs[uniqueid]

	def remove_callref(self, callref):
		for uniqueid, cf in self._callRefs.items():
			if cf == callref:
				del self._callRefs[uniqueid]
				break

	def get_callrefs_count(self):
		return len(self._callRefs)

	def has_uniqueid(self, uniqueid):
		return self._callRefs.has_key(uniqueid)

	def get_callref(self, uniqueid):
		callref = ''
		if self._callRefs.has_key(uniqueid) :
			callref = self._callRefs[uniqueid]

		return callref

