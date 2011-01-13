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
			"CENTER": {"action": "[//]", "type": "text", "text": "x // y", },
			"SOUTH": {"action": "1", "type": "text", "text": "1", },
			"SOUTH_EAST": {"action": "2", "type": "text", "text": "2", },
			"EAST": {"action": "3", "type": "text", "text": "3", },
			"showAllSlices": False,
		},
		(0, 1): {
			"CENTER": {"action": "[dec]", "type": "text", "text": "-> dec", },
			"SOUTH_WEST": {"action": "4", "type": "text", "text": "4", },
			"SOUTH": {"action": "5", "type": "text", "text": "5", },
			"SOUTH_EAST": {"action": "6", "type": "text", "text": "6", },
			"showAllSlices": True,
		},
		(0, 2): {
			"CENTER": {"action": "[%]", "type": "text", "text": "x % y", },
			"WEST": {"action": "7", "type": "text", "text": "7", },
			"SOUTH_WEST": {"action": "8", "type": "text", "text": "8", },
			"SOUTH": {"action": "9", "type": "text", "text": "9", },
			"showAllSlices": False,
		},
		(1, 0): {
			"CENTER": {"action": "0o", "type": "text", "text": "0o", },
			"SOUTH": {"action": "[oct]", "type": "text", "text": "-> oct", },
			"showAllSlices": True,
		},
		(1, 1): {
			"CENTER": {"action": "0x", "type": "text", "text": "0x", },
			"SOUTH": {"action": "[hex]", "type": "text", "text": "-> hex", },
			"NORTH_WEST": {"action": "a", "type": "text", "text": "A", },
			"WEST": {"action": "b", "type": "text", "text": "B", },
			"SOUTH_WEST": {"action": "c", "type": "text", "text": "C", },
			"NORTH_EAST": {"action": "d", "type": "text", "text": "D", },
			"EAST": {"action": "e", "type": "text", "text": "E", },
			"SOUTH_EAST": {"action": "f", "type": "text", "text": "F", },
			"showAllSlices": True,
		},
		(1, 2): {
			"CENTER": {"action": "0b", "type": "text", "text": "0b", },
			"NORTH": {"action": "1", "type": "text", "text": "1", },
			"SOUTH": {"action": "0", "type": "text", "text": "0", },
			"showAllSlices": True,
		},
		(2, 0): {
			"CENTER": {"action": "[&]", "type": "text", "text": "and", },
			"showAllSlices": True,
		},
		(2, 1): {
			"CENTER": {"action": "[|]", "type": "text", "text": "or", },
			"NORTH": {"action": "[~]", "type": "text", "text": "not", },
			"showAllSlices": True,
		},
		(2, 2): {
			"CENTER": {"action": "[^]", "type": "text", "text": "xor", },
			"showAllSlices": True,
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
