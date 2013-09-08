#!/usr/bin/env python

import unittest, numpy as np
from mix import Mixer
from buf import MasterBuf
from dac import Dac
from nod import Node, Block

class Counter(Node):

  def __init__(self, x = 0):
    Node.__init__(self, int)
    self.x = x

  def callimpl(self, block):
    for frameindex in xrange(block.framecount):
      self.blockbuf.fill(frameindex, frameindex + 1, self.x)
      self.x += 1

def expect(*values):
  return [np.float32(v - Dac.halfpoweramp) for v in values]

class TestMixer(unittest.TestCase):

  def test_works(self):
    m = Mixer(Counter(10), Counter())
    self.assertEqual(expect(10, 12, 14, 16, 18), m(Block(0, 5)).tolist())
    # Check the buffer is actually cleared first:
    self.assertEqual(expect(20, 22, 24, 26, 28), m(Block(1, 5)).tolist())

if __name__ == '__main__':
  unittest.main()
