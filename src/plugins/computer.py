from __future__ import division

import os
import operator
import math

import operation

import sys
sys.path.append("../")
import plugin_utils


_MAP_FILE_PATH = os.path.join(os.path.dirname(__file__), "computer.map")
PLUGIN = plugin_utils.PieKeyboardPluginFactory("Computer", _MAP_FILE_PATH)

hex = operation.change_base(16, "hex")
oct = operation.change_base(8, "oct")
dec = operation.change_base(10, "dec")
ceil = operation.generate_function(math.ceil, "ceil", operation.Function.REP_FUNCTION, 1)
floor = operation.generate_function(math.floor, "floor", operation.Function.REP_FUNCTION, 1)

PLUGIN.register_operation("hex", hex)
PLUGIN.register_operation("oct", oct)
PLUGIN.register_operation("dec", dec)
PLUGIN.register_operation("ceil", ceil)
PLUGIN.register_operation("floor", floor)

floorDivision = operation.generate_function(operator.floordiv, "//", operation.Function.REP_INFIX, 2)
modulo = operation.generate_function(operator.mod, "%", operation.Function.REP_INFIX, 2)

PLUGIN.register_operation("//", floorDivision)
PLUGIN.register_operation("%", modulo)

bitAnd = operation.generate_function(operator.and_, "&", operation.Function.REP_INFIX, 2)
bitOr = operation.generate_function(operator.or_, "|", operation.Function.REP_INFIX, 2)
bitXor = operation.generate_function(operator.xor, "^", operation.Function.REP_INFIX, 2)
bitInvert = operation.generate_function(operator.invert, "~", operation.Function.REP_PREFIX, 1)

PLUGIN.register_operation("&", bitAnd)
PLUGIN.register_operation("|", bitOr)
PLUGIN.register_operation("^", bitXor)
PLUGIN.register_operation("~", bitInvert)
