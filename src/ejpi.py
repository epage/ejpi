#!/usr/bin/env python

import sys
import logging


_moduleLogger = logging.getLogger(__name__)
sys.path.append("/opt/ejpi/lib")


import ejpi_qt


if __name__ == "__main__":
	ejpi_qt.run()
