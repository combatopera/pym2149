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
from .shapes import level4to5, level5toamp, leveltosinusshape, signaldtype, toneshape
from diapyr.util import singleton
import numpy as np

class Level(BufNode):

    pwmzero4bit = 0 # TODO: Currently consistent with ST-Sound, but make it a register.
    pwmzero5bit = level4to5(pwmzero4bit)
    lookup = np.fromiter([pwmzero5bit] + list(range(32)), signaldtype)

    def __init__(self, levelmodereg, fixedreg, env, signal, rtone, timereffectreg):
        super().__init__(BufType.signal) # Must be suitable for use as index downstream.
        self.levelmodereg = levelmodereg
        self.fixedreg = fixedreg
        self.env = env
        self.signal = signal
        self.rtone = rtone
        self.timereffectreg = timereffectreg

    def callimpl(self):
        timereffect = self.timereffectreg.value
        if timereffect is not None:
            timereffect(self)
        elif self.levelmodereg.value:
            self.blockbuf.copybuf(self.chain(self.signal))
            self.blockbuf.mulbuf(self.chain(self.env))
        else:
            self.blockbuf.copybuf(self.chain(self.signal))
            self.blockbuf.mul(level4to5(self.fixedreg.value))

@singleton
class PWMEffect:

    def getshape(self, fixedreg):
        return toneshape

    def __call__(self, node):
        if node.levelmodereg.value:
            # TODO: Test this branch, or override levelmode starting with first interrupt.
            node.blockbuf.copybuf(node.chain(node.env)) # Values in [0, 31].
            node.blockbuf.add(1) # Shift env values to [1, 32].
            node.blockbuf.mulbuf(node.chain(node.signal)) # Introduce 0.
            node.blockbuf.mulbuf(node.chain(node.rtone)) # Introduce more 0.
            node.blockbuf.mapbuf(node.blockbuf, node.lookup) # Map 0 to 5-bit pwmzero and sub 1 from rest.
        else:
            node.blockbuf.copybuf(node.chain(node.signal))
            node.blockbuf.mulbuf(node.chain(node.rtone))
            # Map 0 to pwmzero and 1 to fixed level:
            node.blockbuf.mul(level4to5(node.fixedreg.value) - node.pwmzero5bit)
            node.blockbuf.add(node.pwmzero5bit)

@singleton
class SinusEffect:

    def getshape(self, fixedreg):
        return leveltosinusshape[fixedreg.value]

    def __call__(self, node):
        node.blockbuf.copybuf(node.chain(node.rtone))
        node.blockbuf.mul(2)
        node.blockbuf.add(1)

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
