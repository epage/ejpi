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
import operator

import operation

import sys
sys.path.append("../")
import plugin_utils


_MAP_FILE_PATH = os.path.join(os.path.dirname(__file__), "alphabet.map")
PLUGIN = plugin_utils.PieKeyboardPluginFactory("Alphabet", _MAP_FILE_PATH)
