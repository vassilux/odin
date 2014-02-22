#!/bin/bash

# 
# Description : Deamonize server.js(the vor http server part)	
#				Please check the forever documentation for more information
#				Example :
#				 	List all run scripts : forever list
#					Start the server : forever start server.js	
#					Stop the server : forever stop server.js		
#					Restart the server : forever restart server.js				
# Author : vassilux
# Last modified : 2014-02-20 16:37:47 
#

SERVERLOG_DIRECTORY=/opt/odin/server/logs
LOG_OPTONS="-o ${SERVERLOG_DIRECTORY}/server_out.log -l ${SERVERLOG_DIRECTORY}/server_log.log -e ${SERVERLOG_DIRECTORY}/server_err.log --append"
OPTIONS="--minUptime 20000 --spinSleepTime 15000"
#
forever start ${LOG_OPTONS} ${OPTIONS} server.js
#
echo "Please check the state of the server script by the standart forever commands ."

