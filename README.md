# ODIN project
Monitoring system for Asterisk IPBX.
This project is has 3 parts.
Http Server : Web server for monitoring iPBX states by web interface. This application is base inot nodejs.
OdinAMI : Dispatcher Asterisk AMI Events to the different types of client. REDIS message queue used as message dispatcher.
OdinF1COM : F1COM server some kind of glue beetwen OdinAMI and F1COM clients

## Web Server
Nodejs web server based. 
Client part of the application implemented with angularsjs.

### OdinAMI
Python twisted server based on starpy.
Monitor the states of an Asterisk IPBX to different type of clent and accept(dispatch) request to Asterisk IPBX. 


### OdinFCOM
Python twisted server.
Its role is to manage F1COM protocol for outgoing and incomming calls.
Configuration file contains values for different parameters.
Theses parameters are divided into several sections.
Section names and settings are very meaningful to use.
Please see the configuration file odinf1com.conf into config directory

Configuration of Asterisk dialplan is very important for the application.
Please pay a littele attention for the dialplan configuration.
Dialplan example is presented below

[incomming-calls-for-queue]
exten = _X.,1,NoOp(incomming-calls-for-queue)
same => n,Answer
same => n,UserEvent(incommingcall,Context:from-white-house, channel: ${CHANNEL}, extention:${EXTEN},calleridnum:${CALLERID(num)},calleridname:${CALLERID(name)},uniqueid: ${CDR(uniqueid)})
same => n,Goto(queues,6500,1)
same => n,Hangup()

Generated UserEvent is important for the incomming call processing don't forget to include the context to yours spans contexts.
You must configured a queue like below
[6500]
fullname = WaitingQueue
strategy = ringall
timeout = 15
wrapuptime = 15
autofill = no
autopause = no
joinempty = yes
leavewhenempty = no
reportholdtime = no
maxlen = 10
musicclass = default
eventwhencalled = yes

Important thing that provide joinempty = yes queue's parameter for leave the new incomming into the queue on waiting.


### Installation
Please read Readme.txt file into docs folder

## Directory Layout

    odin/                --> all application components and library
      client/              --> web client files

      server/              --> Nodejs web server 

      odinami/             --> AMI and F1COM servers
 
      scripts/            -->  Test scripts, not for production
      

      test/               -->  Test source files and libraries


## Contact


