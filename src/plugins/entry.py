from __future__ import division

import os

import sys
sys.path.append("../")
import plugin_utils


_NAME = "Entry"
_ICON = "newline.png"
_MAP = {
	"name": _NAME,
	"keys": {
		(0, 0): {
			"CENTER": {"action": "[push]", "type": "image", "path": "newline.png", },
			"NORTH": {"action": "[unpush]", "type": "text", "text": "Undo", },
			"NORTH_WEST": {"action": "[clear]", "type": "image", "path": "clear.png", },
			"WEST": {"action": "[backspace]", "type": "image", "path": "backspace.png", },
			"showAllSlices": False,
		},
	},
}
_ICON_PATH = [os.path.join(os.path.dirname(__file__), "images")]
PLUGIN = plugin_utils.PieKeyboardPluginFactory(_NAME, _ICON, _MAP, _ICON_PATH)
