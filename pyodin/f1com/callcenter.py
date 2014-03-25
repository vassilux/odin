#
# Call Center module , this module is a helper for the F1Com worker.
# 
#
'''
This is the a dialplan example
[incomming-calls-for-queue]
exten = _X.,1,NoOp(incomming-calls-for-queue)
same => n,Answer
same => n,UserEvent(incommingcall,Context:from-white-house, channel: ${CHANNEL}, extention:${EXTEN},calleridnum:${CALLERID(num)},calleridname:${CALLERID(name)},uniqueid: ${CDR(uniqueid)})
same => n,Goto(queues,6500,1)
same => n,Hangup()

Pay a little attention for include into you dialplan UserEvent like this one and send an incomming call to the queue
'''
import os
import sys
import re
import time
import logging
import optparse
import signal
import json
import sys, warnings
import struct
import logging
from commons import BasicObject, BasicObjectEncoder, OdinConfigParser, AsteriskHelper



#logger initialized by main runner module
logger = logging.getLogger("odin_callcenter");
#
CC_INCALL_RING 				= '00'
CC_INCALL_OP_PHONE_RING 	= '01'
CC_INCALL_OP_TAKE_CALL 		= '02'
CC_INCALL_OP_HANGUP_CALL 	= '03'
CC_INCALL_OP_DIAL_PROCESS 	= '05' #Means the call in the transfering state (Dial) to the operator
CC_INCALL_HANGUP_CALL 		= '10'
#
CC_INFO_CODE_1ECOUT ='ECOUTE'
CC_INFO_CODE_INCOMM ='INCOMM'
CC_INFO_CODE_CALLCT ='CALLCT'

DUMPOBJECTS = False

