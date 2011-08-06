#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
reload(sys).setdefaultencoding("UTF-8")
import os

try:
	from sdist_maemo import sdist_maemo as _sdist_maemo
	sdist_maemo = _sdist_maemo
except ImportError:
	sdist_maemo = None
	print 'sdist_maemo command not available'

from distutils.core import setup


#[[[cog
#	import cog
#	from ejpi import constants
#	cog.outl('APP_NAME="%s"' % constants.__app_name__)
#	cog.outl('PRETTY_APP_NAME="%s"' % constants.__pretty_app_name__)
#	cog.outl('VERSION="%s"' % constants.__version__)
#	cog.outl('BUILD="%s"' % constants.__build__)
#	cog.outl('DESKTOP_FILE_PATH="%s"' % DESKTOP_FILE_PATH)
#	cog.outl('INPUT_DESKTOP_FILE="%s"' % INPUT_DESKTOP_FILE)
#]]]
APP_NAME="ejpi"
PRETTY_APP_NAME="e**(j pi) + 1 = 0"
VERSION="0.1.0"
BUILD=0
DESKTOP_FILE_PATH="/usr/share/applications"
INPUT_DESKTOP_FILE="data/harmattan/ejpi.desktop"
#[[[end]]]

CHANGES = """Switching from py2deb.py to sdist_maemo
""".strip()
BUGTRACKER_URL = "https://bugs.maemo.org/enter_bug.cgi?product=ejpi"


def is_package(path):
	return (
		os.path.isdir(path) and
		os.path.isfile(os.path.join(path, '__init__.py'))
	)


def find_packages(path, base="", includeRoot=False):
	""" Find all packages in path """
	if includeRoot:
		assert not base, "Base not supported with includeRoot: %r" % base
		rootPath, module_name = os.path.split(path)
		yield module_name
		base = module_name
	for item in os.listdir(path):
		dir = os.path.join(path, item)
		if is_package( dir ):
			if base:
				module_name = "%(base)s.%(item)s" % vars()
			else:
				module_name = item
			yield module_name
			for mname in find_packages(dir, module_name):
				yield mname


setup(
	name=APP_NAME,
	version=VERSION,
	description="RPN calculator designed for touchscreens",
	long_description="RPN calculator designed for touchscreens",
	author="Ed Page",
	author_email="eopage@byu.net",
	maintainer="Ed Page",
	maintainer_email="eopage@byu.net",
	url="http://ejpi.garage.maemo.org/",
	license="GNU LGPLv2.1",
	scripts=[
		"ejpi-calc",
	],
	packages=list(find_packages(APP_NAME, includeRoot=True)),
	package_data={
		"plugins": "*.ini"
	},
	data_files=[
		(DESKTOP_FILE_PATH, [INPUT_DESKTOP_FILE]),
		("/usr/share/icons/hicolor/22x22/apps", ["data/icons/22/%s.png" % APP_NAME]),
		("/usr/share/icons/hicolor/28x28/apps", ["data/icons/28/%s.png" % APP_NAME]),
		("/usr/share/icons/hicolor/32x32/apps", ["data/icons/32/%s.png" % APP_NAME]),
		("/usr/share/icons/hicolor/48x48/apps", ["data/icons/48/%s.png" % APP_NAME]),
		("/usr/share/icons/hicolor/80x80/apps", ["data/icons/80/%s.png" % APP_NAME]),
		("/usr/share/icons/hicolor/scalable/apps", ["data/%s.svg" % APP_NAME]),
	],
	requires=[
		"PySide",
	],
	cmdclass={
		'sdist_ubuntu': sdist_maemo,
		'sdist_diablo': sdist_maemo,
		'sdist_fremantle': sdist_maemo,
		'sdist_harmattan': sdist_maemo,
	},
	options={
		"sdist_ubuntu": {
			"debian_package": APP_NAME,
			"section": "math",
			"copyright": "lgpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "python, python-pyside.qtcore, python-pyside.qtgui",
			"architecture": "any",
		},
		"sdist_diablo": {
			"debian_package": APP_NAME,
			"Maemo_Display_Name": PRETTY_APP_NAME,
			#"Maemo_Upgrade_Description": CHANGES,
			"Maemo_Bugtracker": BUGTRACKER_URL,
			"Maemo_Icon_26": "data/icons/26/%s.png" % APP_NAME,
			"section": "user/science",
			"copyright": "lgpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "python2.5, python2.5-qt4-core, python2.5-qt4-gui",
			"architecture": "any",
		},
		"sdist_fremantle": {
			"debian_package": APP_NAME,
			"Maemo_Display_Name": PRETTY_APP_NAME,
			#"Maemo_Upgrade_Description": CHANGES,
			"Maemo_Bugtracker": BUGTRACKER_URL,
			"Maemo_Icon_26": "data/icons/48/%s.png" % APP_NAME,
			"section": "user/science",
			"copyright": "lgpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "python, python-pyside.qtcore, python-pyside.qtgui, python-pyside.qtmaemo5",
			"architecture": "any",
		},
		"sdist_harmattan": {
			"debian_package": APP_NAME,
			"Maemo_Display_Name": PRETTY_APP_NAME,
			#"Maemo_Upgrade_Description": CHANGES,
			"Maemo_Bugtracker": BUGTRACKER_URL,
			"Maemo_Icon_26": "data/icons/48/%s.png" % APP_NAME,
			"MeeGo_Desktop_Entry_Filename": APP_NAME,
			#"MeeGo_Desktop_Entry": "",
			"section": "user/science",
			"copyright": "lgpl",
			"changelog": CHANGES,
			"buildversion": str(BUILD),
			"depends": "python, python-pyside.qtcore, python-pyside.qtgui",
			"architecture": "any",
		},
		"bdist_rpm": {
			"requires": "REPLACEME",
			"icon": "data/icons/48/%s.png" % APP_NAME,
			"group": "REPLACEME",
		},
	},
)
