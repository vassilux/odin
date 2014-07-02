**** Prepare developpement envirenement

Please install pip and virtualenv pacakges for your target system.
pip install virtualenv
pip install virtualenvwrapper

Or install python-dev python-twisted supervisor launchtool python-setuptools python-pip redis-server mongodb python-virtualenv virtualenvwrapper with apt-get , it can be more easy :-)

Note : Don't forget to initilize http_proxy and https_proxy envirenement variables if you use a proxy server into your network.


Edit the ~/.bashrc and add 
export WORKON_HOME=~/Projects/virtualEnvs (Note I use this path but if you wnat change it )
source /usr/local/bin/virtualenvwrapper.sh

Create the work virtual enveroment : mkvirtualenv odin
Activate the work virtual enveroment : workon odin

Install requirements pacakges with pip , you find the requirements.txt file into the install directory of the project.
pip install -r requirements.txt

Note: Please check it the directory install/packages is disponile. This directory has all projects dependencies packages.
Packages basicproperty-0.6.12a and starpy-1.0.2 can not be find into pypi web site.

Package pip2pi used to create a all python packages dependencies.

Install the basicproperty and startpy by hand ... 
cd to package
python setyp.py install

Install debian packages padoc texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended for generate the documentaiton on html, pdf formats

You are ready to the adventures !!!! 

**** Install applicaitons
REDIS : used for as communicaiton(broker) channel for exchange the messages beetwen different parts of the application.


**** Deploy application
http://www.marmelune.net/en/python/buildout/from-virtualenv-to-buildout/
