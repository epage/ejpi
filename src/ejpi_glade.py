#!/usr/bin/python

"""
@todo Add preference file
	@li enable/disable plugins
	@li plugin search path
	@li Number format
	@li Current tab
@todo Expand operations to support
	@li mathml then to cairo?
	@li cairo directly?
@todo Expanded copy/paste (Unusure how far to go)
	@li Copy formula, value, serialized, mathml, latex?
	@li Paste serialized, value?

Some useful things on Maemo
@li http://maemo.org/api_refs/4.1/libosso-2.16-1/group__Statesave.html
@li http://maemo.org/api_refs/4.1/libosso-2.16-1/group__Autosave.html
"""


from __future__ import with_statement


import sys
import gc
import os
import string
import warnings

import gtk
import gtk.glade

try:
	import hildon
except ImportError:
	hildon = None

from libraries import gtkpie
from libraries import gtkpieboard
import plugin_utils
import history
import gtkhistory


PLUGIN_SEARCH_PATHS = [
	os.path.join(os.path.dirname(__file__), "plugins/"),
]


class ValueEntry(object):

	def __init__(self, widget):
		self.__widget = widget
		self.__actualEntryDisplay = ""

	def get_value(self):
		value = self.__actualEntryDisplay.strip()
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
		self.__actualEntryDisplay = value
		self.__widget.set_text(value)

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


class ErrorDisplay(history.ErrorReporting):

	def __init__(self, widgetTree):
		super(ErrorDisplay, self).__init__()
		self.__errorBox = widgetTree.get_widget("errorEventBox")
		self.__errorDescription = widgetTree.get_widget("errorDescription")
		self.__errorClose = widgetTree.get_widget("errorClose")
		self.__parentBox = self.__errorBox.get_parent()

		self.__errorBox.connect("button_release_event", self._on_close)

		self.__messages = []
		self.__parentBox.remove(self.__errorBox)

	def push_message(self, message):
		if 0 < len(self.__messages):
			self.__messages.append(message)
		else:
			self.__show_message(message)

	def pop_message(self):
		if 0 < len(self.__messages):
			self.__show_message(self.__messages[0])
			del self.__messages[0]
		else:
			self.__hide_message()

	def _on_close(self, *args):
		self.pop_message()

	def __show_message(self, message):
		self.__errorDescription.set_text(message)
		self.__parentBox.pack_start(self.__errorBox, False, False)
		self.__parentBox.reorder_child(self.__errorBox, 1)

	def __hide_message(self):
		self.__errorDescription.set_text("")
		self.__parentBox.remove(self.__errorBox)


