from __future__ import division

import os
import operator
import math

import operation

import sys
sys.path.append("../")
import plugin_utils


_NAME = "Computer"
_ICON = "computer.png"
_MAP = {
	"name": _NAME,
	"keys": {
		(0, 0): {
			"CENTER": {"action": "7", "type": "text", "text": "7", },
			"SOUTH": {"action": "d", "type": "text", "text": "D", },
			"showAllSlices": False,
		},
		(0, 1): {
			"CENTER": {"action": "8", "type": "text", "text": "8", },
			"SOUTH": {"action": "e", "type": "text", "text": "E", },
			"showAllSlices": False,
		},
		(0, 2): {
			"CENTER": {"action": "9", "type": "text", "text": "9", },
			"SOUTH": {"action": "f", "type": "text", "text": "F", },
			"showAllSlices": False,
		},
		(1, 0): {
			"CENTER": {"action": "4", "type": "text", "text": "4", },
			"NORTH_EAST": {"action": "0o", "type": "text", "text": "0o", },
			"EAST": {"action": "0x", "type": "text", "text": "0x", },
			"SOUTH_EAST": {"action": "0b", "type": "text", "text": "0b", },
			"showAllSlices": True,
		},
		(1, 1): {
			"CENTER": {"action": "5", "type": "text", "text": "5", },
			"NORTH": {"action": "[&]", "type": "text", "text": "and", },
			"WEST": {"action": "[|]", "type": "text", "text": "or", },
			"SOUTH": {"action": "[~]", "type": "text", "text": "not", },
			"EAST": {"action": "[^]", "type": "text", "text": "xor", },
			"showAllSlices": True,
		},
		(1, 2): {
			"CENTER": {"action": "6", "type": "text", "text": "6", },
			"NORTH_WEST": {"action": "[oct]", "type": "text", "text": "-> oct", },
			"WEST": {"action": "[dec]", "type": "text", "text": "-> dec", },
			"SOUTH_WEST": {"action": "[hex]", "type": "text", "text": "-> hex", },
			"showAllSlices": True,
		},
		(2, 0): {
			"CENTER": {"action": "1", "type": "text", "text": "1", },
			"NORTH": {"action": "a", "type": "text", "text": "A", },
			"EAST": {"action": "0", "type": "text", "text": "0", },
			"showAllSlices": False,
		},
		(2, 1): {
			"CENTER": {"action": "2", "type": "text", "text": "2", },
			"NORTH": {"action": "b", "type": "text", "text": "B", },
			"EAST": {"action": "[//]", "type": "text", "text": "x // y", },
			"WEST": {"action": "[%]", "type": "text", "text": "x % y", },
			"showAllSlices": False,
		},
		(2, 2): {
			"CENTER": {"action": "3", "type": "text", "text": "3", },
			"NORTH": {"action": "c", "type": "text", "text": "C", },
			"showAllSlices": False,
		},
	},
}
_ICON_PATH = [os.path.join(os.path.dirname(__file__), "images")]
PLUGIN = plugin_utils.PieKeyboardPluginFactory(_NAME, _ICON, _MAP, _ICON_PATH)

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
