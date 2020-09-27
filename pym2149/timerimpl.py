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

from .clock import ClockInfo
from .iface import Platform
from .minblep import MinBleps
from .nod import Block
from .timer import MinBlockRateTimer, SimpleTimer
from diapyr import types

class SyncTimer(SimpleTimer):
    'Fill platform buffer most efficiently.'

    @types(Platform, MinBleps, ClockInfo)
    def __init__(self, platform, minbleps, clockinfo):
        self.naiverate = clockinfo.implclock
        super().__init__(self.naiverate)
        self.buffersize = platform.buffersize
        self.naivex = 0
        self.bufferx = 0
        self.minbleps = minbleps

    def blocksforperiod(self, refreshrate):
        wholeperiodblock, = super().blocksforperiod(refreshrate)
        naiveN = wholeperiodblock.framecount
        while naiveN:
            naiven = min(naiveN, self.minbleps.getminnaiven(self.naivex, self.buffersize - self.bufferx))
            yield Block(naiven)
            self.bufferx = (self.bufferx + self.minbleps.getoutcount(self.naivex, naiven)) % self.buffersize
            self.naivex = (self.naivex + naiven) % self.naiverate
            naiveN -= naiven

class ChipTimer(MinBlockRateTimer):

    @types(ClockInfo)
    def __init__(self, clockinfo):
        super().__init__(clockinfo.implclock, 100)

class SimpleChipTimer(SimpleTimer):
    'One block per update.'

    @types(ClockInfo)
    def __init__(self, clockinfo):
        super().__init__(clockinfo.implclock)
