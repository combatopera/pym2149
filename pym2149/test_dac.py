#!/usr/bin/env python

import unittest
from dac import Dac
from nod import Node, Block

class Ramps(Node):

  def __init__(self):
    Node.__init__(self, int)

  def callimpl(self, masked):
    for i in xrange(self.block.framecount):
      self.blockbuf.fillpart(i, i + 1, i)

class TestDac(unittest.TestCase):

  def test_works(self):
    d = Dac(Ramps(), 1)
    self.assertEqual([d.leveltoamp[v] for v in xrange(32)], d.call(Block(32)).tolist())

if __name__ == '__main__':
  unittest.main()
