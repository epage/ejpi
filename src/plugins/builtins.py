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
#factorial = operation.generate_function(math.factorial, "!", operation.Function.REP_POSTFIX, 1)

PLUGIN.register_operation("**", exponentiation)
PLUGIN.register_operation("abs", abs)
