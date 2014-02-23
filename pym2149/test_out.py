#!/usr/bin/env python

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
