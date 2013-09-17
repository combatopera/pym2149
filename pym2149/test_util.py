#!/usr/bin/env python

import unittest
from util import Session

class TestSession(unittest.TestCase):

  def test_carry(self):
    s = Session(2000000)
    def nextframecount(rate):
      return s.block(rate).framecount
    self.assertEqual(33333, nextframecount(60))
    self.assertEqual(20, s.carryticks)
    self.assertEqual(33334, nextframecount(60))
    self.assertEqual(-20, s.carryticks)
    self.assertEqual(33333, nextframecount(60))
    self.assertEqual(0, s.carryticks)
    self.assertEqual(20000000, nextframecount(.1))
    self.assertEqual(0, s.carryticks)

if __name__ == '__main__':
  unittest.main()
