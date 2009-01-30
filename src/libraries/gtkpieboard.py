#!/usr/bin/env python


from __future__ import division

import copy
import warnings

import gobject
import gtk

import gtkpie


class PieKeyboard(gtk.Table):

	def __init__(self, style, rows, columns, alternateStyles=True):
		super(PieKeyboard, self).__init__(rows, columns, homogeneous=True)

		self.__cells = {}
		for row in xrange(rows):
			for column in xrange(columns):
				popup = gtkpie.PiePopup(
					self._alternate_style(row, column, style) if alternateStyles else style
				)
				self.attach(popup, column, column+1, row, row+1)
				self.__cells[(row, column)] = popup

	def add_slice(self, row, column, slice, direction):
		pie = self.__cells[(row, column)]
		pie.add_slice(slice, direction)

	def add_slices(self, row, column, slices):
		pie = self.__cells[(row, column)]
		for direction, slice in slices.iteritems():
			pie.add_slice(slice, direction)

	def get_pie(self, row, column):
		return self.__cells[(row, column)]

	@classmethod
	def _alternate_style(cls, row, column, style):
		i = row + column
		isEven = (i % 2) == 0

		if not isEven:
			return style

		altStyle = copy.copy(style)
		selected = altStyle[True]
		notSelected = altStyle[False]
		altStyle[False] = selected
		altStyle[True] = notSelected
		return altStyle


class KeyboardModifier(object):

	def __init__(self, name):
		self.name = name
		self.lock = False
		self.once = False

	@property
	def isActive(self):
		return self.lock or self.once

	def on_toggle_lock(self, *args, **kwds):
		self.lock = not self.lock

	def on_toggle_once(self, *args, **kwds):
		self.once = not self.once

	def reset_once(self):
		self.once = False


gobject.type_register(PieKeyboard)


def parse_keyboard_data(text):
	return eval(text)


def load_keyboard(keyboardName, dataTree, keyboard, keyboardHandler):
	for (row, column), pieData in dataTree.iteritems():
		showAllSlices = pieData["showAllSlices"]
		keyboard.get_pie(row, column).showAllSlices = showAllSlices
		for direction, directionName in enumerate(gtkpie.PieSlice.SLICE_DIRECTION_NAMES):
			if directionName not in pieData:
				continue
			sliceName = "%s-(%d, %d)-%s" % (keyboardName, row, column, directionName)

			sliceData = pieData[directionName]
			sliceAction = sliceData["action"]
			sliceType = sliceData["type"]
			if sliceType == "text":
				text = sliceData["text"]
				# font = sliceData["font"] # @TODO
				slice = gtkpie.TextLabelPieSlice(text, handler=keyboardHandler)
			elif sliceType == "image":
				path = sliceData["path"]
				slice = gtkpie.ImageLabelPieSlice(path, handler=keyboardHandler)

			slice.name = sliceName
			keyboard.add_slice(row, column, slice, direction)
			keyboardHandler.map_slice_action(slice, sliceAction)


class KeyboardHandler(object):

	def __init__(self, keyhandler):
		self.__keyhandler = keyhandler
		self.__commandHandlers = {}
		self.__modifiers = {}
		self.__sliceActions = {}

		self.register_modifier("Shift")
		self.register_modifier("Super")
		self.register_modifier("Control")
		self.register_modifier("Alt")

	def register_command_handler(self, command, handler):
		#@todo Make this handle multiple handlers or switch to gobject events
		self.__commandHandlers["[%s]" % command] = handler

	def unregister_command_handler(self, command):
		#@todo Make this handle multiple handlers or switch to gobject events
		del self.__commandHandlers["[%s]" % command]

	def register_modifier(self, modifierName):
		mod = KeyboardModifier(modifierName)
		self.register_command_handler(modifierName, mod.on_toggle_lock)
		self.__modifiers["<%s>" % modifierName] = mod

	def unregister_modifier(self, modifierName):
		self.unregister_command_handler(modifierName)
		del self.__modifiers["<%s>" % modifierName]

	def map_slice_action(self, slice, action):
		self.__sliceActions[slice.name] = action

	def __call__(self, pie, slice, direction):
		try:
			action = self.__sliceActions[slice.name]
		except KeyError:
			return

		activeModifiers = [
			mod.name
			for mod in self.__modifiers.itervalues()
				if mod.isActive
		]

		needResetOnce = False
		if action.startswith("[") and action.endswith("]"):
			commandName = action[1:-1]
			if action in self.__commandHandlers:
				self.__commandHandlers[action](commandName, activeModifiers)
				needResetOnce = True
			else:
				warnings.warn("Unknown command: [%s]" % commandName)
		elif action.startswith("<") and action.endswith(">"):
			modName = action[1:-1]
			for mod in self.__modifiers.itervalues():
				if mod.name == modName:
					mod.on_toggle_once()
					break
			else:
				warnings.warn("Unknown modifier: <%s>" % modName)
		else:
			self.__keyhandler(action, activeModifiers)
			needResetOnce = True

		if needResetOnce:
			for mod in self.__modifiers.itervalues():
				mod.reset_once()
