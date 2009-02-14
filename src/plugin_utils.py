#!/usr/bin/env python


from __future__ import with_statement


import sys
import os
import inspect
import ConfigParser

from libraries import gtkpieboard
from libraries.recipes import io
import operation


class CommandStackHandler(object):

	def __init__(self, stack, command, operator):
		self.command = command

		self.__stack = stack
		self.__operator = operator

	def handler(self, commandName, activeModifiers):
		self.__stack.apply_operation(self.__operator)


class PieKeyboardPlugin(object):

	def __init__(self, name, factory):
		self.name = name
		self.factory = factory
		self.__handler = None

	def setup(self, calcStack, style, boardHandler):
		self.__handler = boardHandler

		with open(self.factory.mapFile, "r") as mapfile:
			boardTree = gtkpieboard.parse_keyboard_data("\n".join(mapfile.readlines()))

		rows, columns = boardTree["dimensions"]
		keyboardName = boardTree["name"]
		keyTree = boardTree["keys"]

		keyboard = gtkpieboard.PieKeyboard(style, rows, columns)
		gtkpieboard.load_keyboard(keyboardName, keyTree, keyboard, self.__handler)

		for commandName, operator in self.factory.commands.iteritems():
			handler = CommandStackHandler(calcStack, commandName, operator)
			self.__handler.register_command_handler(commandName, handler.handler)

		return keyboard

	def tear_down(self):
		for commandName, operator in self.factory.commands.itervalues():
			self.__handler.unregister_command_handler(commandName)

		# Leave our self completely unusable
		self.name = None
		self.factory = None
		self.__handler = None


class PieKeyboardPluginFactory(object):

	def __init__(self, pluginName, keyboardMapFile):
		self.name = pluginName
		self.mapFile = keyboardMapFile
		self.commands = {}

	def register_operation(self, commandName, operator):
		self.commands[commandName] = operator

	def construct_keyboard(self):
		plugin = PieKeyboardPlugin(self.name, self)
		return plugin


class PluginManager(object):

	def __init__(self, pluginType):
		self._pluginType = pluginType
		self._plugins = {}
		self._enabled = set()

		self.__searchPaths = []

	def add_path(self, *paths):
		self.__searchPaths.append(paths)
		self.__scan(paths)

	def rescan(self):
		self._plugins = {}
		self.__scan(self.__searchPaths)

	def plugin_info(self, pluginId):
		pluginData = self._plugins[pluginId]
		return pluginData["name"], pluginData["version"], pluginData["description"]

	def plugins(self):
		for id, pluginData in self._plugins.iteritems():
			yield id, pluginData["name"], pluginData["version"], pluginData["description"]

	def enable_plugin(self, id):
		assert id in self._plugins, "Can't find plugin %s in the search path %r" % (id, self.__searchPaths)
		self._load_module(id)
		self._enabled.add(id)

	def disable_plugin(self, id):
		self._enabled.remove(id)

	def lookup_plugin(self, name):
		for id, data in self._plugins.iteritems():
			if data["name"] == name:
				return id

	def _load_module(self, id):
		pluginData = self._plugins[id]

		if "module" not in pluginData:
			pluginPath = pluginData["pluginpath"]
			dataPath = pluginData["datapath"]
			assert dataPath.endswith(".ini")

			dataPath = io.relpath(pluginPath, dataPath)
			pythonPath = dataPath[0:-len(".ini")]
			modulePath = fspath_to_ipath(pythonPath, "")

			sys.path.append(pluginPath)
			try:
				module = __import__(modulePath)
			finally:
				sys.path.remove(pluginPath)
			pluginData["module"] = module
		else:
			# @todo Decide if want to call reload
			module = pluginData["module"]

		return module

	def __scan(self, paths):
		pluginDataFiles = find_plugins(paths, ".ini")

		for pluginPath, pluginDataFile in pluginDataFiles:
			config = ConfigParser.SafeConfigParser()
			config.read(pluginDataFile)

			name = config.get(self._pluginType, "name")
			version = config.get(self._pluginType, "version")
			description = config.get(self._pluginType, "description")

			self._plugins[pluginDataFile] = {
				"name": name,
				"version": version,
				"description": description,
				"datapath": pluginDataFile,
				"pluginpath": pluginPath,
			}


