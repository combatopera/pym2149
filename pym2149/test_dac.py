#!/usr/bin/env python

import unittest, numpy as np
from dac import Dac
from nod import Node, Block

class Ramps(Node):

  def __init__(self):
    Node.__init__(self, int)

  def callimpl(self):
    for i in xrange(self.block.framecount):
      self.blockbuf.fill(i, i + 1, i)

class TestDac(unittest.TestCase):

  def test_works(self):
    d = Dac(Ramps(), 1)
    self.assertEqual([d.leveltoamp[v] for v in xrange(32)], d(Block(32)).tolist())

if __name__ == '__main__':
  unittest.main()
