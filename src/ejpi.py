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

userLogPath = "%s/ejpi.log" % constants._data_path_
logging.basicConfig(level=logging.DEBUG, filename=userLogPath)
_moduleLogger.info("ejpi %s-%s" % (constants.__version__, constants.__build__))


ejpi_glade.run_calculator()
