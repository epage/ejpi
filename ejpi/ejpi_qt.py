#!/usr/bin/env python
# -*- coding: UTF8 -*-

from __future__ import with_statement

import os
try:
	import json as simplejson
except ImportError:
	print "json not available, falling back to simplejson"
	import simplejson
import string
import logging
import logging.handlers

import util.qt_compat as qt_compat
QtCore = qt_compat.QtCore
QtGui = qt_compat.import_module("QtGui")

import constants
from util import misc as misc_utils
from util import linux as linux_utils

from util import qui_utils
from util import qwrappers
from util import qtpie
from util import qtpieboard
import plugin_utils
import history
import qhistory


_moduleLogger = logging.getLogger(__name__)


class Calculator(qwrappers.ApplicationWrapper):

	def __init__(self, app):
		self._recent = []
		self._hiddenCategories = set()
		self._hiddenUnits = {}
		qwrappers.ApplicationWrapper.__init__(self, app, constants)

	def load_settings(self):
		settingsPath = linux_utils.get_resource_path(
			"config", constants.__app_name__, "settings.json"
		)
		try:
			with open(settingsPath) as settingsFile:
				settings = simplejson.load(settingsFile)
		except IOError, e:
			_moduleLogger.info("No settings")
			settings = {}
		except ValueError:
			_moduleLogger.info("Settings were corrupt")
			settings = {}

		isPortraitDefault = qui_utils.screen_orientation() == QtCore.Qt.Vertical
		self._fullscreenAction.setChecked(settings.get("isFullScreen", False))
		self._orientationAction.setChecked(settings.get("isPortrait", isPortraitDefault))

	def save_settings(self):
		settings = {
			"isFullScreen": self._fullscreenAction.isChecked(),
			"isPortrait": self._orientationAction.isChecked(),
		}

		settingsPath = linux_utils.get_resource_path(
			"config", constants.__app_name__, "settings.json"
		)
		with open(settingsPath, "w") as settingsFile:
			simplejson.dump(settings, settingsFile)

	@property
	def dataPath(self):
		return self._dataPath

	def _new_main_window(self):
		return MainWindow(None, self)

	@misc_utils.log_exception(_moduleLogger)
	def _on_about(self, checked = True):
		raise NotImplementedError("Booh")


class QValueEntry(object):

	def __init__(self):
		self._widget = QtGui.QLineEdit("")
		qui_utils.mark_numbers_preferred(self._widget)

	@property
	def toplevel(self):
		return self._widget

	@property
	def entry(self):
		return self._widget

	def get_value(self):
		value = str(self._widget.text()).strip()
		if any(
			0 < value.find(whitespace)
			for whitespace in string.whitespace
		):
			self.clear()
			raise ValueError('Invalid input "%s"' % value)
		return value

	def set_value(self, value):
		value = value.strip()
		if any(
			0 < value.find(whitespace)
			for whitespace in string.whitespace
		):
			raise ValueError('Invalid input "%s"' % value)
		self._widget.setText(value)

	def append(self, value):
		value = value.strip()
		if any(
			0 < value.find(whitespace)
			for whitespace in string.whitespace
		):
			raise ValueError('Invalid input "%s"' % value)
		self.set_value(self.get_value() + value)

	def pop(self):
		value = self.get_value()[0:-1]
		self.set_value(value)

	def clear(self):
		self.set_value("")

	value = property(get_value, set_value, clear)


