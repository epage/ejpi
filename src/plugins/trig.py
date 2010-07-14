from __future__ import division

import os
import math
import cmath

import operation

import sys
sys.path.append("../")
import plugin_utils


_NAME = "Trigonometry"
_ICON = "trig.png"
_MAP = {
	"name": _NAME,
	"keys": {
		(0, 0): {
			"CENTER": {"action": "[sinh]", "type": "text", "text": "sinh", },
			"SOUTH": {"action": "[asinh]", "type": "text", "text": "asinh", },
			"showAllSlices": False,
		},
		(0, 1): {
			"CENTER": {"action": "[cosh]", "type": "text", "text": "cosh", },
			"SOUTH": {"action": "[acosh]", "type": "text", "text": "acosh", },
			"showAllSlices": False,
		},
		(0, 2): {
			"CENTER": {"action": "[tanh]", "type": "text", "text": "tanh", },
			"SOUTH": {"action": "[atanh]", "type": "text", "text": "atanh", },
			"showAllSlices": False,
		},
		(1, 0): {
			"CENTER": {"action": "[exp]", "type": "text", "text": "exp", },
			"NORTH": {"action": "[log]", "type": "text", "text": "log", },
			"showAllSlices": True,
		},
		(1, 1): {
			"CENTER": {"action": "pi", "type": "text", "text": "pi", },
			"NORTH": {"action": "e", "type": "text", "text": "e", },
			"showAllSlices": True,
		},
		(1, 2): {
			"CENTER": {"action": "[rad]", "type": "text", "text": "rad", },
			"NORTH": {"action": "[deg]", "type": "text", "text": "deg", },
			"showAllSlices": True,
		},
		(2, 0): {
			"CENTER": {"action": "[sin]", "type": "text", "text": "sin", },
			"NORTH": {"action": "[asin]", "type": "text", "text": "asin", },
			"showAllSlices": False,
		},
		(2, 1): {
			"CENTER": {"action": "[cos]", "type": "text", "text": "cos", },
			"NORTH": {"action": "[acos]", "type": "text", "text": "acos", },
			"showAllSlices": False,
		},
		(2, 2): {
			"CENTER": {"action": "[tan]", "type": "text", "text": "tan", },
			"NORTH": {"action": "[atan]", "type": "text", "text": "atan", },
			"showAllSlices": False,
		},
	},
}
_ICON_PATH = [os.path.join(os.path.dirname(__file__), "images")]
PLUGIN = plugin_utils.PieKeyboardPluginFactory(_NAME, _ICON, _MAP, _ICON_PATH)

pi = operation.Constant("pi", operation.Value(math.pi, operation.render_float_eng))
e = operation.Constant("e", operation.Value(math.e, operation.render_float_eng))

def float_or_complex(float_func, complex_func):

	def switching_func(self, *args, **kwd):
		if any(
			isinstance(arg, complex)
			for arg in args
		):
			return complex_func(*args, **kwd)
		else:
			return float_func(*args, **kwd)

	switching_func.__name__ = complex_func.__name__
	switching_func.__doc__ = complex_func.__doc__
	return switching_func

exp = operation.generate_function(float_or_complex(math.exp, cmath.exp), "exp", operation.Function.REP_FUNCTION, 1)
log = operation.generate_function(float_or_complex(math.log, cmath.log), "log", operation.Function.REP_FUNCTION, 1)

PLUGIN.register_operation("exp", exp)
PLUGIN.register_operation("log", log)

cos = operation.generate_function(float_or_complex(math.cos, cmath.cos), "cos", operation.Function.REP_FUNCTION, 1)
acos = operation.generate_function(float_or_complex(math.acos, cmath.acos), "acos", operation.Function.REP_FUNCTION, 1)
sin = operation.generate_function(float_or_complex(math.sin, cmath.sin), "sin", operation.Function.REP_FUNCTION, 1)
asin = operation.generate_function(float_or_complex(math.asin, cmath.asin), "asin", operation.Function.REP_FUNCTION, 1)
tan = operation.generate_function(float_or_complex(math.tan, cmath.tan), "tan", operation.Function.REP_FUNCTION, 1)
atan = operation.generate_function(float_or_complex(math.atan, cmath.atan), "atan", operation.Function.REP_FUNCTION, 1)

PLUGIN.register_operation("cos", cos)
PLUGIN.register_operation("acos", acos)
PLUGIN.register_operation("sin", sin)
PLUGIN.register_operation("asin", asin)
PLUGIN.register_operation("tan", tan)
PLUGIN.register_operation("atan", atan)

cosh = operation.generate_function(float_or_complex(math.cosh, cmath.cosh), "cosh", operation.Function.REP_FUNCTION, 1)
acosh = operation.generate_function(cmath.acosh, "acosh", operation.Function.REP_FUNCTION, 1)
sinh = operation.generate_function(float_or_complex(math.sinh, cmath.sinh), "sinh", operation.Function.REP_FUNCTION, 1)
asinh = operation.generate_function(cmath.asinh, "asinh", operation.Function.REP_FUNCTION, 1)
tanh = operation.generate_function(float_or_complex(math.tanh, cmath.tanh), "tanh", operation.Function.REP_FUNCTION, 1)
atanh = operation.generate_function(cmath.atanh, "atanh", operation.Function.REP_FUNCTION, 1)

PLUGIN.register_operation("cosh", cosh)
PLUGIN.register_operation("acosh", acosh)
PLUGIN.register_operation("sinh", sinh)
PLUGIN.register_operation("asinh", asinh)
PLUGIN.register_operation("tanh", tanh)
PLUGIN.register_operation("atanh", atanh)

deg = operation.generate_function(math.degrees, "deg", operation.Function.REP_FUNCTION, 1)
rad = operation.generate_function(math.radians, "rad", operation.Function.REP_FUNCTION, 1)

PLUGIN.register_operation("deg", deg)
PLUGIN.register_operation("rad", rad)

# In 2.6
#phase = operation.generate_function(cmath.phase, "phase", operation.Function.REP_FUNCTION, 1)
#polar = operation.generate_function(cmath.polar, "polar", operation.Function.REP_FUNCTION, 1)
#rect = operation.generate_function(cmath.rect, "rect", operation.Function.REP_FUNCTION, 1)