class Calculator(object):

	__pretty_app_name__ = "e**(j pi) + 1 = 0"
	__app_name__ = "ejpi"
	__version__ = "0.9.0"
	__app_magic__ = 0xdeadbeef

	_glade_files = [
		'/usr/lib/ejpi/ejpi.glade',
		os.path.join(os.path.dirname(__file__), "ejpi.glade"),
		os.path.join(os.path.dirname(__file__), "../lib/ejpi.glade"),
	]

	_plugin_search_paths = [
		"/usr/lib/ejpi/plugins/",
		os.path.join(os.path.dirname(__file__), "plugins/"),
	]

	_user_data = os.path.expanduser("~/.%s/" % __app_name__)
	_user_settings = "%s/settings.ini" % _user_data
	_user_history = "%s/history.stack" % _user_data

	def __init__(self):
		self.__constantPlugins = plugin_utils.ConstantPluginManager()
		self.__constantPlugins.add_path(*self._plugin_search_paths)
		for pluginName in ["Builtin", "Trigonometry", "Computer", "Alphabet"]:
			try:
				pluginId = self.__constantPlugins.lookup_plugin(pluginName)
				self.__constantPlugins.enable_plugin(pluginId)
			except:
				warnings.warn("Failed to load plugin %s" % pluginName)

		self.__operatorPlugins = plugin_utils.OperatorPluginManager()
		self.__operatorPlugins.add_path(*self._plugin_search_paths)
		for pluginName in ["Builtin", "Trigonometry", "Computer", "Alphabet"]:
			try:
				pluginId = self.__operatorPlugins.lookup_plugin(pluginName)
				self.__operatorPlugins.enable_plugin(pluginId)
			except:
				warnings.warn("Failed to load plugin %s" % pluginName)

		self.__keyboardPlugins = plugin_utils.KeyboardPluginManager()
		self.__keyboardPlugins.add_path(*self._plugin_search_paths)
		self.__activeKeyboards = {}

		for path in self._glade_files:
			if os.path.isfile(path):
				self._widgetTree = gtk.glade.XML(path)
				break
		else:
			self.display_error_message("Cannot find ejpi.glade")
			gtk.main_quit()
		try:
			os.makedirs(self._user_data)
		except OSError, e:
			if e.errno != 17:
				raise

		self._clipboard = gtk.clipboard_get()
		self.__window = self._widgetTree.get_widget("mainWindow")

		global hildon
		self._app = None
		self._isFullScreen = False
		if hildon is not None and self.__window is gtk.Window:
			warnings.warn("Hildon installed but glade file not updated to work with hildon", UserWarning, 2)
			hildon = None
		elif hildon is not None:
			self._app = hildon.Program()
			self.__window = hildon.Window()
			self._widgetTree.get_widget("mainLayout").reparent(self.__window)
			self._app.add_window(self.__window)
			hildon.hildon_helper_set_thumb_scrollbar(self._widgetTree.get_widget('scrollingHistory'), True)

			gtkMenu = self._widgetTree.get_widget("mainMenubar")
			menu = gtk.Menu()
			for child in gtkMenu.get_children():
				child.reparent(menu)
			self.__window.set_menu(menu)
			gtkMenu.destroy()

			self.__window.connect("key-press-event", self._on_key_press)
			self.__window.connect("window-state-event", self._on_window_state_change)
		else:
			warnings.warn("No Hildon", UserWarning, 2)

		self.__errorDisplay = ErrorDisplay(self._widgetTree)
		self.__userEntry = ValueEntry(self._widgetTree.get_widget("entryView"))
		self.__stackView = self._widgetTree.get_widget("historyView")

		self.__historyStore = gtkhistory.GtkCalcHistory(self.__stackView)
		self.__history = history.RpnCalcHistory(
			self.__historyStore,
			self.__userEntry, self.__errorDisplay,
			self.__constantPlugins.constants, self.__operatorPlugins.operators
		)
		self.__load_history()

		self.__sliceStyle = gtkpie.generate_pie_style(gtk.Button())
		self.__handler = gtkpieboard.KeyboardHandler(self._on_entry_direct)
		self.__handler.register_command_handler("push", self._on_push)
		self.__handler.register_command_handler("unpush", self._on_unpush)
		self.__handler.register_command_handler("backspace", self._on_entry_backspace)
		self.__handler.register_command_handler("clear", self._on_entry_clear)

		builtinKeyboardId = self.__keyboardPlugins.lookup_plugin("Builtin")
		self.__keyboardPlugins.enable_plugin(builtinKeyboardId)
		self.__builtinPlugin = self.__keyboardPlugins.keyboards["Builtin"].construct_keyboard()
		self.__builtinKeyboard = self.__builtinPlugin.setup(self.__history, self.__sliceStyle, self.__handler)
		self._widgetTree.get_widget("functionLayout").pack_start(self.__builtinKeyboard)
		self._widgetTree.get_widget("functionLayout").reorder_child(self.__builtinKeyboard, 0)
		self.enable_plugin(self.__keyboardPlugins.lookup_plugin("Trigonometry"))
		self.enable_plugin(self.__keyboardPlugins.lookup_plugin("Computer"))
		self.enable_plugin(self.__keyboardPlugins.lookup_plugin("Alphabet"))

		callbackMapping = {
			"on_calculator_quit": self._on_close,
			"on_paste": self._on_paste,
			"on_clear_history": self._on_clear_all,
			"on_about": self._on_about_activate,
		}
		self._widgetTree.signal_autoconnect(callbackMapping)

		if self.__window:
			if hildon is None:
				self.__window.set_title("%s" % self.__pretty_app_name__)
			self.__window.connect("destroy", self._on_close)
			self.__window.show_all()

		try:
			import osso
		except ImportError:
			osso = None

		self._osso = None
		if osso is not None:
			self._osso = osso.Context(Calculator.__app_name__, Calculator.__version__, False)
			device = osso.DeviceState(self._osso)
			device.set_device_state_callback(self._on_device_state_change, 0)
		else:
			warnings.warn("No OSSO", UserWarning, 2)

	def display_error_message(self, msg):
		error_dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, msg)

		def close(dialog, response, editor):
			editor.about_dialog = None
			dialog.destroy()
		error_dialog.connect("response", close, self)
		error_dialog.run()

	def enable_plugin(self, pluginId):
		self.__keyboardPlugins.enable_plugin(pluginId)
		pluginData = self.__keyboardPlugins.plugin_info(pluginId)
		pluginName = pluginData[0]
		plugin = self.__keyboardPlugins.keyboards[pluginName].construct_keyboard()
		pluginKeyboard = plugin.setup(self.__history, self.__sliceStyle, self.__handler)

		keyboardTabs = self._widgetTree.get_widget("pluginKeyboards")
		keyboardTabs.append_page(pluginKeyboard, gtk.Label(pluginName))
		keyboardPageNum = keyboardTabs.page_num(pluginKeyboard)
		assert keyboardPageNum not in self.__activeKeyboards
		self.__activeKeyboards[keyboardPageNum] = {
			"pluginName": pluginName,
			"plugin": plugin,
			"pluginKeyboard": pluginKeyboard,
		}

	def __load_history(self):
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
		self.__history.deserialize_stack(serialized)

	def __save_history(self):
		serialized = self.__history.serialize_stack()
		with open(self._user_history, "w") as f:
			for lineData in serialized:
				line = " ".join(data for data in lineData)
				f.write("%s\n" % line)

	def _on_device_state_change(self, shutdown, save_unsaved_data, memory_low, system_inactivity, message, userData):
		"""
		For system_inactivity, we have no background tasks to pause

		@note Hildon specific
		"""
		if memory_low:
			gc.collect()

		if save_unsaved_data or shutdown:
			self.__save_history()

	def _on_window_state_change(self, widget, event, *args):
		"""
		@note Hildon specific
		"""
		if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
			self._isFullScreen = True
		else:
			self._isFullScreen = False

	def _on_close(self, *args, **kwds):
		try:
			self.__save_history()
		finally:
			gtk.main_quit()

	def _on_paste(self, *args):
		contents = self._clipboard.wait_for_text()
		self.__userEntry.append(contents)

	def _on_key_press(self, widget, event, *args):
		"""
		@note Hildon specific
		"""
		if event.keyval == gtk.keysyms.F6:
			if self._isFullScreen:
				self.__window.unfullscreen()
			else:
				self.__window.fullscreen()

	def _on_push(self, *args):
		self.__history.push_entry()

	def _on_unpush(self, *args):
		self.__historyStore.unpush()

	def _on_entry_direct(self, keys, modifiers):
		if "shift" in modifiers:
			keys = keys.upper()
		self.__userEntry.append(keys)

	def _on_entry_backspace(self, *args):
		self.__userEntry.pop()

	def _on_entry_clear(self, *args):
		self.__userEntry.clear()

	def _on_clear_all(self, *args):
		self.__history.clear()

	def _on_about_activate(self, *args):
		dlg = gtk.AboutDialog()
		dlg.set_name(self.__pretty_app_name__)
		dlg.set_version(self.__version__)
		dlg.set_copyright("Copyright 2008 - LGPL")
		dlg.set_comments("")
		dlg.set_website("")
		dlg.set_authors([""])
		dlg.run()
		dlg.destroy()


def run_doctest():
	import doctest

	failureCount, testCount = doctest.testmod()
	if not failureCount:
		print "Tests Successful"
		sys.exit(0)
	else:
		sys.exit(1)


def run_calculator():
	gtk.gdk.threads_init()

	gtkpie.IMAGES.add_path(os.path.join(os.path.dirname(__file__), "libraries/images"), )
	if hildon is not None:
		gtk.set_application_name(Calculator.__pretty_app_name__)
	handle = Calculator()
	gtk.main()


class DummyOptions(object):

	def __init__(self):
		self.test = False


if __name__ == "__main__":
	if len(sys.argv) > 1:
		try:
			import optparse
		except ImportError:
			optparse = None

		if optparse is not None:
			parser = optparse.OptionParser()
			parser.add_option("-t", "--test", action="store_true", dest="test", help="Run tests")
			(commandOptions, commandArgs) = parser.parse_args()
	else:
		commandOptions = DummyOptions()
		commandArgs = []

	if commandOptions.test:
		run_doctest()
	else:
		run_calculator()
