#!/usr/bin/env python
# -*- coding: UTF8 -*-

from __future__ import with_statement

import sys
import os
import simplejson
import string
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore

import constants
import maeqt
from util import misc as misc_utils

from libraries import qtpie
from libraries import qtpieboard
import plugin_utils
import history
import qhistory


_moduleLogger = logging.getLogger(__name__)


IS_MAEMO = True


PLUGIN_SEARCH_PATHS = [
	os.path.join(os.path.dirname(__file__), "plugins/"),
]


class Calculator(object):

	def __init__(self, app):
		self._app = app
		self._recent = []
		self._hiddenCategories = set()
		self._hiddenUnits = {}
		self._clipboard = QtGui.QApplication.clipboard()
		self._mainWindow = None

		self._fullscreenAction = QtGui.QAction(None)
		self._fullscreenAction.setText("Fullscreen")
		self._fullscreenAction.setCheckable(True)
		self._fullscreenAction.setShortcut(QtGui.QKeySequence("CTRL+Enter"))
		self._fullscreenAction.toggled.connect(self._on_toggle_fullscreen)

		self._logAction = QtGui.QAction(None)
		self._logAction.setText("Log")
		self._logAction.setShortcut(QtGui.QKeySequence("CTRL+l"))
		self._logAction.triggered.connect(self._on_log)

		self._quitAction = QtGui.QAction(None)
		self._quitAction.setText("Quit")
		self._quitAction.setShortcut(QtGui.QKeySequence("CTRL+q"))
		self._quitAction.triggered.connect(self._on_quit)

		self._app.lastWindowClosed.connect(self._on_app_quit)
		self.load_settings()

		self._mainWindow = MainWindow(None, self)
		self._mainWindow.window.destroyed.connect(self._on_child_close)

	def load_settings(self):
		try:
			with open(constants._user_settings_, "r") as settingsFile:
				settings = simplejson.load(settingsFile)
		except IOError, e:
			_moduleLogger.info("No settings")
			settings = {}
		except ValueError:
			_moduleLogger.info("Settings were corrupt")
			settings = {}

		self._fullscreenAction.setChecked(settings.get("isFullScreen", False))

	def save_settings(self):
		settings = {
			"isFullScreen": self._fullscreenAction.isChecked(),
		}
		with open(constants._user_settings_, "w") as settingsFile:
			simplejson.dump(settings, settingsFile)

	@property
	def fullscreenAction(self):
		return self._fullscreenAction

	@property
	def logAction(self):
		return self._logAction

	@property
	def quitAction(self):
		return self._quitAction

	def _close_windows(self):
		if self._mainWindow is not None:
			self._mainWindow.window.destroyed.disconnect(self._on_child_close)
			self._mainWindow.close()
			self._mainWindow = None

	@misc_utils.log_exception(_moduleLogger)
	def _on_app_quit(self, checked = False):
		self.save_settings()

	@misc_utils.log_exception(_moduleLogger)
	def _on_child_close(self, obj = None):
		self._mainWindow = None

	@misc_utils.log_exception(_moduleLogger)
	def _on_toggle_fullscreen(self, checked = False):
		for window in self._walk_children():
			window.set_fullscreen(checked)

	@misc_utils.log_exception(_moduleLogger)
	def _on_log(self, checked = False):
		with open(constants._user_logpath_, "r") as f:
			logLines = f.xreadlines()
			log = "".join(logLines)
			self._clipboard.setText(log)

	@misc_utils.log_exception(_moduleLogger)
	def _on_quit(self, checked = False):
		self._close_windows()


