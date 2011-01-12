#!/usr/bin/python2.5

import os
import sys

try:
	import py2deb
except ImportError:
	import fake_py2deb as py2deb

import constants


__appname__ = constants.__app_name__
__description__ = """A Touch Screen Optimized RPN Calculator using Pie Menus
.
RPN: Stack based math, come on it is fun
.
Pie Menus: Press them or press-drag them
.
History: Its such a drag, so drag them around, delete them, etc
.
Homepage: http://ejpi.garage.maemo.org/
"""
__author__ = "Ed Page"
__email__ = "eopage@byu.net"
__version__ = constants.__version__
__build__ = constants.__build__
__changelog__ = """
* Cleaning up the display of the pie buttons
* Fixing the size of the pie menus on Maemo 5
* Adding rotation support with a custom portrait layout
* Minor UI Polish
""".strip()


__postinstall__ = """#!/bin/sh -e

gtk-update-icon-cache -f /usr/share/icons/hicolor
rm -f ~/.%(name)s/%(name)s.log
""" % {"name": constants.__app_name__}

__preremove__ = """#!/bin/sh -e
"""


def find_files(prefix, path):
	for root, dirs, files in os.walk(path):
		for file in files:
			if file.startswith(prefix+"-"):
				fileParts = file.split("-")
				unused, relPathParts, newName = fileParts[0], fileParts[1:-1], fileParts[-1]
				assert unused == prefix
				relPath = os.sep.join(relPathParts)
				yield relPath, file, newName


def unflatten_files(files):
	d = {}
	for relPath, oldName, newName in files:
		if relPath not in d:
			d[relPath] = []
		d[relPath].append((oldName, newName))
	return d


def build_package(distribution):
	try:
		os.chdir(os.path.dirname(sys.argv[0]))
	except:
		pass

	py2deb.Py2deb.SECTIONS = py2deb.SECTIONS_BY_POLICY[distribution]
	p = py2deb.Py2deb(__appname__)
	p.prettyName = constants.__pretty_app_name__
	p.description = __description__
	p.bugTracker = "https://bugs.maemo.org/enter_bug.cgi?product=ejpi"
	p.author = __author__
	p.mail = __email__
	p.license = "lgpl"
	p.depends = ", ".join([
		"python2.6 | python2.5",
	])
	p.depends += {
		"debian": ", python-qt4",
		"diablo": ", python2.5-qt4-core, python2.5-qt4-gui",
		"fremantle": ", python2.5-qt4-core, python2.5-qt4-gui, python2.5-qt4-maemo5",
	}[distribution]
	p.section = {
		"debian": "math",
		"diablo": "user/science",
		"fremantle": "user/science",
	}[distribution]
	p.arch = "all"
	p.urgency = "low"
	p.distribution = "diablo fremantle debian"
	p.repository = "extras"
	p.changelog = __changelog__
	p.postinstall = __postinstall__
	p.icon = {
		"debian": "26x26-ejpi.png",
		"diablo": "26x26-ejpi.png",
		"fremantle": "64x64-ejpi.png", # Fremantle natively uses 48x48
	}[distribution]
	p["/opt/%s/bin" % __appname__] = [ "%s.py" % __appname__ ]
	for relPath, files in unflatten_files(find_files("src", ".")).iteritems():
		fullPath = "/opt/%s/lib" % __appname__
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	p["/usr/share/applications/hildon"] = ["%s.desktop" % __appname__]
	p["/usr/share/icons/hicolor/26x26/hildon"] = ["26x26-ejpi.png|ejpi.png"]
	p["/usr/share/icons/hicolor/64x64/hildon"] = ["64x64-ejpi.png|ejpi.png"]
	p["/usr/share/icons/hicolor/scalable/hildon"] = ["scale-ejpi.png|ejpi.png"]

	if distribution == "debian":
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=True,
			tar=False,
			changes=False,
			dsc=False,
		)
		print "Building for %s finished" % distribution
	else:
		print p
		print p.generate(
			version="%s-%s" % (__version__, __build__),
			changelog=__changelog__,
			build=False,
			tar=True,
			changes=True,
			dsc=True,
		)
		print "Building for %s finished" % distribution


if __name__ == "__main__":
	if len(sys.argv) > 1:
		try:
			import optparse
		except ImportError:
			optparse = None

		if optparse is not None:
			parser = optparse.OptionParser()
			(commandOptions, commandArgs) = parser.parse_args()
	else:
		commandArgs = None
		commandArgs = ["diablo"]
	build_package(commandArgs[0])
