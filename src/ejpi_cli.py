#!/usr/bin/env python

import os

import plugin_utils
import history


PLUGIN_SEARCH_PATHS = [
	os.path.join(os.path.dirname(__file__), "plugins/"),
]


OPERATIONS = {}

CONSTANTS = {}


class CliEntry(object):

	def __init__(self):
		self.value = ""

	def set_value(self, value):
		self.value = value

	def get_value(self):
		return self.value

	def clear(self):
		self.value = ""


def parse_command(userInput):
	return OPERATIONS[userInput.strip()]


def ambiguous_parse(calc, userInput):
	try:
		Node = parse_command(userInput)
		calc.apply_operation(Node)
		return True
	except KeyError:
		return False


def repl():
	entry = CliEntry()
	stack = history.CalcHistory()
	rpnCalc = history.RpnCalcHistory(
		stack,
		entry, history.ErrorWarning(),
		CONSTANTS, OPERATIONS
	)
	while True:
		userInput = raw_input(">")
		isUsed = ambiguous_parse(rpnCalc, userInput)
		if not isUsed:
			entry.set_value(userInput)
			rpnCalc.push_entry()

		if 0 < len(stack):
			node = stack.peek()
			print "\t= %s" % str(node)
			print "\t~= %s" % str(node.simplify(**CONSTANTS))


def main():
	constantPlugins = plugin_utils.ConstantPluginManager()
	constantPlugins.add_path(*PLUGIN_SEARCH_PATHS)
	constantPlugins.enable_plugin(constantPlugins.lookup_plugin("Builtin"))
	CONSTANTS.update(constantPlugins.constants)

	operatorPlugins = plugin_utils.OperatorPluginManager()
	operatorPlugins.add_path(*PLUGIN_SEARCH_PATHS)
	operatorPlugins.enable_plugin(operatorPlugins.lookup_plugin("Builtin"))
	OPERATIONS.update(operatorPlugins.operators)

	repl()

if __name__ == "__main__":
	main()