class QErrorDisplay(object):

	def __init__(self):
		self._messages = []

		icon = QtGui.QIcon.fromTheme("gtk-dialog-error")
		self._severityIcon = icon.pixmap(32, 32)
		self._severityLabel = QtGui.QLabel()
		self._severityLabel.setPixmap(self._severityIcon)

		self._message = QtGui.QLabel()
		self._message.setText("Boo")

		icon = QtGui.QIcon.fromTheme("gtk-close")
		self._closeLabel = QtGui.QPushButton(icon, "")
		self._closeLabel.clicked.connect(self._on_close)

		self._controlLayout = QtGui.QHBoxLayout()
		self._controlLayout.addWidget(self._severityLabel)
		self._controlLayout.addWidget(self._message)
		self._controlLayout.addWidget(self._closeLabel)

		self._topLevelLayout = QtGui.QHBoxLayout()
		self._topLevelLayout.addLayout(self._controlLayout)
		self._hide_message()

	@property
	def toplevel(self):
		return self._topLevelLayout

	def push_message(self, message):
		self._messages.append(message)
		if 1 == len(self._messages):
			self._show_message(message)

	def push_exception(self):
		userMessage = str(sys.exc_info()[1])
		_moduleLogger.exception(userMessage)
		self.push_message(userMessage)

	def pop_message(self):
		del self._messages[0]
		if 0 == len(self._messages):
			self._hide_message()
		else:
			self._message.setText(self._messages[0])

	def _on_close(self, *args):
		self.pop_message()

	def _show_message(self, message):
		self._message.setText(message)
		self._severityLabel.show()
		self._message.show()
		self._closeLabel.show()

	def _hide_message(self):
		self._message.setText("")
		self._severityLabel.hide()
		self._message.hide()
		self._closeLabel.hide()


class QValueEntry(object):

	def __init__(self):
		self._widget = QtGui.QLineEdit("")
		maeqt.mark_numbers_preferred(self._widget)

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


