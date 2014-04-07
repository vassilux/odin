@echo off
tar --exclude=CVS --exclude=*.bat --exclude=*.pyc -cvf website.tar *
gzip website.tar
scp website.tar.gz mcfletch@shell.sourceforge.net:
rem scp website.tar.gz mcfletch@shell.sourceforge.net:/home/groups/b/ba/basicproperty/htdocs
echo ssh -l mcfletch simpleparse.sourceforge.net
echo cd /home/groups/b/ba/basicproperty/htdocs
del website.tar.gz
