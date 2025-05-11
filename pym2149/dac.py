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
from foyndation import singleton
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
        self.timereffectreg.value.putlevel5(self)

@singleton
class NullEffect:
    'All registers are non-virtual and write directly to chip, the timer does not interfere.'

    def putlevel5(self, node):
        node.blockbuf.copybuf(node.chain(node.signal))
        if node.levelmodereg.value:
            node.blockbuf.mulbuf(node.chain(node.env))
        else:
            # According to block diagram, the level is already 5-bit when combining with binary signal:
            node.blockbuf.mul(level4to5(node.fixedreg.value))

class FixedLevelEffect:
    'Registers levelmodereg and fixedreg are virtual, of which levelmodereg is ignored.'

    def __init__(self):
        self.wavelength, = {shape.wavelength() for shape in self.level4toshape}

    def getshape(self, fixedreg):
        return self.level4toshape[fixedreg.value]

    def putlevel5(self, node):
        node.blockbuf.copybuf(node.chain(node.signal))
        node.blockbuf.mulbuf(node.chain(node.rtone))

@singleton
class PWMEffect(FixedLevelEffect):
    'Interrupt setup/routine alternates fixed level between fixedreg and zero.'

    level4toshape = level4totone5shape

@singleton
class SinusEffect(FixedLevelEffect):
    'Interrupt setup/routine sets fixed level to sample value as scaled by fixedreg.'

    level4toshape = level4tosinus5shape

class DigiDrumEffect:
    'Like SinusEffect but in addition toneflagreg and noiseflagreg are virtual and we ignore them.'

    def __init__(self, sample5shape):
        self.sample5shape = sample5shape

    def getshape(self, fixedreg):
        return self.sample5shape

    def putlevel5(self, node):
        node.blockbuf.copybuf(node.chain(node.rtone))

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