class ConstantPluginManager(PluginManager):

	def __init__(self):
		super(ConstantPluginManager, self).__init__("Constants")
		self.__constants = {}
		self.__constantsCache = {}
		self.__isCacheDirty = False

	def enable_plugin(self, id):
		super(ConstantPluginManager, self).enable_plugin(id)
		self.__constants[id] = dict(
			extract_instance_from_plugin(self._plugins[id]["module"], operation.Operation)
		)
		self.__isCacheDirty = True

	def disable_plugin(self, id):
		super(ConstantPluginManager, self).disable_plugin(id)
		self.__isCacheDirty = True

	@property
	def constants(self):
		if self.__isCacheDirty:
			self.__update_cache()
		return self.__constantsCache

	def __update_cache(self):
		self.__constantsCache.clear()
		for pluginId in self._enabled:
			self.__constantsCache.update(self.__constants[pluginId])
		self.__isCacheDirty = False


class OperatorPluginManager(PluginManager):

	def __init__(self):
		super(OperatorPluginManager, self).__init__("Operator")
		self.__operators = {}
		self.__operatorsCache = {}
		self.__isCacheDirty = False

	def enable_plugin(self, id):
		super(OperatorPluginManager, self).enable_plugin(id)
		operators = (
			extract_class_from_plugin(self._plugins[id]["module"], operation.Operation)
		)
		self.__operators[id] = dict(
			(op.symbol, op)
			for op in operators
		)
		self.__isCacheDirty = True

	def disable_plugin(self, id):
		super(OperatorPluginManager, self).disable_plugin(id)
		self.__isCacheDirty = True

	@property
	def operators(self):
		if self.__isCacheDirty:
			self.__update_cache()
		return self.__operatorsCache

	def __update_cache(self):
		self.__operatorsCache.clear()
		for pluginId in self._enabled:
			self.__operatorsCache.update(self.__operators[pluginId])
		self.__isCacheDirty = False


class KeyboardPluginManager(PluginManager):

	def __init__(self):
		super(KeyboardPluginManager, self).__init__("Keyboard")
		self.__keyboards = {}
		self.__keyboardsCache = {}
		self.__isCacheDirty = False

	def enable_plugin(self, id):
		super(KeyboardPluginManager, self).enable_plugin(id)
		keyboards = (
			extract_instance_from_plugin(self._plugins[id]["module"], PieKeyboardPluginFactory)
		)
		self.__keyboards[id] = dict(
			(board.name, board)
			for boardVariableName, board in keyboards
		)
		self.__isCacheDirty = True

	def disable_plugin(self, id):
		super(KeyboardPluginManager, self).disable_plugin(id)
		self.__isCacheDirty = True

	@property
	def keyboards(self):
		if self.__isCacheDirty:
			self.__update_cache()
		return self.__keyboardsCache

	def __update_cache(self):
		self.__keyboardsCache.clear()
		for pluginId in self._enabled:
			self.__keyboardsCache.update(self.__keyboards[pluginId])
		self.__isCacheDirty = False


def fspath_to_ipath(fsPath, extension = ".py"):
	"""
	>>> fspath_to_ipath("user/test/file.py")
	'user.test.file'
	"""
	assert fsPath.endswith(extension)
	CURRENT_DIR = "."+os.sep
	CURRENT_DIR_LEN = len(CURRENT_DIR)
	if fsPath.startswith(CURRENT_DIR):
		fsPath = fsPath[CURRENT_DIR_LEN:]

	if extension:
		fsPath = fsPath[0:-len(extension)]
	parts = fsPath.split(os.sep)
	return ".".join(parts)


def find_plugins(searchPaths, fileType=".py"):
	pythonFiles = (
		(path, os.path.join(root, file))
		for path in searchPaths
		for root, dirs, files in os.walk(path)
		for file in files
			if file.endswith(fileType)
	)
	return pythonFiles


def extract_class_from_plugin(pluginModule, cls):
	try:
		for item in pluginModule.__dict__.itervalues():
			try:
				if cls in inspect.getmro(item):
					yield item
			except AttributeError:
				pass
	except AttributeError:
		pass


def extract_instance_from_plugin(pluginModule, cls):
	try:
		for name, item in pluginModule.__dict__.iteritems():
			try:
				if isinstance(item, cls):
					yield name, item
			except AttributeError:
				pass
	except AttributeError:
		pass
