# Copyright 2014 Andrzej Cichocki

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

from __future__ import division
from pym2149.timer import Timer, MinBlockRateTimer, SimpleTimer
from pym2149.vis import Roll
from pym2149.iface import Chip, Stream, YMFile, Config
from pym2149.di import types
from pym2149.ym2149 import ClockInfo
from pym2149.bg import MainBackground
from pym2149.nod import Block
from pym2149.minblep import MinBleps
import time

class SyncTimer(SimpleTimer):

    @types(Stream, MinBleps, ClockInfo)
    def __init__(self, stream, minbleps, clockinfo):
        self.naiverate = clockinfo.implclock
        SimpleTimer.__init__(self, self.naiverate)
        self.buffersize = stream.getbuffersize()
        self.naivex = 0
        self.bufferx = 0
        self.minbleps = minbleps

    def blocksforperiod(self, refreshrate):
        wholeperiodblock, = SimpleTimer.blocksforperiod(self, refreshrate)
        naiveN = wholeperiodblock.framecount
        while naiveN:
            naiven = min(naiveN, self.minbleps.getminnaiven(self.naivex, self.buffersize - self.bufferx))
            yield Block(naiven)
            self.bufferx = (self.bufferx + self.minbleps.getoutcount(self.naivex, naiven)) % self.buffersize
            self.naivex = (self.naivex + naiven) % self.naiverate
            naiveN -= naiven

class StreamReady:

    def __init__(self, updaterate):
        self.period = 1 / updaterate
        self.readytime = time.time()

    def await(self):
        sleeptime = self.readytime - time.time()
        if sleeptime > 0:
            time.sleep(sleeptime)
        self.readytime += self.period

class ChipTimer(MinBlockRateTimer):

    @types(ClockInfo)
    def __init__(self, clockinfo):
        MinBlockRateTimer.__init__(self, clockinfo.implclock, 100)

class SimpleChipTimer(SimpleTimer):

    @types(ClockInfo)
    def __init__(self, clockinfo):
        SimpleTimer.__init__(self, clockinfo.implclock)

class Player(MainBackground):

    @types(Config, YMFile, Chip, Roll, Timer, Stream)
    def __init__(self, config, ymfile, chip, roll, timer, stream):
        MainBackground.__init__(self, config)
        self.updaterate = config.updaterate
        self.ym = ymfile.ym
        self.chip = chip
        self.roll = roll
        self.timer = timer
        self.stream = stream

    def __call__(self):
        for frame in self.ym:
            if self.quit:
                break
            frame(self.chip)
            self.roll.update()
            for b in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(b)
        self.stream.flush()
