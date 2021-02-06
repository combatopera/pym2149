# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

from .const import u4
from mynblep.shapes import floatdtype
import math, numpy as np

signaldtype = np.uint8 # Slightly faster than plain old int.
floatdtype = floatdtype
log2 = math.log(2)

def level5toamp(level):
    return 2 ** ((level - 31) / 4)

def amptolevel5(amp):
    return 31 + 4 * math.log(amp) / log2

def amptolevel4(amp):
    return 15 + 2 * math.log(amp) / log2

def level4to5(level4):
    return level4 * 2 + 1 # Observe 4-bit 0 is 5-bit 1.

class Shape:

    pyrbotype = dict(buf = [signaldtype], size = u4, introlen = u4)

    @classmethod
    def level4to5(cls, data4):
        return cls(map(level4to5, data4))

    def __init__(self, g, introlen = 0):
        self.buf = np.fromiter(g, signaldtype)
        self.size = self.buf.size
        self.introlen = introlen

rawtoneshape = 1, 0
toneshape = Shape(rawtoneshape)

def _meansin(x1, x2):
    return (-math.cos(x2) - -math.cos(x1)) / (x2 - x1)

def _sinsliceamp(i, n, skew):
    return (_meansin(*(2 * math.pi * (i + off + skew) / n for off in [-.5, .5])) + 1) / 2

def _sinuslevel4(steps, maxlevel4, skew):
    maxamp = level5toamp(level4to5(maxlevel4))
    for step in range(steps):
        amp = maxamp * _sinsliceamp(step, steps, skew)
        # For each step, the level that's closest to its ideal mean amp:
        yield max(0, int(round(amptolevel4(amp))))

level4tosinus5shape = tuple(Shape.level4to5(_sinuslevel4(8, level4, 0)) for level4 in range(16))
level4totone5shape = tuple(Shape.level4to5(level4 * x for x in rawtoneshape) for level4 in range(16))
