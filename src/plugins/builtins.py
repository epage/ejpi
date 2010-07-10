from __future__ import division

import os
import operator
import math

import operation

import sys
sys.path.append("../")
import plugin_utils

_NAME = "Builtins"
_MAP = {
	"name": _NAME,
	"keys": {
		(0, 0): {
			"CENTER": {"action": "7", "type": "text", "text": "7", },
			"showAllSlices": True,
		},
		(0, 1): {
			"CENTER": {"action": "8", "type": "text", "text": "8", },
			"SOUTH": {"action": "[**]", "type": "text", "text": "**", },
			"EAST": {"action": "[sq]", "type": "text", "text": "sq", },
			"WEST": {"action": "[sqrt]", "type": "text", "text": "sqrt", },
			"showAllSlices": False,
		},
		(0, 2): {
			"CENTER": {"action": "9", "type": "text", "text": "9", },
			"showAllSlices": True,
		},
		(1, 0): {
			"CENTER": {"action": "4", "type": "text", "text": "4", },
			"showAllSlices": True,
		},
		(1, 1): {
			"CENTER": {"action": "5", "type": "text", "text": "5", },
			"EAST": {"action": "[+]", "type": "text", "text": "+", },
			"WEST": {"action": "[-]", "type": "text", "text": "-", },
			"NORTH": {"action": "[*]", "type": "text", "text": "*", },
			"SOUTH": {"action": "[/]", "type": "text", "text": "/", },
			"showAllSlices": True,
		},
		(1, 2): {
			"CENTER": {"action": "6", "type": "text", "text": "6", },
			"showAllSlices": True,
		},
		(2, 0): {
			"CENTER": {"action": "1", "type": "text", "text": "1", },
			"EAST": {"action": "0", "type": "text", "text": "0", },
			"showAllSlices": True,
		},
		(2, 1): {
			"CENTER": {"action": "2", "type": "text", "text": "2", },
			"EAST": {"action": "[abs]", "type": "text", "text": "abs", },
			"NORTH": {"action": ".", "type": "text", "text": ".", },
			"WEST": {"action": "[+-]", "type": "text", "text": "+/-", },
			"showAllSlices": True,
		},
		(2, 2): {
			"CENTER": {"action": "3", "type": "text", "text": "3", },
			"NORTH": {"action": "[!]", "type": "text", "text": "!", },
			"WEST": {"action": "j", "type": "text", "text": "j", },
			"showAllSlices": True,
		},
	},
}
PLUGIN = plugin_utils.PieKeyboardPluginFactory(_NAME, _MAP, [])

addition = operation.generate_function(operator.add, "+", operation.Function.REP_INFIX, 2)
subtraction = operation.generate_function(operator.sub, "-", operation.Function.REP_INFIX, 2)
multiplication = operation.generate_function(operator.mul, "*", operation.Function.REP_INFIX, 2)
trueDivision = operation.generate_function(operator.truediv, "/", operation.Function.REP_INFIX, 2)

PLUGIN.register_operation("+", addition)
PLUGIN.register_operation("-", subtraction)
PLUGIN.register_operation("*", multiplication)
PLUGIN.register_operation("/", trueDivision)

exponentiation = operation.generate_function(operator.pow, "**", operation.Function.REP_INFIX, 2)
abs = operation.generate_function(operator.abs, "abs", operation.Function.REP_FUNCTION, 1)
try:
	fact_func = math.factorial
except AttributeError:
	def fact_func(self, num):
		if num <= 0:
			return 1
		return num * fact_func(self, num - 1)
factorial = operation.generate_function(fact_func, "!", operation.Function.REP_POSTFIX, 1)
negate = operation.generate_function(operator.neg, "+-", operation.Function.REP_PREFIX, 1)
square = operation.generate_function((lambda self, x: x ** 2), "sq", operation.Function.REP_FUNCTION, 1)
square_root = operation.generate_function((lambda self, x: x ** 0.5), "sqrt", operation.Function.REP_FUNCTION, 1)

# @todo Possibly make a graphic for this of x^y
PLUGIN.register_operation("**", exponentiation)
PLUGIN.register_operation("abs", abs)
PLUGIN.register_operation("!", factorial)
PLUGIN.register_operation("+-", negate)
PLUGIN.register_operation("sq", square)
PLUGIN.register_operation("sqrt", square_root)
