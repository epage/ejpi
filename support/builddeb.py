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
Homepage: http://ejpi.garage.maemo.org/
"""
__author__ = "Ed Page"
__email__ = "eopage@byu.net"
__version__ = constants.__version__
__build__ = constants.__build__
__changelog__ = """
0.9.6
* Fullscreen by Ctrl+Enter
* "Enter" in number entry causes a push

0.9.4
 * Added icons
 * Minor improvements
 * Swapping the keyboard positions, seem more friendly to my thumb location this way

0.9.3 - ""
 * Added +/-, !, sq, and sqrt functions
 * Improved Documentation
 * Copy of calculation result and the corresponding equation
 * Bug fixes

0.9.2 - ""
 * Experimenting with faster startup by including pyc files in package
 * Minor tweaks and bug fixes

0.9.1 - "Laziness doesn't always pay off"
 * Profiled the code with an especial focus on the pie menus
 * Tried to reduce potential bugs with double clicks
 * Fixed a visual artifact issue on popup

0.9.0 - "Feed is for horses, so what about feedback?"
 * Initial public release
 * Pie menus for keys
 * Modifiable history
 * Supports different number types and bases
 * Basic trig support
"""


__postinstall__ = """#!/bin/sh -e

gtk-update-icon-cache -f /usr/share/icons/hicolor
"""


def find_files(path):
	for root, dirs, files in os.walk(path):
		for file in files:
			if file.startswith("src-"):
				fileParts = file.split("-")
				unused, relPathParts, newName = fileParts[0], fileParts[1:-1], fileParts[-1]
				assert unused == "src"
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
	p.upgradeDescription = __changelog__.split("\n\n", 1)[0]
	p.author = __author__
	p.mail = __email__
	p.license = "lgpl"
	p.depends = ", ".join([
		"python2.6 | python2.5",
		"python-gtk2 | python2.5-gtk2",
		"python-xml | python2.5-xml",
	])
	maemoSpecificDepends = ", python-osso | python2.5-osso, python-hildon | python2.5-hildon"
	p.depends += {
		"debian": ", python-glade2",
		"chinook": maemoSpecificDepends,
		"diablo": maemoSpecificDepends,
		"fremantle": maemoSpecificDepends + ", python-glade2",
		"mer": maemoSpecificDepends + ", python-glade2",
	}[distribution]
	p.section = "user/accessories"
	p.arch = "all"
	p.urgency = "low"
	p.distribution = "chinook diablo fremantle mer debian"
	p.repository = "extras"
	p.changelog = __changelog__
	p.postinstall = __postinstall__
	p.icon = {
		"debian": "26x26-ejpi.png",
		"chinook": "26x26-ejpi.png",
		"diablo": "26x26-ejpi.png",
		"fremantle": "64x64-ejpi.png", # Fremantle natively uses 48x48
		"mer": "64x64-ejpi.png",
	}[distribution]
	p["/usr/bin"] = [ "ejpi.py" ]
	for relPath, files in unflatten_files(find_files(".")).iteritems():
		fullPath = "/usr/lib/ejpi"
		if relPath:
			fullPath += os.sep+relPath
		p[fullPath] = list(
			"|".join((oldName, newName))
			for (oldName, newName) in files
		)
	p["/usr/share/applications/hildon"] = ["ejpi.desktop"]
	p["/usr/share/icons/hicolor/26x26/hildon"] = ["26x26-ejpi.png|ejpi.png"]
	p["/usr/share/icons/hicolor/64x64/hildon"] = ["64x64-ejpi.png|ejpi.png"]
	p["/usr/share/icons/hicolor/scalable/hildon"] = ["scale-ejpi.png|ejpi.png"]

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
