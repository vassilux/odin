#!/bin/bash
#########################################################################################
#											
#											
#											
#											
#											
# Description : odin script installation				
# Author : vassilux
# Last modified : 2014-02-20 14:00:00 
########################################################################################## 

#source /usr/src/scripts/common
#Debian specific 
source /etc/bash_completion.d/virtualenvwrapper

MYSQL_ROOT_PW=lepanos
RC1_DB_USER=sa
RC1_DB_PASSWORD=ESI

function dprint()
{
  tput setb 1
  level="$1"
  dtype="$2"
  value="$3"
  echo -e "\e[00;31m $dtype:$level $value \e[00m" >&2
}

function install_system_packages(){
	dprint 0 INFO "Install system's packages"
	PACKAGES="python-dev supervisor launchtool python-setuptools python-pip redis-server mongodb python-virtualenv virtualenvwrapper"	
	
	CMD=`apt-get -y install ${PACKAGES} `
	if [ $? != 0 ]; then
		dprint 0 INFO "Package installation failed"
		echo $CMD
		y2continue
	fi
}

function install_rc1_database(){
	dprint 0 INFO "Do you want to install rc1 mysql database?[Y/n]"
	read resp
	if [ "$resp" = "Y" -o "$resp" = "y" ]; then

    dprint 0 INFO "Please provide host for rc1 user. If empty localhost will be used."  
    read rc1_host
    if [ "$rc1_host" = "" -o "$rc1_host" = "n" ]; then
      rc1_host="localhost"
    fi

		echo "CREATE DATABASE IF NOT EXISTS rc1;" | mysql -u root -p${MYSQL_ROOT_PW}
		echo "GRANT ALL PRIVILEGES ON rc1.* TO ${RC1_DB_USER}@${rc1_host} IDENTIFIED BY '${RC1_DB_PASSWORD}';" | mysql -u root -p${MYSQL_ROOT_PW}
		#root used cause SUPER privileges
		mysql -u root -p${MYSQL_ROOT_PW} rc1 < RC1.sql
	fi

}

function install_node_server(){
	dprint 0 INFO "Start node package installation....";
	dpkg -i  /usr/src/programs/node_*
    dprint 0 INFO "Node package is installed with success.";
    if [ ! -f /opt/odin/server/config/config.json ]; then
  		cp /opt/odin/server/config/config.sample.json /opt/odin/server/config/config.json
  	fi
}

function install_web_client(){
	if [ ! -f /opt/odin/client/app/config.json ]; then
  		dprint 0 INFO "Prepare the configuraiton file for the web client part."
  		cp /opt/odin/client/app/config.sample.json /opt/odin/client/app/config.json
  		dprint 0 INFO "Please provide the IP address of the web server ?";
  		read ip_adr
  		dprint 0 INFO "Please provide the port number of the web server ?";
  		read port_number
  		sed -i "s/X.X.X.X/$ip_adr/g" /opt/odin/client/app/config.json
  		sed -i "s/YYYY/$port_number/g" /opt/odin/client/app/config.json
  		dprint 0 INFO "Configuration file for the client part is ready."
  	else
  		dprint 0 INFO "Client configuration file existe. May be it is an udpate ? Please check it."
  	fi

}

