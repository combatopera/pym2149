#!/usr/bin/env python

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

import unittest, numpy as np, time
from nod import Node, Block
from buf import Buf
from out import WavWriter

class MinPeriodTone(Node):

  size = 250000 # One second at adjusted rate.

  def __init__(self):
    Node.__init__(self)
    toneamp = .5 * 2 ** 15 # Half of full scale.
    self.buf = np.empty(self.size)
    self.buf[::2] = toneamp
    self.buf[1::2] = -toneamp

  def callimpl(self):
    return Buf(self.buf[self.cursor:self.cursor + self.block.framecount])

def minperiodperformance(bigblocks):
    clock = 250000
    blocksize = clock // (1000, 10)[bigblocks]
    tone = MinPeriodTone()
    w = WavWriter(clock, tone, '/dev/null')
    tone.cursor = 0
    start = time.time()
    while tone.cursor < tone.size:
      block = Block(blocksize)
      w.call(block)
      tone.cursor += block.framecount
    w.close()
    return time.time() - start

class TestWavWriter(unittest.TestCase):

  def test_minperiodperformancesmallblocks(self):
    self.assertTrue(minperiodperformance(False) < 1)

  def test_minperiodperformancebigblocks(self):
    self.assertTrue(minperiodperformance(True) < 3) # FIXME: Get this under a second.

if __name__ == '__main__':
  unittest.main()