class MainWindow(qwrappers.WindowWrapper):

	_plugin_search_paths = [
		os.path.join(os.path.dirname(__file__), "plugins/"),
	]

	_user_history = linux_utils.get_resource_path("config", constants.__app_name__, "history.stack")

	def __init__(self, parent, app):
		qwrappers.WindowWrapper.__init__(self, parent, app)
		self._window.setWindowTitle("%s" % constants.__pretty_app_name__)
		#self._freezer = qwrappers.AutoFreezeWindowFeature(self._app, self._window)

		self._historyView = qhistory.QCalcHistory(self._app.errorLog)
		self._userEntry = QValueEntry()
		self._userEntry.entry.returnPressed.connect(self._on_push)
		self._userEntryLayout = QtGui.QHBoxLayout()
		self._userEntryLayout.setContentsMargins(0, 0, 0, 0)
		self._userEntryLayout.addWidget(self._userEntry.toplevel, 10)

		self._controlLayout = QtGui.QVBoxLayout()
		self._controlLayout.setContentsMargins(0, 0, 0, 0)
		self._controlLayout.addWidget(self._historyView.toplevel, 1000)
		self._controlLayout.addLayout(self._userEntryLayout, 0)

		self._keyboardTabs = QtGui.QTabWidget()

		self._layout.addLayout(self._controlLayout)
		self._layout.addWidget(self._keyboardTabs)

		self._copyItemAction = QtGui.QAction(None)
		self._copyItemAction.setText("Copy")
		self._copyItemAction.setShortcut(QtGui.QKeySequence("CTRL+c"))
		self._copyItemAction.triggered.connect(self._on_copy)

		self._pasteItemAction = QtGui.QAction(None)
		self._pasteItemAction.setText("Paste")
		self._pasteItemAction.setShortcut(QtGui.QKeySequence("CTRL+v"))
		self._pasteItemAction.triggered.connect(self._on_paste)

		self._closeWindowAction = QtGui.QAction(None)
		self._closeWindowAction.setText("Close")
		self._closeWindowAction.setShortcut(QtGui.QKeySequence("CTRL+w"))
		self._closeWindowAction.triggered.connect(self._on_close_window)

		self._window.addAction(self._copyItemAction)
		self._window.addAction(self._pasteItemAction)

		self._constantPlugins = plugin_utils.ConstantPluginManager()
		self._constantPlugins.add_path(*self._plugin_search_paths)
		for pluginName in ["Builtins", "Trigonometry", "Computer", "Alphabet"]:
			try:
				pluginId = self._constantPlugins.lookup_plugin(pluginName)
				self._constantPlugins.enable_plugin(pluginId)
			except:
				_moduleLogger.exception("Failed to load plugin %s" % pluginName)

		self._operatorPlugins = plugin_utils.OperatorPluginManager()
		self._operatorPlugins.add_path(*self._plugin_search_paths)
		for pluginName in ["Builtins", "Trigonometry", "Computer", "Alphabet"]:
			try:
				pluginId = self._operatorPlugins.lookup_plugin(pluginName)
				self._operatorPlugins.enable_plugin(pluginId)
			except:
				_moduleLogger.exception("Failed to load plugin %s" % pluginName)

		self._keyboardPlugins = plugin_utils.KeyboardPluginManager()
		self._keyboardPlugins.add_path(*self._plugin_search_paths)
		self._activeKeyboards = []

		self._history = history.RpnCalcHistory(
			self._historyView,
			self._userEntry, self._app.errorLog,
			self._constantPlugins.constants, self._operatorPlugins.operators
		)
		self._load_history()

		# Basic keyboard stuff
		self._handler = qtpieboard.KeyboardHandler(self._on_entry_direct)
		self._handler.register_command_handler("push", self._on_push)
		self._handler.register_command_handler("unpush", self._on_unpush)
		self._handler.register_command_handler("backspace", self._on_entry_backspace)
		self._handler.register_command_handler("clear", self._on_entry_clear)

		# Main keyboard
		entryKeyboardId = self._keyboardPlugins.lookup_plugin("Entry")
		self._keyboardPlugins.enable_plugin(entryKeyboardId)
		entryPlugin = self._keyboardPlugins.keyboards["Entry"].construct_keyboard()
		entryKeyboard = entryPlugin.setup(self._history, self._handler)
		self._userEntryLayout.addWidget(entryKeyboard.toplevel)

		# Plugins
		self.enable_plugin(self._keyboardPlugins.lookup_plugin("Builtins"))
		self.enable_plugin(self._keyboardPlugins.lookup_plugin("Trigonometry"))
		self.enable_plugin(self._keyboardPlugins.lookup_plugin("Computer"))
		self.enable_plugin(self._keyboardPlugins.lookup_plugin("Alphabet"))

		self._scrollTimer = QtCore.QTimer()
		self._scrollTimer.setInterval(0)
		self._scrollTimer.setSingleShot(True)
		self._scrollTimer.timeout.connect(self._on_delayed_scroll_to_bottom)
		self._scrollTimer.start()

		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self.update_orientation(self._app.orientation)

	def walk_children(self):
		return ()

	def update_orientation(self, orientation):
		qwrappers.WindowWrapper.update_orientation(self, orientation)
		windowOrientation = self.idealWindowOrientation
		if windowOrientation == QtCore.Qt.Horizontal:
			defaultLayoutOrientation = QtGui.QBoxLayout.LeftToRight
			tabPosition = QtGui.QTabWidget.North
		else:
			defaultLayoutOrientation = QtGui.QBoxLayout.TopToBottom
			#tabPosition = QtGui.QTabWidget.South
			tabPosition = QtGui.QTabWidget.West
		self._layout.setDirection(defaultLayoutOrientation)
		self._keyboardTabs.setTabPosition(tabPosition)

	def enable_plugin(self, pluginId):
		self._keyboardPlugins.enable_plugin(pluginId)
		pluginData = self._keyboardPlugins.plugin_info(pluginId)
		pluginName = pluginData[0]
		plugin = self._keyboardPlugins.keyboards[pluginName].construct_keyboard()
		relIcon = self._keyboardPlugins.keyboards[pluginName].icon
		for iconPath in self._keyboardPlugins.keyboards[pluginName].iconPaths:
			absIconPath = os.path.join(iconPath, relIcon)
			if os.path.exists(absIconPath):
				icon = QtGui.QIcon(absIconPath)
				break
		else:
			icon = None
		pluginKeyboard = plugin.setup(self._history, self._handler)

		self._activeKeyboards.append({
			"pluginName": pluginName,
			"plugin": plugin,
			"pluginKeyboard": pluginKeyboard,
		})
		if icon is None:
			self._keyboardTabs.addTab(pluginKeyboard.toplevel, pluginName)
		else:
			self._keyboardTabs.addTab(pluginKeyboard.toplevel, icon, "")

	def close(self):
		qwrappers.WindowWrapper.close(self)
		self._save_history()

	def _load_history(self):
		serialized = []
		try:
			with open(self._user_history, "rU") as f:
				serialized = (
					(part.strip() for part in line.split(" "))
					for line in f.readlines()
				)
		except IOError, e:
			if e.errno != 2:
				raise
		self._history.deserialize_stack(serialized)

	def _save_history(self):
		serialized = self._history.serialize_stack()
		with open(self._user_history, "w") as f:
			for lineData in serialized:
				line = " ".join(data for data in lineData)
				f.write("%s\n" % line)

	@misc_utils.log_exception(_moduleLogger)
	def _on_delayed_scroll_to_bottom(self):
		with qui_utils.notify_error(self._app.errorLog):
			self._historyView.scroll_to_bottom()

	@misc_utils.log_exception(_moduleLogger)
	def _on_child_close(self, something = None):
		with qui_utils.notify_error(self._app.errorLog):
			self._child = None

	@misc_utils.log_exception(_moduleLogger)
	def _on_copy(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			eqNode = self._historyView.peek()
			resultNode = eqNode.simplify()
			self._app._clipboard.setText(str(resultNode))

	@misc_utils.log_exception(_moduleLogger)
	def _on_paste(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			result = str(self._app._clipboard.text())
			self._userEntry.append(result)

	@misc_utils.log_exception(_moduleLogger)
	def _on_entry_direct(self, keys, modifiers):
		with qui_utils.notify_error(self._app.errorLog):
			if "shift" in modifiers:
				keys = keys.upper()
			self._userEntry.append(keys)

	@misc_utils.log_exception(_moduleLogger)
	def _on_push(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			self._history.push_entry()

	@misc_utils.log_exception(_moduleLogger)
	def _on_unpush(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			self._historyView.unpush()

	@misc_utils.log_exception(_moduleLogger)
	def _on_entry_backspace(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			self._userEntry.pop()

	@misc_utils.log_exception(_moduleLogger)
	def _on_entry_clear(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			self._userEntry.clear()

	@misc_utils.log_exception(_moduleLogger)
	def _on_clear_all(self, *args):
		with qui_utils.notify_error(self._app.errorLog):
			self._history.clear()


def run():
	try:
		os.makedirs(linux_utils.get_resource_path("config", constants.__app_name__))
	except OSError, e:
		if e.errno != 17:
			raise
	try:
		os.makedirs(linux_utils.get_resource_path("cache", constants.__app_name__))
	except OSError, e:
		if e.errno != 17:
			raise
	try:
		os.makedirs(linux_utils.get_resource_path("data", constants.__app_name__))
	except OSError, e:
		if e.errno != 17:
			raise

	logPath = linux_utils.get_resource_path("cache", constants.__app_name__, "%s.log" % constants.__app_name__)
	logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(threadName)s.%(name)s.%(funcName)s: %(message)s'
	logging.basicConfig(level=logging.DEBUG, format=logFormat)
	rotating = logging.handlers.RotatingFileHandler(logPath, maxBytes=512*1024, backupCount=1)
	rotating.setFormatter(logging.Formatter(logFormat))
	root = logging.getLogger()
	root.addHandler(rotating)
	_moduleLogger.info("%s %s-%s" % (constants.__app_name__, constants.__version__, constants.__build__))
	_moduleLogger.info("OS: %s" % (os.uname()[0], ))
	_moduleLogger.info("Kernel: %s (%s) for %s" % os.uname()[2:])
	_moduleLogger.info("Hostname: %s" % os.uname()[1])

	app = QtGui.QApplication([])
	handle = Calculator(app)
	qtpie.init_pies()
	return app.exec_()


if __name__ == "__main__":
	import sys
	val = run()
	sys.exit(val)
