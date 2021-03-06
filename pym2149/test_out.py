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

from .buf import Buf
from .minblep import MinBleps
from .nod import Block, Node
from .out import floatdtype, WavBuf, WavWriter
from .power import batterypower
from .test_osc import CmpTime
from types import SimpleNamespace
from unittest import TestCase
import numpy as np, os, time

class MinPeriodTone(Node):

    size = 250000 # One second at adjusted rate.

    def __init__(self):
        super().__init__()
        toneamp = .5 * 2 ** 15 # Half of full scale.
        self.buf = np.empty(self.size, dtype = floatdtype)
        self.buf[::2] = toneamp
        self.buf[1::2] = -toneamp

    def callimpl(self):
        return Buf(self.buf[self.cursor:self.cursor + self.block.framecount])

class TestWavWriter(TestCase, CmpTime):

    def minperiodperformance(self, bigblocks, strictlimitornone):
        clock = 250000
        blocksize = clock // (1000, 10)[bigblocks]
        tone = MinPeriodTone()
        outrate = 44100
        w = WavBuf(SimpleNamespace(implclock = clock), tone, MinBleps.create(clock, outrate, None))
        config = SimpleNamespace(outpath = os.devnull)
        platform = SimpleNamespace(outputrate = outrate)
        w = WavWriter(
            config,
            w,
            SimpleNamespace(getoutchans = SimpleNamespace(size = 1)),
            platform)
        w.start()
        tone.cursor = 0
        start = time.time()
        while tone.cursor < tone.size:
            block = Block(blocksize)
            w.call(block)
            tone.cursor += block.framecount
        w.stop()
        strictlimitornone is None or self.cmptime(start, strictlimitornone)

    def test_minperiodperformancesmallblocks(self):
        if batterypower():
            return
        for strictlimitornone in None, 1:
            self.minperiodperformance(False, strictlimitornone)

    def test_minperiodperformancebigblocks(self):
        if batterypower():
            return
        for strictlimitornone in None, .1: # Wow!
            self.minperiodperformance(True, strictlimitornone)
