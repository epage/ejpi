"""
Keyboard Origin:

qwe rtyu iop
as dfghj kl
zxc vb nm

e t i
a h l
c b n
"""

from __future__ import division

import os

from ejpi import plugin_utils


_NAME = "Alphabet"
_ICON = "alphabet.png"
_MAP = {
	"name": _NAME,
	"keys": {
		(0, 0): {
			"CENTER": {"action": "e", "type": "text", "text": "E", },
			"SOUTH": {"action": "q", "type": "text", "text": "Q", },
			"EAST": {"action": "w", "type": "text", "text": "W", },
			"showAllSlices": True,
		},
		(0, 1): {
			"CENTER": {"action": "t", "type": "text", "text": "T", },
			"WEST": {"action": "r", "type": "text", "text": "R", },
			"EAST": {"action": "y", "type": "text", "text": "Y", },
			"SOUTH": {"action": "u", "type": "text", "text": "U", },
			"showAllSlices": True,
		},
		(0, 2): {
			"CENTER": {"action": "i", "type": "text", "text": "I", },
			"WEST": {"action": "o", "type": "text", "text": "O", },
			"SOUTH": {"action": "p", "type": "text", "text": "P", },
			"showAllSlices": True,
		},
		(1, 0): {
			"CENTER": {"action": "a", "type": "text", "text": "A", },
			"EAST": {"action": "s", "type": "text", "text": "S", },
			"showAllSlices": True,
		},
		(1, 1): {
			"CENTER": {"action": "h", "type": "text", "text": "H", },
			"WEST": {"action": "d", "type": "text", "text": "D", },
			"NORTH": {"action": "f", "type": "text", "text": "F", },
			"EAST": {"action": "g", "type": "text", "text": "G", },
			"SOUTH": {"action": "j", "type": "text", "text": "J", },
			"showAllSlices": True,
		},
		(1, 2): {
			"CENTER": {"action": "l", "type": "text", "text": "L", },
			"WEST": {"action": "k", "type": "text", "text": "K", },
			"showAllSlices": True,
		},
		(2, 0): {
			"CENTER": {"action": "c", "type": "text", "text": "C", },
			"NORTH": {"action": "z", "type": "text", "text": "Z", },
			"EAST": {"action": "x", "type": "text", "text": "X", },
			"showAllSlices": True,
		},
		(2, 1): {
			"CENTER": {"action": "b", "type": "text", "text": "B", },
			"NORTH": {"action": "v", "type": "text", "text": "V", },
			"showAllSlices": True,
		},
		(2, 2): {
			"CENTER": {"action": "n", "type": "text", "text": "N", },
			"NORTH_WEST": {"action": "m", "type": "text", "text": "M", },
			"showAllSlices": True,
		},
	},
}
_ICON_PATH = [os.path.join(os.path.dirname(__file__), "images")]
PLUGIN = plugin_utils.PieKeyboardPluginFactory(_NAME, _ICON, _MAP, _ICON_PATH)
