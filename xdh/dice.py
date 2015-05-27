"""
Module containing the numeric data type for simulating polyhedral dice.
"""

import sys

from xdh import _dice

dice = _dice.DiceConfig()
dice.__doc__ = __doc__
sys.modules[__name__] = dice