class CallCenter(object):
	"""docstring for CallCenter"""
	def __init__(self, amiBridge):
		super(CallCenter, self).__init__()
		self._amiBridge     = amiBridge
		self._astHelper     = AsteriskHelper()
		self._incalls       = {}
	#
	def __send_callcenter_event(self, code, extention, callcenter, callref, caller, post=""):
	    '''
	    Send a callcenter message to F1COM clients for indicate the state if an incomming call
	    '''
	    logger.debug("CallCenter : __send_callcenter_message [ %s %s %s %s ]" % (extention, callcenter, callref, caller))
	    if self._amiBridge:
	        type     = "1"
	        pstn     = "1"
	        optional ="#SDA=" + extention
	        if post and len(post) > 0:
	            optional +="#POSTE=" + post
	        optional +="#IDCOMM=" + callref
	        optional +="#CALLCENTER=" + callcenter
	        optional +="#APPELANT=" + caller
	        optional += "#AT=F1#NOMENT=27"
	        self._amiBridge.send_alarm_event(type, code, pstn, optional)
	    else:
	        logger.error("CallCenter : CallCenter event can't be send to F1COM clients.")
	    

	def new_call(self, data):
		uniqueid = data['event']['uniqueid']
		logger.debug("CallCenter : CallCenter create a new call for uniqueid [%s] " % (uniqueid))
		callref = self._astHelper.add_uniqueid(uniqueid)
		code = CC_INFO_CODE_1ECOUT
		extention = data['event']['extention']
		callcenter = CC_INCALL_RING
		caller = data['event']['calleridnum']
		newcall = BasicObject('InCall')
		newcall.callref = callref
		newcall.extention = extention
		newcall.caller = caller
		newcall.post =''
		newcall.uniqueid = uniqueid
		newcall.bridgeduniqueid = ''
		newcall.channel = data['event']['channel']
		self._incalls[uniqueid] = newcall
		self.__send_callcenter_event(code, extention, callcenter, callref, caller)
		logger.debug("CallCenter : New call created for uniqueid [%s] extention [%s] caller [%s]" % (uniqueid, extention, caller))
		if DUMPOBJECTS:
			logger.debug("CallCenter : new call :%s", newcall)

	def udpate_call_from_channel(self,channel):
		for i in self._incalls.keys():
			incall = self._incalls[i]
			if incall.bridgeduniqueid == channel.uniqueid:
				if channel.state == 'Ringing':
					#send the notification that an operator post ringing
					callcenter = CC_INCALL_OP_PHONE_RING
					code = CC_INFO_CODE_INCOMM
					extention = incall.extention
					callref = incall.callref
					caller = incall.caller
					post = incall.bridgecalleridnum
					self.__send_callcenter_event(code, extention, callcenter, callref, caller, post)
					logger.debug("CallCenter : update_call_from_channel F1Client for uniqueid [%s] operator phone ringing " % (incall.uniqueid))
					if DUMPOBJECTS:
						logger.debug("CallCenter : Call update from channel :%s", incall)


	def update_call_from_bridge(self, bridge):
		uniqueid = bridge.uniqueid
		bridgeduniqueid = bridge.bridgeduniqueid
		status = bridge.status
		logger.debug("CallCenter : update_call_from_bridge for uniqueid [%s] and bridgeduniqueid [%s] and status [%s]" % (uniqueid, bridgeduniqueid, status))
		
		if self._incalls.has_key(uniqueid):
			callcenter 	= None
			code 		= None
			incall = self._incalls[uniqueid]
			incall.bridgeduniqueid = bridgeduniqueid
			incall.post = bridge.bridgecalleridnum
			incall.bridgedchannel = bridge.bridgedchannel
			if status == 'Dial':
				callcenter = CC_INCALL_OP_DIAL_PROCESS
				code = CC_INFO_CODE_CALLCT
			elif status == 'Link':
				callcenter = CC_INCALL_OP_TAKE_CALL
				code = CC_INFO_CODE_CALLCT
			#
			if code and callcenter > 0:		
				post = None
				if incall.post :
					post = incall.post		
				extention = incall.extention
				callref = incall.callref
				caller = bridge.calleridnum
				self.__send_callcenter_event(code, extention, callcenter, callref, caller, post)
				logger.debug("CallCenter : update_call_from_bridge F1Client notified for code [%s] and extention [%s] and callcenter [%s]" % (code, extention, callcenter))
			#
			if DUMPOBJECTS:
				logger.debug("Call update_call_from_bridge :%s", incall)
		else:
			logger.debug("CallCenter : Can't update_call_from_bridge for uniqueid [%s] and bridgeduniqueid [%s]" % (uniqueid, bridgeduniqueid))

	def remove_call(self, bridge):
		'''
		Remove an incomming call from the conencted (bridged) call
		'''
		uniqueid = bridge.uniqueid
		logger.debug("CallCenter : Removing an incall for [%s]." % (uniqueid))
		if self._incalls.has_key(uniqueid):
			incall = self._incalls[uniqueid]
			code = CC_INFO_CODE_CALLCT
			extention = incall.extention
			post = bridge.bridgecalleridnum
			callcenter = CC_INCALL_HANGUP_CALL
			callref = incall.callref
			caller = bridge.calleridnum
			self.__send_callcenter_event(code, extention, callcenter, callref, caller, post)
			if DUMPOBJECTS:
				logger.debug("CallCenter : Remove call :%s", incall)
			#remove the call references
			self._astHelper.remove_callref_by_uniqueid(uniqueid)
			del self._incalls[uniqueid]
			logger.debug("CallCenter : CallCenter the incall removed for uniqueid [%s]." % (uniqueid))
		else:
			logger.info("CallCenter : CallCenter can't find incall for uniqueid [%s]." % (uniqueid))

	def __look_for_call_by_callref(self, callref):
		incall = None
		for i in self._incalls.keys():
			tmp = self._incalls[i]
			if tmp.callref == callref:
				incall = tmp
				break

		return incall

	def commut_call(self, internal, callref):
		''' 
		Try to find an incomming call and in the success to execute transffer to the internal given number 
		Please see the asterisk dialplan 
		'''
		done = False
		logger.debug("CallCenter : CallCenter try to find callref [%s]."%(callref))
		incall = self.__look_for_call_by_callref(callref)
		if incall:
			logger.debug("CallCenter : CallCenter find callref %s and send commut to the internal [%s]."%(callref, internal))
			done = True
			#try execute transferring 
			self._amiBridge.transffer_call(incall.channel, internal)
		else:
			logger.debug("CallCenter : CallCenter can't find callref %s and send commut to the internal [%s]." % (callref, internal))
		#check and log if the callref doen't find
		if not done :
			logger.debug("CallCenter : CallCenter can't find callref %s and send commut to the internal [%s].", 
				callref, internal)
		#return the search result
		return done

	def check_and_remove_call(self, uniqueid):
		call = self.__get_call_by_uniqueid(uniqueid)
		if call:
			code = CC_INFO_CODE_CALLCT
			extention = call.extention
			post = call.post
			callcenter = CC_INCALL_HANGUP_CALL
			callref = call.callref
			caller = call.caller
			self.__send_callcenter_event(code, extention, callcenter, callref, caller, post)
			if DUMPOBJECTS:
				logger.debug("CallCenter : Check and remove a call :%s", incall)
			#remove the call references
			self._astHelper.remove_callref_by_uniqueid(uniqueid)
			del self._incalls[uniqueid]
			logger.debug("CallCenter : Check and remove the incall removed for uniqueid [%s]." % (uniqueid))


	def get_channel_by_callref(self, callref):
		'''
		Look for a channel in the incomming calls by callref 
		Return the originate channel for the call otherwise None
		'''
		logger.debug("CallCenter : Look for a channel by callref [%s] ", callref)	
		channel = None
		incall = self.__look_for_call_by_callref(callref)
		if incall:
			channel = incall.channel
			logger.debug("CallCenter : Channel [%s] find for the callref [%s]", channel, callref)
			if DUMPOBJECTS:
				logger.debug("CallCenter : Find the call %s by callref %s", incall, callref)
		else:
			logger.debug("CallCenter : Can't find a channel for the callref [%s]", callref)
		return channel

	def __get_call_by_uniqueid(self, uniqueid):
		'''
		Look for an incomming call by uniqueid 
		'''
		call = None
		for i in self._incalls.keys():
			incall = self._incalls[i]
			if incall.uniqueid == uniqueid:
				call = incall
				break

		return call

			
