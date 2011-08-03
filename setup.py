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
from ejpi import constants


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


changes = ""
icon = "data/%s.png" % constants.__app_name__


setup(
	name=constants.__app_name__,
	version=constants.__version__,
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
	packages=list(find_packages(constants.__app_name__, includeRoot=True)),
	data_files=[
		#[[[cog
		#	import cog
		#	cog.outl('		("%s", ["data/%%s.desktop" %% constants.__app_name__]),' % desktopFilePath)
		#]]]
		("/usr/share/applications", ["data/%s.desktop" % constants.__app_name__]),
		#[[[end]]]
		("/usr/share/icons/hicolor/22x22/apps", ["data/icons/22/%s.png" % constants.__app_name__]),
		("/usr/share/icons/hicolor/28x28/apps", ["data/icons/28/%s.png" % constants.__app_name__]),
		("/usr/share/icons/hicolor/32x32/apps", ["data/icons/32/%s.png" % constants.__app_name__]),
		("/usr/share/icons/hicolor/48x48/apps", ["data/icons/48/%s.png" % constants.__app_name__]),
		("/usr/share/icons/hicolor/scalable/apps", ["data/%s.svg" % constants.__app_name__]),
	],
	requires=[
		"PySide",
	],
	cmdclass={
		'sdist_diablo': sdist_maemo,
		'sdist_fremantle': sdist_maemo,
		'sdist_harmattan': sdist_maemo,
	},
	options={
		"sdist_diablo": {
			"debian_package": constants.__app_name__,
			"Maemo_Display_Name": constants.__pretty_app_name__,
			#"Maemo_Upgrade_Description": changes,
			"Maemo_Bugtracker": "https://bugs.maemo.org/enter_bug.cgi?product=ejpi",
			"Maemo_Icon_26": "data/icons/48/%s.png" % constants.__app_name__,
			"MeeGo_Desktop_Entry_Filename": constants.__app_name__,
			#"MeeGo_Desktop_Entry": "",
			"section": "user/science",
			"copyright": "lgpl",
			"changelog": changes,
			"buildversion": str(constants.__build__),
			"depends": "python, python-qt4-core, python-qt4-gui",
			"architecture": "any",
		},
		"sdist_fremantle": {
			"debian_package": constants.__app_name__,
			"Maemo_Display_Name": constants.__pretty_app_name__,
			#"Maemo_Upgrade_Description": changes,
			"Maemo_Bugtracker": "https://bugs.maemo.org/enter_bug.cgi?product=ejpi",
			"Maemo_Icon_26": "data/icons/48/%s.png" % constants.__app_name__,
			"MeeGo_Desktop_Entry_Filename": constants.__app_name__,
			#"MeeGo_Desktop_Entry": "",
			"section": "user/science",
			"copyright": "lgpl",
			"changelog": changes,
			"buildversion": str(constants.__build__),
			"depends": "python, python-pyside.qtcore, python-pyside.qtgui, python-pyside.maemo5",
			"architecture": "any",
		},
		"sdist_harmattan": {
			"debian_package": constants.__app_name__,
			"Maemo_Display_Name": constants.__pretty_app_name__,
			#"Maemo_Upgrade_Description": changes,
			"Maemo_Bugtracker": "https://bugs.maemo.org/enter_bug.cgi?product=ejpi",
			"Maemo_Icon_26": "data/icons/26/%s.png" % constants.__app_name__,
			"MeeGo_Desktop_Entry_Filename": constants.__app_name__,
			#"MeeGo_Desktop_Entry": "",
			"section": "user/science",
			"copyright": "lgpl",
			"changelog": changes,
			"buildversion": str(constants.__build__),
			"depends": "python, python-pyside.qtcore, python-pyside.qtgui",
			"architecture": "any",
		},
		"bdist_rpm": {
			"requires": "REPLACEME",
			"icon": icon,
			"group": "REPLACEME",
		},
	},
)
