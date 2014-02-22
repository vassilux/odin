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

function install_system_packages(){
	dprint 0 INFO "Install system's packages"
	PACKAGES="python-dev python-twisted supervisor launchtool python-setuptools python-pip"	
	
	CMD=`apt-get -y install ${PACKAGES} `
	if [ $? != 0 ]; then
	{
			dprint 0 INFO "Package installation failed"
    		echo $CMD
			y2continue
	} fi
}

function install_node_server(){

}

function install_web_client(){

}

function install_pyodin(){
	dprint 0 INFO "Do you have http proxy in the network ?"
	dprint 0 INFO "In this case you must configure the proxy settings for pip like this : http://[adr_proxy]:[port_proxy]";
	#
	ki="n"
  	read proxy
  	if [[ "${proxy}" == "" ]]; then
  			dprint 0 INFO "Proxy configuration skipped."	
  	else
    	export http_proxy="${proxy}"
    	export https_proxy="${proxy}"
    	dprint 0 INFO "Proxy for pip package manager configured ${proxy}."
  	fi
}

function install_redis()
{
	cd /opt/odin/install
	if [ ! -f /opt/odin/install/redis-server_2%3a2.4.15-1~bpo60+2_i386.deb ]; then
	 dprint 0 INFO "Error can't find redis-server_2%3a2.4.15-1~bpo60+2_i386.deb into vor install directory";
	 exit;
	else
		dpkg -i redis-server_2%3a2.4.15-1~bpo60+2_i386.deb	
    fi

}

function install_mongodb()
{
	cd /opt/odin/install
	if [ ! -f /opt/odin/install/mongodb-10gen_2.2.0_i386.deb ]; then
	 dprint 0 INFO "Error can't find mongodb-10gen_2.2.0_i386.deb into vor install directory";
	 exit;
	else
		dpkg -i mongodb-10gen_2.2.0_i386.deb	
    fi

}


function install_node()
{
	cat /etc/kesix/kesix-addons|grep nodejs &>/dev/null
	res=$?
	pause
	if [ ! $res -eq 0 ]; then
		cp /usr/src/programs/node-${NODEJS_VER}.tar.gz /usr/src/node-${NODEJS_VER}.tar.gz
		cd /usr/src
		tar xvzf /usr/src/node-${NODEJS_VER}.tar.gz
		cd node-${NODEJS_VER}
		./configure
		make
		make install
		dprint 0 INFO "nodejs installed."
		dprint 0 INFO "Do you have http proxy in the network ?"
		dprint 0 INFO "In this case you must configure the proxy settings for nodejs like this : http://[adr_proxy]:[port_proxy]";
		#
		ki="n"
  		read proxy
  		if [[ "${proxy}" == "" ]]; then
  			dprint 0 INFO "Proxy configuration skipped."	
  		else
  			npm config set strict-ssl false
    		npm config set proxy ${proxy}
    		dprint 0 INFO "Proxy for nodejs package manager configured ${proxy}."
  		fi
  		dprint 0 INFO "I will install forever."
  		npm install -g forever
  		PKGNAME=node-${NODEJS_VER}
	fi
}


function main()
{
	dprint 0 INFO "Odin installation started."
	install_system_packages
	install_node
	install_redis
	install_mongodb
	install_node_server
	install_web_client
	install_pyodin
	dprint 0 INFO "Odin installation finished."
}

main






