#!/usr/bin/env python


import re
import weakref

from util import algorithms
import operation


__BASE_MAPPINGS = {
	"0x": 16,
	"0o": 8,
	"0b": 2,
}


_VARIABLE_VALIDATION_RE = re.compile("^[a-zA-Z0-9]+$")


def validate_variable_name(variableName):
	match = _VARIABLE_VALIDATION_RE.match(variableName)
	if match is None:
		raise RuntimeError("Invalid characters in '%s'" % variableName)


def parse_number(userInput):
	try:
		base = __BASE_MAPPINGS.get(userInput[0:2], 10)
		if base != 10:
			userInput = userInput[2:] # Remove prefix
		value = int(userInput, base)
		return value, base
	except ValueError:
		pass

	try:
		value = float(userInput)
		return value, 10
	except ValueError:
		pass

	try:
		value = complex(userInput)
		return value, 10
	except ValueError:
		pass

	raise ValueError('Cannot parse "%s" as a number' % userInput)


class AbstractHistory(object):
	"""
	Is it just me or is this class name begging for some jokes?
	"""

	def push(self, node):
		raise NotImplementedError

	def pop(self):
		raise NotImplementedError

	def unpush(self):
		node = self.pop()
		for child in node.get_children():
			self.push(child)

	def peek(self):
		raise NotImplementedError

	def clear(self):
		raise NotImplementedError

	def __len__(self):
		raise NotImplementedError

	def __iter__(self):
		raise NotImplementedError


class CalcHistory(AbstractHistory):

	def __init__(self):
		super(CalcHistory, self).__init__()
		self.__nodeStack = []

	def push(self, node):
		assert node is not None
		self.__nodeStack.append(node)
		return node

	def pop(self):
		popped = self.__nodeStack[-1]
		del self.__nodeStack[-1]
		return popped

	def peek(self):
		return self.__nodeStack[-1]

	def clear(self):
		self.__nodeStack = []

	def __len__(self):
		return len(self.__nodeStack)

	def __iter__(self):
		return self.__nodeStack[::-1]


class RpnCalcHistory(object):

	def __init__(self, history, entry, errorReporting, constants, operations):
		self.history = history
		self.history._parse_value = self._parse_value
		self.__entry = weakref.ref(entry)

		self.__errorReporter = errorReporting
		self.__constants = constants
		self.__operations = operations

		self.__serialRenderer = operation.render_number()

	@property
	def errorReporter(self):
		return self.__errorReporter

	@property
	def OPERATIONS(self):
		return self.__operations

	@property
	def CONSTANTS(self):
		return self.__constants

	def clear(self):
		self.history.clear()
		self.__entry().clear()

	def push_entry(self):
		value = self.__entry().get_value()

		valueNode = None
		if 0 < len(value):
			valueNode = self._parse_value(value)
			self.history.push(valueNode)

		self.__entry().clear()
		return valueNode

	def apply_operation(self, Node):
		try:
			self.push_entry()

			node = self._apply_operation(Node)
			return node
		except StandardError, e:
			self.errorReporter.push_exception()
			return None

	def serialize_stack(self):
		serialized = (
			stackNode.serialize(self.__serialRenderer)
			for stackNode in self.history
		)
		serialized = list(serialized)
		return serialized

	def deserialize_stack(self, data):
		for possibleNode in data:
			for nodeValue in possibleNode:
				if nodeValue in self.OPERATIONS:
					Node = self.OPERATIONS[nodeValue]
					self._apply_operation(Node)
				else:
					node = self._parse_value(nodeValue)
					self.history.push(node)

	def _parse_value(self, userInput):
		try:
			value, base = parse_number(userInput)
			return operation.Value(value, base)
		except ValueError:
			pass

		try:
			return self.CONSTANTS[userInput]
		except KeyError:
			pass

		validate_variable_name(userInput)
		return operation.Variable(userInput)

	def _apply_operation(self, Node):
		numArgs = Node.argumentCount

		if len(self.history) < numArgs:
			raise ValueError(
				"Not enough arguments.  The stack has %d but %s needs %d" % (
					len(self.history), Node.symbol, numArgs
				)
			)

		args = [arg for arg in algorithms.func_repeat(numArgs, self.history.pop)]
		args.reverse()

		try:
			node = Node(*args)
		except StandardError:
			for arg in args:
				self.history.push(arg)
			raise
		self.history.push(node)
		return node
