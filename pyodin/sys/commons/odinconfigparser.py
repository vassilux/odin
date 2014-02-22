import os
import sys
import re
import time

from ConfigParser import SafeConfigParser, NoOptionError

#
class OdinConfigParser(SafeConfigParser):
    def optionxform(self, optionstr):
        return optionstr

#if __name__ == '__main__':
#	pass