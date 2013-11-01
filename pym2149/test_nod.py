#!/usr/bin/env python

import unittest
from nod import AbstractNode, Block

class MyAbstractNode(AbstractNode):

  def __init__(self):
    AbstractNode.__init__(self)
    self.x = 0

  def callimpl(self):
    x = self.block.framecount + self.x
    self.x += 1
    return x

class TestAbstractNode(unittest.TestCase):

  def test_works(self):
    n = MyAbstractNode()
    b1 = Block(10)
    b2 = Block(20)
    for _ in xrange(2):
      self.assertEqual(10, n.call(b1))
    for _ in xrange(2):
      self.assertEqual(21, n.call(b2))
    for _ in xrange(2):
      self.assertEqual(12, n.call(b1))

if __name__ == '__main__':
  unittest.main()
