**** Install packages 
Please install pip and virtualenv pacakges for your target system.
pip install virtualenv
pip install virtualenvwrapper
Edit the ~/.bashrc and add 
export WORKON_HOME=~/Projects/virtualEnvs (Note I use this path but if you wnat change it )
source /usr/local/bin/virtualenvwrapper.sh

Create the work virtual enveroment : mkvirtualenv odin
Activate the work virtual enveroment : workon odin

Install requirements pacakges with pip , you find the requirements.txt file inot the docs directory of the project.
pip install -r requirements.txt

Install the basicproperty and startpy by hand ... 
cd to package
python setyp.py install

Install debian packages padoc texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended for generate the documentaiton on html, pdf formats

You are ready to the adventures !!!! 

**** Install applicaitons
REDIS : used for as communicaiton(broker) channel for exchange the messages beetwen different parts of the application.


**** Deploy application
http://www.marmelune.net/en/python/buildout/from-virtualenv-to-buildout/
