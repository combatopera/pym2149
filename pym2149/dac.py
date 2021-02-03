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

from .buf import BufType
from .nod import BufNode
from .shapes import level4to5, level5toamp, level4tosinus5shape, level4totone5shape
from diapyr.util import singleton
import numpy as np

class Level(BufNode):

    def __init__(self, levelmodereg, fixedreg, env, signal, rtone, timereffectreg):
        super().__init__(BufType.signal) # Must be suitable for use as index downstream.
        self.levelmodereg = levelmodereg
        self.fixedreg = fixedreg
        self.env = env
        self.signal = signal
        self.rtone = rtone
        self.timereffectreg = timereffectreg

    def callimpl(self):
        self.timereffectreg.value(self)

@singleton
class NullEffect:
    'The timer does not interfere.'

    def __call__(self, node):
        node.blockbuf.copybuf(node.chain(node.signal))
        if node.levelmodereg.value:
            node.blockbuf.mulbuf(node.chain(node.env))
        else:
            node.blockbuf.mul(level4to5(node.fixedreg.value))

class FixedLevelEffect:

    def __call__(self, node):
        node.blockbuf.copybuf(node.chain(node.signal))
        # XXX: Support clearing levelmode via interrupt?
        node.blockbuf.mulbuf(node.chain(node.env if node.levelmodereg.value else node.rtone))

@singleton
class PWMEffect(FixedLevelEffect):

    def getshape(self, fixedreg):
        return level4totone5shape[fixedreg.value]

@singleton
class SinusEffect(FixedLevelEffect):

    def getshape(self, fixedreg):
        return level4tosinus5shape[fixedreg.value]

class Dac(BufNode):

    def __init__(self, level, log2maxpeaktopeak, ampshare):
        buftype = BufType.float
        super().__init__(buftype)
        # We take off .5 so that the peak amplitude is about -3 dB:
        maxpeaktopeak = (2 ** (log2maxpeaktopeak - .5)) / ampshare
        # Lookup of ideal amplitudes:
        self.leveltopeaktopeak = np.fromiter((level5toamp(v) * maxpeaktopeak for v in range(32)), buftype.dtype)
        self.level = level

    def callimpl(self):
        self.blockbuf.mapbuf(self.chain(self.level), self.leveltopeaktopeak)
