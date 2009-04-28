from __future__ import division

import os
import operator
import math

import operation

import sys
sys.path.append("../")
import plugin_utils


_MAP_FILE_PATH = os.path.join(os.path.dirname(__file__), "builtins.map")
PLUGIN = plugin_utils.PieKeyboardPluginFactory("Builtin", _MAP_FILE_PATH)

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
	def fact_func(num):
		return num * fact_func(num - 1)
factorial = operation.generate_function(math.factorial, "!", operation.Function.REP_POSTFIX, 1)
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
