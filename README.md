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


