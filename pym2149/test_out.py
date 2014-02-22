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

def minperiodperformance():
    clock = 250000
    tone = MinPeriodTone()
    w = WavWriter(clock, tone, '/dev/null')
    tone.cursor = 0
    start = time.time()
    while tone.cursor < tone.size:
      # Big blocks as we're measuring per-block performance:
      block = Block(clock // 10)
      w.call(block)
      tone.cursor += block.framecount
    w.close()
    return time.time() - start

class TestWavWriter(unittest.TestCase):

  def test_minperiodperformance(self):
    self.assertTrue(minperiodperformance() < 5) # FIXME: Get this under a second.

if __name__ == '__main__':
  unittest.main()
