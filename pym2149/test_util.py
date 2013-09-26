#!/usr/bin/env python

import unittest
from util import Session

class TestSession(unittest.TestCase):

  def test_carry(self):
    clock = 2000000
    s = Session(clock, None)
    def nextframecount(rate):
      blocks = list(s.blocks(rate))
      self.assertEqual(1, len(blocks))
      return blocks[0].framecount
    self.assertEqual(33333, nextframecount(60))
    self.assertEqual(20, s.carryticks)
    self.assertEqual(33334, nextframecount(60))
    self.assertEqual(-20, s.carryticks)
    self.assertEqual(33333, nextframecount(60))
    self.assertEqual(0, s.carryticks)
    self.assertEqual(clock * 10, nextframecount(.1))
    self.assertEqual(0, s.carryticks)

  def test_maxblocksize(self):
    s = Session(1000, 2)
    self.assertEqual([333], [b.framecount for b in s.blocks(3)])
    self.assertEqual(1, s.carryticks)
    self.assertEqual([334], [b.framecount for b in s.blocks(3)])
    self.assertEqual(-1, s.carryticks)
    self.assertEqual([333], [b.framecount for b in s.blocks(3)])
    self.assertEqual(0, s.carryticks)
    self.assertEqual([500], [b.framecount for b in s.blocks(2)])
    self.assertEqual(0, s.carryticks)
    self.assertEqual([500, 500], [b.framecount for b in s.blocks(1)])
    self.assertEqual(0, s.carryticks)
    # Don't bother returning a block of size zero:
    self.assertEqual([], [b.framecount for b in s.blocks(2001)])
    self.assertEqual(1000, s.carryticks)

  def test_inexactblockrate(self):
    s = Session(1000, 3)
    # Every block satisfies the given condition:
    self.assertEqual([333, 333, 333, 1], [b.framecount for b in s.blocks(1)])
    self.assertEqual(0, s.carryticks)

if __name__ == '__main__':
  unittest.main()
