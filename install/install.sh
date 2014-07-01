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

source /usr/src/scripts/common
#Debian specific 
source /etc/bash_completion.d/virtualenvwrapper

MYSQL_ROOT_PW=lepanos
RC1_DB_USER=sa
RC1_DB_PASSWORD=ESI

function install_system_packages(){
	dprint 0 INFO "Install system's packages"
	PACKAGES="python-dev python-twisted supervisor launchtool python-setuptools python-pip redis-server mongodb python-virtualenv virtualenvwrapper"	
	
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
		echo "CREATE DATABASE IF NOT EXISTS rc1;" | mysql -u root -p${MYSQL_ROOT_PW}
		echo "GRANT ALL PRIVILEGES ON rc1.* TO ${RC1_DB_USER}@localhost IDENTIFIED BY '${RC1_DB_PASSWORD}';" | mysql -u root -p${MYSQL_ROOT_PW}
		#
		mysql -u${RC1_DB_USER} -p${RC1_DB_PASSWORD} rc1 < RC1.sql
	fi

}

function install_node_server(){
	echo ""
	#if [ $(dpkg-query -W -f='${Status') node 2>/dev/null | grep -c "ok installed") -eq 0 ]; then
	# dprint 0 INFO "Node package is not installed. Try install the node pacakge.";
	# dpkg -i /usr/src/programs/node_*
	#else
	#	dprint 0 INFO "Node package is already installed. Skip thist step";	
   # fi
}

function install_web_client(){
	echo ""
}

function install_pyodin(){
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
  	pip install -r requirements.txt --find-links=file:///opt/odin/install/packages
}


function main()
{
	dprint 0 INFO "Odin installation started."
	install_system_packages
	#install_node_server
	#install_web_client
	install_pyodin
	#install -m 0644 /opt/odin/install/odin.logrotate /etc/logrotate.d/odin
	dprint 0 INFO "Odin installation finished."
}

main






