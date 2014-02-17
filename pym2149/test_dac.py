#!/usr/bin/env python

import unittest
from dac import Dac
from nod import BufNode, Block

class Ramps(BufNode):

  def __init__(self):
    BufNode.__init__(self, int)

  def callimpl(self):
    for i in xrange(self.block.framecount):
      self.blockbuf.fillpart(i, i + 1, i)

class TestDac(unittest.TestCase):

  def test_works(self):
    d = Dac(Ramps(), 1)
    self.assertEqual([d.leveltopeaktopeak[v] for v in xrange(32)], d.call(Block(32)).tolist())

if __name__ == '__main__':
  unittest.main()