class MainWindow(object):

	_plugin_search_paths = [
		"/opt/epi/lib/plugins/",
		"/usr/lib/ejpi/plugins/",
		os.path.join(os.path.dirname(__file__), "plugins/"),
	]

	_user_history = "%s/history.stack" % constants._data_path_

	def __init__(self, parent, app):
		self._app = app

		self._errorDisplay = QErrorDisplay()
		self._historyView = qhistory.QCalcHistory(self._errorDisplay)
		self._userEntry = QValueEntry()
		self._userEntry.entry.returnPressed.connect(self._on_push)
		self._userEntryLayout = QtGui.QHBoxLayout()
		self._userEntryLayout.addWidget(self._userEntry.toplevel)

		self._controlLayout = QtGui.QVBoxLayout()
		self._controlLayout.addLayout(self._errorDisplay.toplevel)
		self._controlLayout.addWidget(self._historyView.toplevel)
		self._controlLayout.addLayout(self._userEntryLayout)

		self._inputLayout = QtGui.QVBoxLayout()

		if maeqt.screen_orientation() == QtCore.Qt.Vertical:
			self._layout = QtGui.QVBoxLayout()
		else:
			self._layout = QtGui.QHBoxLayout()
		self._layout.addLayout(self._controlLayout)
		self._layout.addLayout(self._inputLayout)

		centralWidget = QtGui.QWidget()
		centralWidget.setLayout(self._layout)

		self._window = QtGui.QMainWindow(parent)
		self._window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
		#maeqt.set_autorient(self._window, True)
		maeqt.set_stackable(self._window, True)
		self._window.setWindowTitle("%s" % constants.__pretty_app_name__)
		self._window.setCentralWidget(centralWidget)
		self._window.destroyed.connect(self._on_close_window)

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

		if IS_MAEMO:
			#fileMenu = self._window.menuBar().addMenu("&File")

			#viewMenu = self._window.menuBar().addMenu("&View")

			self._window.addAction(self._copyItemAction)
			self._window.addAction(self._pasteItemAction)
			self._window.addAction(self._closeWindowAction)
			self._window.addAction(self._app.quitAction)
			self._window.addAction(self._app.fullscreenAction)
		else:
			fileMenu = self._window.menuBar().addMenu("&Units")
			fileMenu.addAction(self._closeWindowAction)
			fileMenu.addAction(self._app.quitAction)

			viewMenu = self._window.menuBar().addMenu("&View")
			viewMenu.addAction(self._app.fullscreenAction)

		self._window.addAction(self._app.logAction)

		self._constantPlugins = plugin_utils.ConstantPluginManager()
		self._constantPlugins.add_path(*self._plugin_search_paths)
		for pluginName in ["Builtins", "Trigonometry", "Computer", "Alphabet"]:
			try:
				pluginId = self._constantPlugins.lookup_plugin(pluginName)
				self._constantPlugins.enable_plugin(pluginId)
			except:
				_moduleLogger.info("Failed to load plugin %s" % pluginName)

		self._operatorPlugins = plugin_utils.OperatorPluginManager()
		self._operatorPlugins.add_path(*self._plugin_search_paths)
		for pluginName in ["Builtins", "Trigonometry", "Computer", "Alphabet"]:
			try:
				pluginId = self._operatorPlugins.lookup_plugin(pluginName)
				self._operatorPlugins.enable_plugin(pluginId)
			except:
				_moduleLogger.info("Failed to load plugin %s" % pluginName)

		self._keyboardPlugins = plugin_utils.KeyboardPluginManager()
		self._keyboardPlugins.add_path(*self._plugin_search_paths)
		self._activeKeyboards = []

		self._history = history.RpnCalcHistory(
			self._historyView,
			self._userEntry, self._errorDisplay,
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
		self._userEntryLayout.addLayout(entryKeyboard.toplevel)

		# Plugins
		self.enable_plugin(self._keyboardPlugins.lookup_plugin("Builtins"))
		#self.enable_plugin(self._keyboardPlugins.lookup_plugin("Trigonometry"))
		#self.enable_plugin(self._keyboardPlugins.lookup_plugin("Computer"))
		#self.enable_plugin(self._keyboardPlugins.lookup_plugin("Alphabet"))
		for keyboardData in self._activeKeyboards:
			keyboardData["pluginKeyboard"].hide()
		self._set_plugin_kb(0)

		self.set_fullscreen(self._app.fullscreenAction.isChecked())
		self._window.show()

	@property
	def window(self):
		return self._window

	def walk_children(self):
		return ()

	def show(self):
		self._window.show()
		for child in self.walk_children():
			child.show()

	def hide(self):
		for child in self.walk_children():
			child.hide()
		self._window.hide()

	def close(self):
		for child in self.walk_children():
			child.window.destroyed.disconnect(self._on_child_close)
			child.close()
		self._window.close()

	def set_fullscreen(self, isFullscreen):
		if isFullscreen:
			self._window.showFullScreen()
		else:
			self._window.showNormal()
		for child in self.walk_children():
			child.set_fullscreen(isFullscreen)

	def enable_plugin(self, pluginId):
		self._keyboardPlugins.enable_plugin(pluginId)
		pluginData = self._keyboardPlugins.plugin_info(pluginId)
		pluginName = pluginData[0]
		plugin = self._keyboardPlugins.keyboards[pluginName].construct_keyboard()
		pluginKeyboard = plugin.setup(self._history, self._handler)

		self._activeKeyboards.append({
			"pluginName": pluginName,
			"plugin": plugin,
			"pluginKeyboard": pluginKeyboard,
		})
		self._inputLayout.addLayout(pluginKeyboard.toplevel)

	def _set_plugin_kb(self, pluginIndex):
		plugin = self._activeKeyboards[pluginIndex]

		for keyboardData in self._activeKeyboards:
			if plugin["pluginName"] != keyboardData["pluginName"]:
				keyboardData["pluginKeyboard"].hide()

		# @todo self._pluginButton.set_label(plugin["pluginName"])
		pluginKeyboard = plugin["pluginKeyboard"]
		pluginKeyboard.show()

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
	def _on_copy(self, *args):
		eqNode = self._historyView.peek()
		resultNode = eqNode.simplify()
		self._app._clipboard.setText(str(resultNode))

	@misc_utils.log_exception(_moduleLogger)
	def _on_paste(self, *args):
		result = str(self._app._clipboard.text())
		self._userEntry.append(result)

	@misc_utils.log_exception(_moduleLogger)
	def _on_entry_direct(self, keys, modifiers):
		if "shift" in modifiers:
			keys = keys.upper()
		self._userEntry.append(keys)

	@misc_utils.log_exception(_moduleLogger)
	def _on_push(self, *args):
		self._history.push_entry()

	@misc_utils.log_exception(_moduleLogger)
	def _on_unpush(self, *args):
		self._historyView.unpush()

	@misc_utils.log_exception(_moduleLogger)
	def _on_entry_backspace(self, *args):
		self._userEntry.pop()

	@misc_utils.log_exception(_moduleLogger)
	def _on_entry_clear(self, *args):
		self._userEntry.clear()

	@misc_utils.log_exception(_moduleLogger)
	def _on_clear_all(self, *args):
		self._history.clear()

	@misc_utils.log_exception(_moduleLogger)
	def _on_close_window(self, checked = True):
		self._save_history()


def run():
	app = QtGui.QApplication([])
	handle = Calculator(app)
	qtpie.init_pies()
	return app.exec_()


if __name__ == "__main__":
	logging.basicConfig(level = logging.DEBUG)
	try:
		os.makedirs(constants._data_path_)
	except OSError, e:
		if e.errno != 17:
			raise

	val = run()
	sys.exit(val)
