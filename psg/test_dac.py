#!/usr/bin/env python

import unittest, numpy as np
from dac import Dac
from nod import Node, Block

class Ramps(Node):

  def __init__(self):
    Node.__init__(self, int)

  def callimpl(self, block):
    for i in xrange(block.framecount):
      self.blockbuf.fill(i, i + 1, i)

def expect(*values):
  return [np.float32(v * 2 * Dac.halfpoweramp) for v in values]

class TestDac(unittest.TestCase):

  def test_works(self):
    d = Dac(Ramps(), self, 15, 13, 1)
    self.value = 15
    self.assertEqual(expect(0, 1, 2), d(Block(3)).tolist())
    self.value = 13
    self.assertEqual(expect(0, .5, 1), d(Block(3)).tolist())
    d = Dac(Ramps(), self, 31, 27, 1)
    self.value = 31
    self.assertEqual(expect(0, 1, 2), d(Block(3)).tolist())
    self.value = 23
    self.assertEqual(expect(0, .25, .5), d(Block(3)).tolist())

if __name__ == '__main__':
  unittest.main()