function install_pyodin(){
	#keep this part for the future use ...
	#dprint 0 INFO "Do you have http proxy in the network ?"
	#dprint 0 INFO "In this case you must configure the proxy settings for pip like this : http://[adr_proxy]:[port_proxy]";
	#
	#ki="n"
  	#read proxy
  	#if [[ "${proxy}" == "" ]]; then
  	#		dprint 0 INFO "Proxy configuration skipped."	
  	#else
    #	export http_proxy="${proxy}"
    #	export https_proxy="${proxy}"
    #	dprint 0 INFO "Proxy for pip package manager configured ${proxy}."
  	#fi
  	if [ ! -f /opt/odin/install/requirements.txt ]; then
  		dprint 0 ERROR "Can't find requirements.txt file. Installation must be stopped."
  		exit 0;
  	fi

  	if [ ! -d /opt/odin/install/packages ]; then
  		dprint 0 ERROR "Can't find the packages local directory into your system. Installation must be stopped."
  		exit 0;
  	fi
  	mkvirtualenv --no-site-packages odin
    pip install /opt/odin/install/packages/basicproperty-0.6.12a.tar.gz
    pip install /opt/odin/install/packages/starpy.tar.gz
  	pip install -r requirements.txt --find-links=file:///opt/odin/install/packages
  	#configuration part
  	if [ ! -f /opt/odin/pyodin/conf/odinamilogger.conf ]; then
  		cp /opt/odin/pyodin/conf/odinamilogger.sample.conf /opt/odin/pyodin/conf/odinamilogger.conf
  	fi
  	if [ ! -f /opt/odin/pyodin/conf/odinami.conf ]; then
  		cp /opt/odin/pyodin/conf/odinami.sample.conf /opt/odin/pyodin/conf/odinami.conf
  	fi
  	if [ ! -f /opt/odin/pyodin/conf/odinf1com.conf ]; then
  		cp /opt/odin/pyodin/conf/odinf1com.sample.conf /opt/odin/pyodin/conf/odinf1com.conf
  	fi
  	if [ ! -f /opt/odin/pyodin/conf/odinincall.conf ]; then
  		cp /opt/odin/pyodin/conf/odinincall.sample.conf /opt/odin/pyodin/conf/odinincall.conf
  	fi
  	if [ ! -f /opt/odin/pyodin/conf/odinmonitor.conf ]; then
  		cp /opt/odin/pyodin/conf/odinmonitor.sample.conf /opt/odin/pyodin/conf/odinmonitor.conf
  	fi
  	if [ ! -f /opt/odin/pyodin/conf/odinsyslogger.conf ]; then
  		cp /opt/odin/pyodin/conf/odinsyslogger.sample.conf /opt/odin/pyodin/conf/odinsyslogger.conf
  	fi
  	if [ ! -f /opt/odin/pyodin/conf/odinsys.conf ]; then
  		cp /opt/odin/pyodin/conf/odinsys.sample.conf /opt/odin/pyodin/conf/odinsys.conf
  	fi
  	#
  	if [ ! -f /etc/supervisor/conf.d/odin.conf ]; then
  		cp /opt/odin/install/supervisor/odin.conf /etc/supervisor/conf.d/odin.conf
  	fi
  	dprint 0 INFO "PYODIN part is installed."

}


function main()
{
	dprint 0 INFO "Odin installation started."

  dprint 0 INFO "Please check if the mysql and mongodb servers are installed."
  dprint 0 INFO "If databases servers are not installed."
  dprint 0 INFO "Execute keSix install-lamp script, located into /usr/src/scripts"

  dprint 0 INFO "Do you want to continue?[y/n]"
  read resp
  if [ "$resp" = "" -o "$resp" = "n" ]; then
    dprint 0 INFO "See you next time. Bye"
  fi

	install_system_packages
	install_node_server
	install_web_client
	install_pyodin
	install_rc1_database
	install -m 0644 /opt/odin/install/odin.logrotate /etc/logrotate.d/odin
	dprint 0 INFO "Odin installation finished."
	dprint 0 INFO "Services activation..."
	supervisorctl reload
	sleep 3
	dprint 0 INFO "Services activated..."
	dprint 0 INFO " "
	dprint 0 INFO "Thank for using ODIN. Good luck."
}

function main_test()
{
  dprint 0 INFO "Please provide host for rc1 user. If empty localhost will be used."  
  read rc1_host
  if [ "$rc1_host" = "" -o "$rc1_host" = "n" ]; then
    rc1_host="localhost"
  fi

  dprint 0 INFO "rc1 user host name $rc1_host."  

}

main






