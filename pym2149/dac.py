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
        levelmode = self.levelmodereg.value
        timereffect = self.timereffectreg.value
        if timereffect is not None:
            timereffect(levelmode, self.env, self.signal, self.rtone, self.blockbuf, self.chain)
        elif levelmode:
            self.blockbuf.copybuf(self.chain(self.signal))
            self.blockbuf.mulbuf(self.chain(self.env))
        else:
            self.blockbuf.copybuf(self.chain(self.signal))
            self.blockbuf.mul(level4to5(self.fixedreg.value))

class TimerEffect:

    def __init__(self, fixedreg):
        self.fixedreg = fixedreg

class PWMEffect(TimerEffect):

    def getshape(self):
        return toneshape

    def __call__(self, levelmode, envnode, signalnode, rtonenode, blockbuf, chain):
        if levelmode:
            # TODO: Test this branch, or override levelmode starting with first interrupt.
            blockbuf.copybuf(chain(envnode)) # Values in [0, 31].
            blockbuf.add(1) # Shift env values to [1, 32].
            blockbuf.mulbuf(chain(signalnode)) # Introduce 0.
            blockbuf.mulbuf(chain(rtonenode)) # Introduce more 0.
            blockbuf.mapbuf(blockbuf, Level.lookup) # Map 0 to 5-bit pwmzero and sub 1 from rest.
        else:
            blockbuf.copybuf(chain(signalnode))
            blockbuf.mulbuf(chain(rtonenode))
            # Map 0 to pwmzero and 1 to fixed level:
            blockbuf.mul(level4to5(self.fixedreg.value) - Level.pwmzero5bit)
            blockbuf.add(Level.pwmzero5bit)

class SinusEffect(TimerEffect):

    def getshape(self):
        return leveltosinusshape[self.fixedreg.value]

    def __call__(self, levelmode, envnode, signalnode, rtonenode, blockbuf, chain):
        blockbuf.copybuf(chain(rtonenode))
        blockbuf.mul(2)
        blockbuf.add(1)

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
