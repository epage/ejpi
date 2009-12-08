#!/usr/bin/python

import os
import sys
import logging


_moduleLogger = logging.getLogger("dialcentral")
sys.path.append("/usr/lib/ejpi/")


import constants
import ejpi_glade


try:
	os.makedirs(constants._data_path_)
except OSError, e:
	if e.errno != 17:
		raise

logging.basicConfig(level=logging.DEBUG, filename=constants._user_logpath_)
_moduleLogger.info("ejpi %s-%s" % (constants.__version__, constants.__build__))
_moduleLogger.info("OS: %s" % (os.uname()[0], ))
_moduleLogger.info("Kernel: %s (%s) for %s" % os.uname()[2:])
_moduleLogger.info("Hostname: %s" % os.uname()[1])


ejpi_glade.run_calculator()
